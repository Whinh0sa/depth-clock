import os
import urllib.request
import numpy as np
from PIL import Image

MODEL_URL = "https://github.com/intel-isl/MiDaS/releases/download/v2_1/model-small.onnx"
APP_DIR = os.path.join(os.path.expanduser("~"), ".depthclock")
MODEL_PATH = os.path.join(APP_DIR, "model-small.onnx")

def ensure_app_dir():
    if not os.path.exists(APP_DIR):
        os.makedirs(APP_DIR)

def download_model(progress_callback=None):
    ensure_app_dir()
    if os.path.exists(MODEL_PATH):
        if os.path.getsize(MODEL_PATH) > 10 * 1024 * 1024: # Must be larger than 10MB
            return True
            
    print("Downloading MiDaS ONNX model...")
    try:
        def report(block_num, block_size, total_size):
            read_so_far = block_num * block_size
            if total_size > 0:
                percent = min(100, int(read_so_far * 100 / total_size))
                if progress_callback:
                    progress_callback(percent)
                else:
                    print(f"Download progress: {percent}%", end="\r")
            
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH, reporthook=report)
        print("\nDownload complete.")
        return True
    except Exception as e:
        print(f"\nError downloading model: {e}")
        if os.path.exists(MODEL_PATH):
            try:
                os.remove(MODEL_PATH)
            except:
                pass
        return False

class DepthEngine:
    def __init__(self):
        ensure_app_dir()
        if not os.path.exists(MODEL_PATH):
            success = download_model()
            if not success:
                raise RuntimeError("Failed to obtain the depth model.")
        
        # Load ONNX Runtime session
        import onnxruntime as ort
        self.session = ort.InferenceSession(MODEL_PATH, providers=['CPUExecutionProvider'])
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    def compute_depth(self, img_path):
        """
        Computes the depth map for a given image path using PIL and NumPy.
        Returns a 2D numpy array normalized to 0-255 (uint8).
        """
        # Load image with PIL
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
        
        # Convert depth array back to PIL Image to resize it back to original resolution
        # First normalize 256x256 depth map to [0, 255]
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

if __name__ == "__main__":
    print("Testing depth engine...")
    if download_model():
        engine = DepthEngine()
        print("Depth engine loaded successfully.")
