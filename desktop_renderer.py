import os
import time
import json
import tkinter as tk
from PIL import Image, ImageTk, ImageFilter
import win32gui
import win32con
import win32api
import win32process
import ctypes

# Enable DPI Awareness to fix resolution and positioning issues on scaled displays
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2) # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

APP_DIR = os.path.join(os.path.expanduser("~"), ".depthclock")
CONFIG_PATH = os.path.join(APP_DIR, "config.json")

def resize_to_fill(img, target_w, target_h):
    """
    Resizes and crops an image to fill the target dimensions,
    maintaining the original aspect ratio (mimics Windows' default "Fill" option).
    """
    img_w, img_h = img.size
    img_aspect = img_w / img_h
    target_aspect = target_w / target_h
    
    if img_aspect > target_aspect:
        # Image is wider than target aspect ratio - crop sides
        new_h = target_h
        new_w = int(new_h * img_aspect)
        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        start_x = (new_w - target_w) // 2
        return img_resized.crop((start_x, 0, start_x + target_w, target_h))
    else:
        # Image is taller than target aspect ratio - crop top/bottom
        new_w = target_w
        new_h = int(new_w / img_aspect)
        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        start_y = (new_h - target_h) // 2
        return img_resized.crop((0, start_y, target_w, start_y + target_h))

def get_desktop_worker_w():
    """
    Sends the magic message to Progman to spawn a WorkerW window behind the desktop icons,
    then locates and returns the exact sibling WorkerW HWND handle.
    """
    progman = win32gui.FindWindow("Progman", None)
    # Send message 0x052C to Progman
    win32gui.SendMessageTimeout(progman, 0x052C, 0, 0, win32con.SMTO_NORMAL, 1000)
    
    shell_worker = None
    
    # Enumerate windows to find the WorkerW containing SHELLDLL_DefView
    def enum_windows_callback(hwnd, extra):
        nonlocal shell_worker
        class_name = win32gui.GetClassName(hwnd)
        if class_name == "WorkerW":
            shell_dll = win32gui.FindWindowEx(hwnd, 0, "SHELLDLL_DefView", None)
            if shell_dll:
                shell_worker = hwnd
        return True

    win32gui.EnumWindows(enum_windows_callback, None)
    
    # The wallpaper WorkerW window is the sibling window immediately after shell_worker
    worker_w = None
    if shell_worker:
        worker_w = win32gui.FindWindowEx(0, shell_worker, "WorkerW", None)
        
    # Fallback to Progman if worker_w is not found
    if not worker_w:
        worker_w = progman
        
    return worker_w

class DesktopRenderer:
    def __init__(self, run_in_worker_w=True):
        self.run_in_worker_w = run_in_worker_w
        self.root = tk.Tk()
        self.root.title("Depth Clock Desktop Window")
        
        # Make borderless
        self.root.overrideredirect(True)
        
        # Get primary screen dimensions (DPI aware now)
        self.screen_width = win32api.GetSystemMetrics(0)
        self.screen_height = win32api.GetSystemMetrics(1)
        self.root.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        
        # Create canvas
        self.canvas = tk.Canvas(
            self.root, 
            width=self.screen_width, 
            height=self.screen_height, 
            bd=0, 
            highlightthickness=0, 
            bg="black"
        )
        self.canvas.pack(fill="both", expand=True)
        
        # State variables
        self.bg_photo = None
        self.fg_photo = None
        self.clock_item = None
        self.bg_item = None
        self.fg_item = None
        
        # Set up Win32 window properties
        self.root.update() # Force window creation to get valid HWND
        self.hwnd = self.root.winfo_id()
        
        if self.run_in_worker_w:
            parent_hwnd = get_desktop_worker_w()
            win32gui.SetParent(self.hwnd, parent_hwnd)
            
            # Apply WS_CHILD style and remove WS_POPUP so it behaves correctly as a desktop child
            style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_STYLE)
            style = (style & ~win32con.WS_POPUP) | win32con.WS_CHILD
            win32gui.SetWindowLong(self.hwnd, win32con.GWL_STYLE, style)
            
            # Position it at 0, 0 inside the WorkerW parent
            win32gui.SetWindowPos(
                self.hwnd, 0, 0, 0, self.screen_width, self.screen_height,
                win32con.SWP_NOZORDER | win32con.SWP_SHOWWINDOW
            )
        else:
            # Standard click-through transparent overlay on top
            style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
            style |= win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
            win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, style)
            # Make it top-most
            win32gui.SetWindowPos(
                self.hwnd, 
                win32con.HWND_TOPMOST, 
                0, 0, 
                self.screen_width, 
                self.screen_height, 
                win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW
            )
            
        self.load_config_and_render()
        self.update_clock()
        
    def load_config_and_render(self):
        if not os.path.exists(CONFIG_PATH):
            return
            
        try:
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return
            
        wallpaper_path = config.get("wallpaper_path", "")
        depth_map_path = config.get("depth_map_path", "")
        threshold = config.get("threshold", 128)
        blur_radius = config.get("blur_radius", 2)
        
        # Clock configurations
        self.clock_font = config.get("font_family", "Outfit")
        self.clock_size = config.get("font_size", 90)
        self.clock_color = config.get("color", "#ffffff")
        self.clock_x = int(config.get("pos_x", self.screen_width / 2))
        self.clock_y = int(config.get("pos_y", self.screen_height / 3))
        self.time_format = "%H:%M" if config.get("format_24h", True) else "%I:%M %p"
        
        if not os.path.exists(wallpaper_path):
            return
            
        # Load and resize wallpaper to fill the screen dimensions exactly (keeping aspect ratio)
        wp_raw = Image.open(wallpaper_path).convert("RGBA")
        wp_img = resize_to_fill(wp_raw, self.screen_width, self.screen_height)
        
        self.bg_photo = ImageTk.PhotoImage(wp_img)
        
        # Set background image
        if self.bg_item:
            self.canvas.itemconfig(self.bg_item, image=self.bg_photo)
        else:
            self.bg_item = self.canvas.create_image(0, 0, anchor="nw", image=self.bg_photo)
            
        # Set or create clock
        font_tuple = (self.clock_font, self.clock_size, "bold")
        if self.clock_item:
            self.canvas.coords(self.clock_item, self.clock_x, self.clock_y)
            self.canvas.itemconfig(self.clock_item, font=font_tuple, fill=self.clock_color)
        else:
            self.clock_item = self.canvas.create_text(
                self.clock_x, 
                self.clock_y, 
                text="", 
                font=font_tuple, 
                fill=self.clock_color, 
                anchor="center"
            )
            
        # Create masked foreground layer
        if os.path.exists(depth_map_path):
            depth_raw = Image.open(depth_map_path).convert("L")
            depth_img = resize_to_fill(depth_raw, self.screen_width, self.screen_height)
            
            # Apply threshold to create mask
            mask = depth_img.point(lambda p: 255 if p >= threshold else 0)
            if blur_radius > 0:
                mask = mask.filter(ImageFilter.GaussianBlur(blur_radius))
                
            fg_img = wp_img.copy()
            fg_img.putalpha(mask)
            
            self.fg_photo = ImageTk.PhotoImage(fg_img)
            
            if self.fg_item:
                self.canvas.itemconfig(self.fg_item, image=self.fg_photo)
            else:
                self.fg_item = self.canvas.create_image(0, 0, anchor="nw", image=self.fg_photo)
                
            # Bring foreground to top
            self.canvas.tag_raise(self.fg_item)
            
    def update_clock(self):
        current_time = time.strftime(self.time_format)
        if self.clock_item:
            self.canvas.itemconfig(self.clock_item, text=current_time)
            
        # Re-check config changes periodically (every 2 seconds)
        if hasattr(self, '_last_config_check') and time.time() - self._last_config_check > 2.0:
            self.load_config_and_render()
            self._last_config_check = time.time()
        elif not hasattr(self, '_last_config_check'):
            self._last_config_check = time.time()
            
        # Update every second
        self.root.after(1000, self.update_clock)
        
    def start(self):
        self.root.mainloop()

if __name__ == "__main__":
    renderer = DesktopRenderer()
    renderer.start()
