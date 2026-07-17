import os
import urllib.request
import numpy as np
from PIL import Image

MODEL_URL = "https://github.com/intel-isl/MiDaS/releases/download/v2_1/model-small.onnx"
U2NETP_URL = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx"
U2NET_URL = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx"

APP_DIR = os.path.join(os.path.expanduser("~"), ".depthclock")
MODEL_PATH = os.path.join(APP_DIR, "model-small.onnx")
U2NETP_PATH = os.path.join(APP_DIR, "u2netp.onnx")
U2NET_PATH = os.path.join(APP_DIR, "u2net.onnx")

def ensure_app_dir():
    if not os.path.exists(APP_DIR):
        os.makedirs(APP_DIR)

def download_model_file(url, target_path, name, progress_callback=None):
    ensure_app_dir()
    if os.path.exists(target_path):
        if os.path.getsize(target_path) > 1 * 1024 * 1024: # Must be larger than 1MB
            return True
            
    print(f"Downloading {name} ONNX model...")
    try:
        def report(block_num, block_size, total_size):
            read_so_far = block_num * block_size
            if total_size > 0:
                percent = min(100, int(read_so_far * 100 / total_size))
                if progress_callback:
                    progress_callback(percent)
                else:
                    print(f"Download progress: {percent}%", end="\r")
            
        urllib.request.urlretrieve(url, target_path, reporthook=report)
        print(f"\nDownload complete for {name}.")
        return True
    except Exception as e:
        print(f"\nError downloading {name} model: {e}")
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
            except:
                pass
        return False

def download_model(progress_callback=None):
    return download_model_file(MODEL_URL, MODEL_PATH, "MiDaS Depth", progress_callback)

def download_u2net(model_type="u2netp", progress_callback=None):
    if model_type == "u2net":
        return download_model_file(U2NET_URL, U2NET_PATH, "U-2-Net (176MB)", progress_callback)
    else:
        return download_model_file(U2NETP_URL, U2NETP_PATH, "U-2-Netp (4.7MB)", progress_callback)

class DepthEngine:
    def __init__(self):
        ensure_app_dir()
        
        # Load MiDaS Depth session lazily or on startup
        if not os.path.exists(MODEL_PATH):
            success = download_model()
            if not success:
                raise RuntimeError("Failed to obtain the depth model.")
        
        import onnxruntime as ort
        self.session = ort.InferenceSession(MODEL_PATH, providers=['CPUExecutionProvider'])
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        
        self.u2net_session = None
        self.u2net_loaded_type = None

    def load_u2net(self, model_type="u2netp"):
        """
        Lazily loads the specified U-2-Net model for sharp subject segmentation.
        """
        if self.u2net_session is not None and self.u2net_loaded_type == model_type:
            return
            
        if self.u2net_session is not None:
            self.u2net_session = None
            self.u2net_loaded_type = None
            
        path = U2NET_PATH if model_type == "u2net" else U2NETP_PATH
        if not os.path.exists(path):
            success = download_u2net(model_type)
            if not success:
                raise RuntimeError(f"Failed to obtain the U-2-Net {model_type} subject segmentation model.")
                
        import onnxruntime as ort
        print(f"Loading U-2-Net {model_type} subject segmentation session...")
        self.u2net_session = ort.InferenceSession(path, providers=['CPUExecutionProvider'])
        self.u2net_input_name = self.u2net_session.get_inputs()[0].name
        self.u2net_output_name = self.u2net_session.get_outputs()[0].name
        self.u2net_loaded_type = model_type

    def compute_depth(self, img_path):
        """
        Computes the depth map for a given image path using PIL and NumPy.
        Returns a 2D numpy array normalized to 0-255 (uint8).
        """
        try:
            img = Image.open(img_path).convert("RGB")
        except Exception as e:
            raise ValueError(f"Could not load image {img_path}: {e}")
            
        w, h = img.size
        
        # Preprocessing: resize to 256x256
        img_resized = img.resize((256, 256), Image.Resampling.BILINEAR)
        img_np = np.array(img_resized, dtype=np.float32) / 255.0
        
        # Standard ImageNet normalization
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img_np = (img_np - mean) / std
        
        # HWC to CHW
        img_input = img_np.transpose(2, 0, 1)
        img_input = np.expand_dims(img_input, axis=0) # 1x3x256x256
        
        # Run inference
        outputs = self.session.run([self.output_name], {self.input_name: img_input})
        depth = outputs[0][0] # Shape: 256x256
        
        # Normalize
        depth_min = depth.min()
        depth_max = depth.max()
        if depth_max - depth_min > 0:
            depth_normalized = (depth - depth_min) / (depth_max - depth_min) * 255.0
        else:
            depth_normalized = np.zeros_like(depth)
            
        depth_pil_256 = Image.fromarray(depth_normalized.astype(np.uint8))
        
        # Resize to original resolution
        depth_pil = depth_pil_256.resize((w, h), Image.Resampling.BICUBIC)
        return np.array(depth_pil)

    def compute_subject_mask(self, img_path, model_type="u2netp"):
        """
        Computes the sharp salient object segmentation mask for a given image.
        Returns a 2D numpy array normalized to 0-255 (uint8).
        """
        self.load_u2net(model_type)
        
        try:
            img = Image.open(img_path).convert("RGB")
        except Exception as e:
            raise ValueError(f"Could not load image {img_path}: {e}")
            
        w, h = img.size
        
        # Preprocessing: resize to 320x320
        img_resized = img.resize((320, 320), Image.Resampling.BILINEAR)
        img_np = np.array(img_resized, dtype=np.float32) / 255.0
        
        # Standard ImageNet normalization
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img_np = (img_np - mean) / std
        
        # HWC to CHW
        img_input = img_np.transpose(2, 0, 1)
        img_input = np.expand_dims(img_input, axis=0) # 1x3x320x320
        
        # Run inference
        outputs = self.u2net_session.run([self.u2net_output_name], {self.u2net_input_name: img_input})
        pred = outputs[0][0][0] # Shape: 320x320
        
        # Normalize probability map to [0, 255]
        pred_min = pred.min()
        pred_max = pred.max()
        if pred_max - pred_min > 0:
            pred_normalized = (pred - pred_min) / (pred_max - pred_min) * 255.0
        else:
            pred_normalized = np.zeros_like(pred)
            
        pred_pil_320 = Image.fromarray(pred_normalized.astype(np.uint8))
        
        # Resize back to original resolution
        pred_pil = pred_pil_320.resize((w, h), Image.Resampling.BICUBIC)
        return np.array(pred_pil)

if __name__ == "__main__":
    print("Testing depth and segmentation engine...")
    engine = DepthEngine()
    print("Engine loaded successfully.")
