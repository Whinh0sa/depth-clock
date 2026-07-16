import os
import json
import threading
import time
import random
import urllib.request
import numpy as np
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageFilter
import customtkinter as ctk
import win32api
import win32con
import ctypes
import winreg
import sys
import zipfile

# Enable DPI Awareness to fix resolution and positioning issues on scaled displays
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2) # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from depth_engine import DepthEngine, download_model, APP_DIR, MODEL_PATH

CONFIG_PATH = os.path.join(APP_DIR, "config.json")
RANDOM_WP_PATH = os.path.join(APP_DIR, "random_wallpaper.jpg")

PREMIUM_COLORS = [
    "#FFFFFF", # White
    "#F5F5F7", # Silver/Grey
    "#00F2FE", # Electric Blue
    "#FF5E62", # Coral Pink
    "#FAD961", # Sunrise Gold
    "#B3FF66", # Neon Lime
    "#EC008C", # Magenta
    "#FF9933"  # Vibrant Orange
]

# Curated high-contrast wallpapers optimized for 3D depth clocks
CURATED_WALLPAPERS = {
    "Curated Nature (Unsplash)": [
        "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1472214222541-d510753a8707?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1501854140801-50d01698950b?auto=format&fit=crop&q=80&w=1920"
    ],
    "Curated Space & Stars": [
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1506318137071-a8e063b4bec0?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1538370965046-79c0d6907d47?auto=format&fit=crop&q=80&w=1920"
    ],
    "Curated Cities & Architecture": [
        "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1449034446853-66c86144b0ad?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&q=80&w=1920"
    ]
}

def get_dominant_colors(image_path, num_colors=5):
    try:
        img = Image.open(image_path).convert("RGB")
        img = img.resize((100, 100))
        colors = img.getcolors(10000)
        if not colors:
            return []
            
        colors_sorted = sorted(colors, key=lambda x: x[0], reverse=True)
        
        hex_colors = []
        for count, rgb in colors_sorted:
            if sum(rgb) < 50:
                continue
                
            hex_val = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
            
            is_similar = False
            for existing in hex_colors:
                r2 = int(existing[1:3], 16)
                g2 = int(existing[3:5], 16)
                b2 = int(existing[5:7], 16)
                dist = ((rgb[0] - r2)**2 + (rgb[1] - g2)**2 + (rgb[2] - b2)**2)**0.5
                if dist < 45:
                    is_similar = True
                    break
            if not is_similar:
                hex_colors.append(hex_val)
                if len(hex_colors) >= num_colors:
                    break
        return hex_colors
    except Exception as e:
        print("Error extracting dominant colors:", e)
        return []

def resize_to_fill(img, target_w, target_h):
    img_w, img_h = img.size
    img_aspect = img_w / img_h
    target_aspect = target_w / target_h
    
    if img_aspect > target_aspect:
        new_h = target_h
        new_w = int(new_h * img_aspect)
        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        start_x = (new_w - target_w) // 2
        return img_resized.crop((start_x, 0, start_x + target_w, target_h))
    else:
        new_w = target_w
        new_h = int(new_w / img_aspect)
        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        start_y = (new_h - target_h) // 2
        return img_resized.crop((0, start_y, target_w, start_y + target_h))

# Set theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class DepthClockGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Windows Depth Clock - Settings")
        self.geometry("1120x700")
        self.resizable(False, False)
        
        # Initialize default values
        self.wallpaper_path = ""
        self.depth_map = None
        self.raw_wp_image = None
        self.raw_depth_image = None
        self.engine = None
        self.renderer_process = None
        self.suggested_buttons = []
        
        # Fetch screen size
        self.screen_w = win32api.GetSystemMetrics(0)
        self.screen_h = win32api.GetSystemMetrics(1)
        
        # Calculate preview canvas dimensions to exactly match screen aspect ratio
        screen_aspect = self.screen_w / self.screen_h
        self.preview_canvas_w = 620
        self.preview_canvas_h = int(self.preview_canvas_w / screen_aspect)
        
        self.config_data = {
            "wallpaper_path": "",
            "depth_map_path": "",
            "threshold": 128,
            "blur_radius": 2,
            "transition_width": 10,
            "font_family": "Segoe UI",
            "font_size": 120,
            "color": "#FFFFFF",
            "pos_x_ratio": 0.5,
            "pos_y_ratio": 0.3,
            "format_24h": True,
            "show_date": True,
            "date_format": "%a, %b %d",
            "date_y_offset_ratio": -0.074,
            "sync_lockscreen": False
        }
        
        self.load_saved_config()
        self.create_widgets()
        
        # Start engine loading thread
        threading.Thread(target=self.initialize_depth_engine, daemon=True).start()
        
    def load_saved_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r") as f:
                    saved = json.load(f)
                    self.config_data.update(saved)
                    self.wallpaper_path = self.config_data["wallpaper_path"]
            except Exception as e:
                print("Failed to load config:", e)

    def save_config(self):
        os.makedirs(APP_DIR, exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(self.config_data, f, indent=4)
            
    def initialize_depth_engine(self):
        self.set_status("Checking model status...")
        if not os.path.exists(MODEL_PATH):
            self.set_status("Downloading 3D Depth Model (approx 58MB)...")
            download_model(self.update_download_progress)
            
        self.set_status("Loading 3D Engine...")
        try:
            self.engine = DepthEngine()
            self.set_status("Engine ready.")
            self.enable_controls(True)
            
            if self.wallpaper_path and os.path.exists(self.wallpaper_path):
                self.process_wallpaper(self.wallpaper_path)
        except Exception as e:
            self.set_status(f"Error loading model: {e}")
            
    def update_download_progress(self, percent):
        self.set_status(f"Downloading 3D Depth Model: {percent}%")
        
    def set_status(self, text):
        self.status_label.configure(text=text)
        
    def enable_controls(self, state):
        val = "normal" if state else "disabled"
        self.select_wp_btn.configure(state=val)
        self.rand_wp_btn.configure(state=val)
        self.import_pkg_btn.configure(state=val)
        self.export_pkg_btn.configure(state=val)
        self.rand_style_btn.configure(state=val)
        
    def is_startup_enabled(self):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, "DepthClock")
                return True
            except FileNotFoundError:
                return False
            finally:
                winreg.CloseKey(key)
        except:
            return False
            
    def set_startup(self, enabled):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "depth_clock.py"))
        
        if sys.executable.endswith("python.exe"):
            pythonw_exe = sys.executable.lower().replace("python.exe", "pythonw.exe")
            cmd_str = f'"{pythonw_exe}" "{script_path}" --daemon'
        else:
            cmd_str = f'"{sys.executable}" --daemon'
            
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            if enabled:
                winreg.SetValueEx(key, "DepthClock", 0, winreg.REG_SZ, cmd_str)
                print("Registered startup boot hook.")
            else:
                try:
                    winreg.DeleteValue(key, "DepthClock")
                    print("Deregistered startup boot hook.")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print("Failed to update startup configuration registry:", e)
        
    def create_widgets(self):
        # Left Panel (Controls)
        left_panel = ctk.CTkScrollableFrame(self, width=420)
        left_panel.pack(side="left", fill="y", padx=15, pady=15)
        
        title_label = ctk.CTkLabel(left_panel, text="Depth Clock", font=("Segoe UI", 24, "bold"))
        title_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        self.status_label = ctk.CTkLabel(left_panel, text="Initializing...", font=("Segoe UI", 12, "italic"), text_color="gray")
        self.status_label.pack(anchor="w", padx=15, pady=(0, 10))
        
        # Wallpaper Action Buttons
        wp_btn_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        wp_btn_frame.pack(fill="x", padx=15, pady=2)
        
        self.select_wp_btn = ctk.CTkButton(wp_btn_frame, text="Choose Wallpaper", width=180, command=self.choose_wallpaper, state="disabled")
        self.select_wp_btn.pack(side="left", padx=(0, 10))
        
        self.rand_wp_btn = ctk.CTkButton(wp_btn_frame, text="Random Wallpaper", width=180, fg_color="#34495e", hover_color="#2c3e50", command=self.fetch_random_wallpaper, state="disabled")
        self.rand_wp_btn.pack(side="right")
        
        # Wallpaper Source Selector
        ctk.CTkLabel(left_panel, text="Random Wallpaper Source", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(5, 2))
        self.wp_source_dropdown = ctk.CTkComboBox(left_panel, values=["Picsum Photos (Random)", "Curated Nature (Unsplash)", "Curated Space & Stars", "Curated Cities & Architecture"])
        self.wp_source_dropdown.set("Picsum Photos (Random)")
        self.wp_source_dropdown.pack(fill="x", padx=15, pady=2)
        
        # Tabview for styling properties
        tabview = ctk.CTkTabview(left_panel)
        tabview.pack(fill="both", expand=True, padx=10, pady=5)
        
        depth_tab = tabview.add("Depth")
        clock_tab = tabview.add("Clock Style")
        position_tab = tabview.add("Clock Pos")
        
        # --- DEPTH TAB ---
        ctk.CTkLabel(depth_tab, text="Foreground Threshold", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(10, 5))
        self.threshold_slider = ctk.CTkSlider(depth_tab, from_=0, to=255, command=self.on_threshold_changed)
        self.threshold_slider.set(self.config_data["threshold"])
        self.threshold_slider.pack(fill="x", pady=5)
        
        self.threshold_val_lbl = ctk.CTkLabel(depth_tab, text=f"Value: {self.config_data['threshold']}", font=("Segoe UI", 12))
        self.threshold_val_lbl.pack(anchor="e")
        
        ctk.CTkLabel(depth_tab, text="Edge Softness (Blur)", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(10, 5))
        self.blur_slider = ctk.CTkSlider(depth_tab, from_=0, to=10, command=self.on_blur_changed)
        self.blur_slider.set(self.config_data["blur_radius"])
        self.blur_slider.pack(fill="x", pady=5)
        
        self.blur_val_lbl = ctk.CTkLabel(depth_tab, text=f"Radius: {self.config_data['blur_radius']}px", font=("Segoe UI", 12))
        self.blur_val_lbl.pack(anchor="e")
        
        ctk.CTkLabel(depth_tab, text="Edge Detail (Smoothstep Width)", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(10, 5))
        self.transition_slider = ctk.CTkSlider(depth_tab, from_=1, to=50, command=self.on_transition_changed)
        self.transition_slider.set(self.config_data.get("transition_width", 10))
        self.transition_slider.pack(fill="x", pady=5)
        
        self.transition_val_lbl = ctk.CTkLabel(depth_tab, text=f"Width: {self.config_data.get('transition_width', 10)}px", font=("Segoe UI", 12))
        self.transition_val_lbl.pack(anchor="e")
        
        # --- CLOCK STYLE TAB ---
        ctk.CTkLabel(clock_tab, text="Font Family", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(5, 5))
        self.font_combobox = ctk.CTkComboBox(clock_tab, values=["Segoe UI", "Arial", "Impact", "Georgia", "Courier New"], command=self.on_font_changed)
        self.font_combobox.set(self.config_data["font_family"])
        self.font_combobox.pack(fill="x", pady=5)
        
        ctk.CTkLabel(clock_tab, text="Font Size", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(5, 5))
        self.font_size_slider = ctk.CTkSlider(clock_tab, from_=10, to=500, command=self.on_size_changed)
        self.font_size_slider.set(self.config_data["font_size"])
        self.font_size_slider.pack(fill="x", pady=5)
        
        self.font_size_val_lbl = ctk.CTkLabel(clock_tab, text=f"{self.config_data['font_size']} px", font=("Segoe UI", 12))
        self.font_size_val_lbl.pack(anchor="e")
        
        # Font Color Presets
        ctk.CTkLabel(clock_tab, text="Font Color Presets", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(5, 2))
        color_frame = ctk.CTkFrame(clock_tab, fg_color="transparent")
        color_frame.pack(fill="x", pady=2)
        
        for color_code in PREMIUM_COLORS:
            btn = ctk.CTkButton(
                color_frame, 
                text="", 
                width=24, 
                height=24, 
                fg_color=color_code, 
                hover_color=color_code, 
                corner_radius=12,
                command=lambda c=color_code: self.on_color_selected(c)
            )
            btn.pack(side="left", padx=3)
            
        self.suggested_label = ctk.CTkLabel(clock_tab, text="Suggested Wallpaper Colors", font=("Segoe UI", 13, "bold"))
        self.suggested_label.pack(anchor="w", pady=(5, 2))
        self.suggested_color_frame = ctk.CTkFrame(clock_tab, fg_color="transparent")
        self.suggested_color_frame.pack(fill="x", pady=2)
        
        # --- CLOCK POS TAB ---
        ctk.CTkLabel(position_tab, text="Horizontal Position (X)", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(10, 5))
        self.pos_x_slider = ctk.CTkSlider(position_tab, from_=-1.0, to=2.0, command=self.on_pos_x_changed)
        self.pos_x_slider.set(self.config_data["pos_x_ratio"])
        self.pos_x_slider.pack(fill="x", pady=5)
        
        ctk.CTkLabel(position_tab, text="Vertical Position (Y)", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(10, 5))
        self.pos_y_slider = ctk.CTkSlider(position_tab, from_=-1.0, to=2.0, command=self.on_pos_y_changed)
        self.pos_y_slider.set(self.config_data["pos_y_ratio"])
        self.pos_y_slider.pack(fill="x", pady=5)
        
        ctk.CTkLabel(position_tab, text="Date Vertical Offset (Y)", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(10, 5))
        self.date_y_offset_slider = ctk.CTkSlider(position_tab, from_=-1.0, to=1.0, command=self.on_date_y_offset_changed)
        self.date_y_offset_slider.set(self.config_data.get("date_y_offset_ratio", -0.074))
        self.date_y_offset_slider.pack(fill="x", pady=5)
        
        # Right Panel (Preview & Action Hub)
        right_panel = ctk.CTkFrame(self)
        right_panel.pack(side="right", fill="both", expand=True, padx=15, pady=15)
        
        preview_title = ctk.CTkLabel(right_panel, text="3D Depth Preview", font=("Segoe UI", 16, "bold"))
        preview_title.pack(anchor="w", padx=15, pady=(15, 5))
        
        # Drag to position instruction
        drag_hint = ctk.CTkLabel(right_panel, text="💡 Tip: Click and drag anywhere on the screen below to position the clock!", font=("Segoe UI", 12, "italic"), text_color="#3498db")
        drag_hint.pack(anchor="w", padx=15, pady=(0, 5))
        
        # Interactive Tkinter Canvas
        self.preview_canvas = tk.Canvas(
            right_panel, 
            width=self.preview_canvas_w, 
            height=self.preview_canvas_h, 
            bg="black", 
            bd=0, 
            highlightthickness=0
        )
        self.preview_canvas.pack(padx=15, pady=5)
        
        # Bind mouse drag actions to allow direct dragging of the clock positioning ratios
        self.preview_canvas.bind("<Button-1>", self.on_canvas_click)
        self.preview_canvas.bind("<B1-Motion>", self.on_canvas_drag)
        
        # System & Time Options Grid (below canvas)
        sys_options_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        sys_options_frame.pack(fill="x", padx=15, pady=5)
        
        self.format_switch = ctk.CTkSwitch(sys_options_frame, text="24-Hour Format", command=self.on_format_changed)
        if self.config_data["format_24h"]:
            self.format_switch.select()
        else:
            self.format_switch.deselect()
        self.format_switch.grid(row=0, column=0, sticky="w", padx=10, pady=4)
        
        self.date_switch = ctk.CTkSwitch(sys_options_frame, text="Show Date", command=self.on_date_changed)
        if self.config_data.get("show_date", True):
            self.date_switch.select()
        else:
            self.date_switch.deselect()
        self.date_switch.grid(row=0, column=1, sticky="w", padx=10, pady=4)
        
        self.auto_color_switch = ctk.CTkSwitch(sys_options_frame, text="Auto Color Matching", command=self.on_auto_color_changed)
        if self.config_data.get("auto_color", False):
            self.auto_color_switch.select()
        else:
            self.auto_color_switch.deselect()
        self.auto_color_switch.grid(row=0, column=2, sticky="w", padx=10, pady=4)
        
        self.sync_lockscreen_switch = ctk.CTkSwitch(sys_options_frame, text="Sync to Lockscreen", command=self.on_sync_lockscreen_changed)
        if self.config_data.get("sync_lockscreen", False):
            self.sync_lockscreen_switch.select()
        else:
            self.sync_lockscreen_switch.deselect()
        self.sync_lockscreen_switch.grid(row=1, column=0, sticky="w", padx=10, pady=4)
        
        self.startup_switch = ctk.CTkSwitch(sys_options_frame, text="Run on Windows Startup", command=self.on_startup_changed)
        if self.is_startup_enabled():
            self.startup_switch.select()
        else:
            self.startup_switch.deselect()
        self.startup_switch.grid(row=1, column=1, sticky="w", padx=10, pady=4)
        
        # Action Buttons frame placed right below the System Options
        action_btn_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        action_btn_frame.pack(fill="x", padx=15, pady=10)
        
        self.import_pkg_btn = ctk.CTkButton(action_btn_frame, text="Import Pkg", width=130, fg_color="#d35400", hover_color="#e67e22", command=self.import_depthpkg, state="disabled")
        self.import_pkg_btn.pack(side="left", padx=(0, 8))
        
        self.export_pkg_btn = ctk.CTkButton(action_btn_frame, text="Export Pkg", width=130, fg_color="#2980b9", hover_color="#3498db", command=self.export_depthpkg, state="disabled")
        self.export_pkg_btn.pack(side="left", padx=(0, 8))
        
        self.rand_style_btn = ctk.CTkButton(action_btn_frame, text="Random Style", width=130, fg_color="#9b59b6", hover_color="#8e44ad", command=self.randomize_styles, state="disabled")
        self.rand_style_btn.pack(side="left", padx=(0, 8))
        
        apply_btn = ctk.CTkButton(action_btn_frame, text="Apply to Desktop", width=180, font=("Segoe UI", 14, "bold"), fg_color="#2ecc71", hover_color="#27ae60", command=self.apply_to_desktop)
        apply_btn.pack(side="right")
        
        self.info_lbl = ctk.CTkLabel(right_panel, text="Choose a wallpaper to generate the 3D effect preview.", font=("Segoe UI", 12), text_color="gray")
        self.info_lbl.pack(pady=(5, 0))
        
        # Warning alignment tip
        alignment_note = ctk.CTkLabel(right_panel, text="* Actual desktop alignment matches preview exactly via screen aspect ratios.", font=("Segoe UI", 11, "italic"), text_color="gray")
        alignment_note.pack(pady=(0, 5))
        
    def on_canvas_click(self, event):
        self.update_position_from_mouse(event)
        
    def on_canvas_drag(self, event):
        self.update_position_from_mouse(event)
        
    def update_position_from_mouse(self, event):
        if self.raw_wp_image is None:
            return
            
        # Constrain drag boundaries to preview canvas size
        x = max(0, min(event.x, self.preview_canvas_w))
        y = max(0, min(event.y, self.preview_canvas_h))
        
        # Convert into ratio coordinates (aspect ratio immune)
        rx = float(x / self.preview_canvas_w)
        ry = float(y / self.preview_canvas_h)
        
        self.config_data["pos_x_ratio"] = rx
        self.config_data["pos_y_ratio"] = ry
        
        # Sync to sliders
        self.pos_x_slider.set(rx)
        self.pos_y_slider.set(ry)
        
        self.save_config()
        self.update_preview()
        
    def choose_wallpaper(self):
        file_path = filedialog.askopenfilename(
            title="Select Wallpaper",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp")]
        )
        if file_path:
            self.wallpaper_path = file_path
            self.config_data["wallpaper_path"] = file_path
            self.save_config()
            self.process_wallpaper(file_path)
            
    def fetch_random_wallpaper(self):
        source_selection = self.wp_source_dropdown.get()
        self.set_status("Fetching random online wallpaper...")
        self.enable_controls(False)
        self.info_lbl.configure(text="Downloading high resolution photo...")
        
        def run_fetch():
            try:
                # Resolve Source URL
                if source_selection in CURATED_WALLPAPERS:
                    url = random.choice(CURATED_WALLPAPERS[source_selection])
                else:
                    sig = random.randint(1, 100000)
                    url = f"https://picsum.photos/{self.screen_w}/{self.screen_h}?random={sig}"
                
                headers = {'User-Agent': 'Mozilla/5.0'}
                req = urllib.request.Request(url, headers=headers)
                
                with urllib.request.urlopen(req) as response:
                    with open(RANDOM_WP_PATH, 'wb') as out_file:
                        out_file.write(response.read())
                        
                self.wallpaper_path = RANDOM_WP_PATH
                self.config_data["wallpaper_path"] = RANDOM_WP_PATH
                self.save_config()
                
                self.process_wallpaper(RANDOM_WP_PATH)
            except Exception as e:
                self.after(0, lambda: self.info_lbl.configure(text=f"Download Error: {e}"))
                self.after(0, lambda: self.set_status("Failed to fetch wallpaper."))
                self.after(0, lambda: self.enable_controls(True))
                
        threading.Thread(target=run_fetch, daemon=True).start()
        
    def randomize_styles(self):
        color_pool = PREMIUM_COLORS
        if hasattr(self, 'extracted_colors') and self.extracted_colors:
            color_pool = PREMIUM_COLORS + self.extracted_colors
            
        color = random.choice(color_pool)
        self.config_data["color"] = color
        
        font = random.choice(["Segoe UI", "Arial", "Impact", "Georgia", "Courier New"])
        self.font_combobox.set(font)
        self.config_data["font_family"] = font
        
        size = random.randint(90, 250)
        self.font_size_slider.set(size)
        self.font_size_val_lbl.configure(text=f"{size} px")
        self.config_data["font_size"] = size
        
        pos_x_ratio = random.uniform(0.2, 0.8)
        pos_y_ratio = random.uniform(0.25, 0.75)
        self.pos_x_slider.set(pos_x_ratio)
        self.pos_y_slider.set(pos_y_ratio)
        self.config_data["pos_x_ratio"] = pos_x_ratio
        self.config_data["pos_y_ratio"] = pos_y_ratio
        
        thresh = random.randint(80, 180)
        self.threshold_slider.set(thresh)
        self.threshold_val_lbl.configure(text=f"Value: {thresh}")
        self.config_data["threshold"] = thresh
        
        blur = random.randint(1, 5)
        self.blur_slider.set(blur)
        self.blur_val_lbl.configure(text=f"Radius: {blur}px")
        self.config_data["blur_radius"] = blur
        
        trans = random.randint(5, 25)
        self.transition_slider.set(trans)
        self.transition_val_lbl.configure(text=f"Width: {trans}px")
        self.config_data["transition_width"] = trans
        
        self.save_config()
        self.update_preview()
        
    def process_wallpaper(self, img_path):
        self.set_status("Analyzing depth maps...")
        self.info_lbl.configure(text="Processing image depth structure...")
        
        def run_inference():
            try:
                # Compute full resolution depth map
                depth = self.engine.compute_depth(img_path)
                
                # Save full resolution depth map to local APP_DIR
                full_depth_path = os.path.join(APP_DIR, "wallpaper_depth.png")
                Image.fromarray(depth).save(full_depth_path)
                
                self.config_data["depth_map_path"] = full_depth_path
                self.save_config()
                
                # Load images
                wp_raw = Image.open(img_path).convert("RGBA")
                depth_raw = Image.fromarray(depth).convert("L")
                
                # Use resize_to_fill to ensure identical aspect ratio scaling and cropping as the desktop
                self.raw_wp_image = resize_to_fill(wp_raw, self.preview_canvas_w, self.preview_canvas_h)
                self.raw_depth_image = resize_to_fill(depth_raw, self.preview_canvas_w, self.preview_canvas_h)
                
                # Extract dominant colors
                self.extracted_colors = get_dominant_colors(img_path, num_colors=5)
                
                self.after(0, self.on_processing_complete)
            except Exception as e:
                self.after(0, lambda: self.info_lbl.configure(text=f"Error: {e}"))
                self.after(0, lambda: self.set_status("Failed to generate depth map."))
                self.after(0, lambda: self.enable_controls(True))
                
        threading.Thread(target=run_inference, daemon=True).start()
        
    def on_processing_complete(self):
        self.set_status("Ready.")
        self.enable_controls(True)
        self.info_lbl.configure(text="Use depth slider to adjust layers. Click Apply to save.")
        
        if self.config_data.get("auto_color", False) and hasattr(self, 'extracted_colors') and self.extracted_colors:
            self.config_data["color"] = self.extracted_colors[0]
            self.save_config()
            
        self.update_suggested_colors()
        self.update_preview()
        
    def update_suggested_colors(self):
        for btn in self.suggested_buttons:
            btn.destroy()
        self.suggested_buttons.clear()
        
        if not hasattr(self, 'extracted_colors') or not self.extracted_colors:
            self.suggested_label.pack_forget()
            return
            
        self.suggested_label.pack(anchor="w", pady=(5, 2))
        
        # Populate buttons
        for color_code in self.extracted_colors:
            btn = ctk.CTkButton(
                self.suggested_color_frame, 
                text="", 
                width=24, 
                height=24, 
                fg_color=color_code, 
                hover_color=color_code, 
                corner_radius=12,
                command=lambda c=color_code: self.on_color_selected(c)
            )
            btn.pack(side="left", padx=3)
            self.suggested_buttons.append(btn)
            
    def update_preview(self):
        if self.raw_wp_image is None or self.raw_depth_image is None:
            return
            
        threshold = int(self.threshold_slider.get())
        blur_radius = int(self.blur_slider.get())
        
        # 1. Background layer
        bg_photo = ImageTk.PhotoImage(self.raw_wp_image)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(0, 0, anchor="nw", image=bg_photo)
        self.bg_photo_ref = bg_photo # keep reference
        
        # 2. Draw Clock & Date
        font_family = self.font_combobox.get()
        scale_factor = self.preview_canvas_w / self.screen_w
        preview_font_size = max(10, int(self.config_data["font_size"] * scale_factor))
        
        # Calculate preview coordinates using ratios (100% immune to DPI/Scaling shifts)
        preview_x = int(self.preview_canvas_w * self.config_data["pos_x_ratio"])
        preview_y = int(self.preview_canvas_h * self.config_data["pos_y_ratio"])
        
        time_str = time.strftime("%H:%M" if self.config_data["format_24h"] else "%I:%M %p")
        if time_str.startswith("0") and not self.config_data["format_24h"]:
            time_str = time_str[1:]
            
        # Draw Date if enabled
        if self.config_data.get("show_date", True):
            date_str = time.strftime(self.config_data.get("date_format", "%a, %b %d"))
            preview_date_size = max(8, int(preview_font_size * 0.3))
            
            # Apply scale factor to date Y offset ratio
            preview_date_offset = int(self.preview_canvas_h * self.config_data.get("date_y_offset_ratio", -0.074))
            date_y = preview_y + preview_date_offset
            
            self.preview_canvas.create_text(
                preview_x, 
                date_y, 
                text=date_str, 
                font=(font_family, preview_date_size, "bold"), 
                fill=self.config_data["color"], 
                anchor="center"
            )
            
        # Draw Clock Time
        self.preview_canvas.create_text(
            preview_x, 
            preview_y, 
            text=time_str, 
            font=(font_family, preview_font_size, "bold"), 
            fill=self.config_data["color"], 
            anchor="center"
        )
        
        # 3. Masked Foreground layer with smoothstep anti-aliasing
        depth_np = np.array(self.raw_depth_image, dtype=np.float32)
        w = max(1, int(self.config_data.get("transition_width", 10)))
        t = (depth_np - (threshold - w)) / (2 * w)
        t = np.clip(t, 0.0, 1.0)
        
        alpha_np = (255 * (3 * t**2 - 2 * t**3)).astype(np.uint8)
        mask = Image.fromarray(alpha_np)
        
        if blur_radius > 0:
            mask = mask.filter(ImageFilter.GaussianBlur(blur_radius))
            
        fg_img = self.raw_wp_image.copy()
        fg_img.putalpha(mask)
        
        fg_photo = ImageTk.PhotoImage(fg_img)
        self.preview_canvas.create_image(0, 0, anchor="nw", image=fg_photo)
        self.fg_photo_ref = fg_photo # keep reference
        
    def on_threshold_changed(self, value):
        self.config_data["threshold"] = int(value)
        self.threshold_val_lbl.configure(text=f"Value: {int(value)}")
        self.save_config()
        self.update_preview()
        
    def on_blur_changed(self, value):
        self.config_data["blur_radius"] = int(value)
        self.blur_val_lbl.configure(text=f"Radius: {int(value)}px")
        self.save_config()
        self.update_preview()
        
    def on_transition_changed(self, value):
        self.config_data["transition_width"] = int(value)
        self.transition_val_lbl.configure(text=f"Width: {int(value)}px")
        self.save_config()
        self.update_preview()
        
    def on_font_changed(self, value):
        self.config_data["font_family"] = value
        self.save_config()
        self.update_preview()
        
    def on_size_changed(self, value):
        self.config_data["font_size"] = int(value)
        self.font_size_val_lbl.configure(text=f"{int(value)} px")
        self.save_config()
        self.update_preview()
        
    def on_color_selected(self, color):
        self.config_data["color"] = color
        self.save_config()
        self.update_preview()
        
    def on_format_changed(self):
        self.config_data["format_24h"] = self.format_switch.get()
        self.save_config()
        self.update_preview()
        
    def on_date_changed(self):
        self.config_data["show_date"] = self.date_switch.get()
        self.save_config()
        self.update_preview()
        
    def on_sync_lockscreen_changed(self):
        self.config_data["sync_lockscreen"] = self.sync_lockscreen_switch.get()
        self.save_config()
        
    def on_startup_changed(self):
        self.set_startup(self.startup_switch.get())
        
    def on_auto_color_changed(self):
        self.config_data["auto_color"] = self.auto_color_switch.get()
        self.save_config()
        if self.config_data["auto_color"] and hasattr(self, 'extracted_colors') and self.extracted_colors:
            self.config_data["color"] = self.extracted_colors[0]
            self.save_config()
            self.update_preview()
        
    def on_pos_x_changed(self, value):
        self.config_data["pos_x_ratio"] = float(value)
        self.save_config()
        self.update_preview()
        
    def on_pos_y_changed(self, value):
        self.config_data["pos_y_ratio"] = float(value)
        self.save_config()
        self.update_preview()
        
    def on_date_y_offset_changed(self, value):
        self.config_data["date_y_offset_ratio"] = float(value)
        self.save_config()
        self.update_preview()
        
    def export_depthpkg(self):
        if not self.wallpaper_path or not os.path.exists(self.wallpaper_path):
            self.set_status("No wallpaper loaded to export.")
            return
            
        depth_map_path = self.config_data.get("depth_map_path", "")
        if not depth_map_path or not os.path.exists(depth_map_path):
            self.set_status("No depth map generated to export.")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Export Depth Package",
            defaultextension=".depthpkg",
            filetypes=[("Depth Package", "*.depthpkg")]
        )
        if not file_path:
            return
            
        try:
            self.set_status("Exporting package...")
            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(self.wallpaper_path, "wallpaper.png")
                zipf.write(depth_map_path, "depth_map.png")
                
                clean_config = self.config_data.copy()
                clean_config["wallpaper_path"] = "wallpaper.png"
                clean_config["depth_map_path"] = "depth_map.png"
                
                zipf.writestr("config.json", json.dumps(clean_config, indent=4))
            self.set_status("Package exported successfully!")
        except Exception as e:
            self.set_status(f"Export failed: {e}")

    def import_depthpkg(self):
        file_path = filedialog.askopenfilename(
            title="Import Depth Package",
            filetypes=[("Depth Package", "*.depthpkg")]
        )
        if not file_path:
            return
            
        try:
            self.set_status("Importing package...")
            os.makedirs(APP_DIR, exist_ok=True)
            
            target_wallpaper = os.path.join(APP_DIR, "wallpaper.png")
            target_depth_map = os.path.join(APP_DIR, "wallpaper_depth.png")
            
            with zipfile.ZipFile(file_path, 'r') as zipf:
                zipf.extract("wallpaper.png", APP_DIR)
                zipf.extract("depth_map.png", APP_DIR)
                config_content = zipf.read("config.json").decode("utf-8")
                
            # Rename the depth_map.png to wallpaper_depth.png to prevent misalignment or cached depth files
            extracted_depth = os.path.join(APP_DIR, "depth_map.png")
            if os.path.exists(extracted_depth):
                if os.path.exists(target_depth_map):
                    os.remove(target_depth_map)
                os.rename(extracted_depth, target_depth_map)
                
            imported_config = json.loads(config_content)
            
            # Override paths to local absolute paths
            imported_config["wallpaper_path"] = target_wallpaper
            imported_config["depth_map_path"] = target_depth_map
            
            self.config_data.update(imported_config)
            self.save_config()
            
            self.wallpaper_path = target_wallpaper
            
            # Reload preview images
            self.raw_wp_image = resize_to_fill(Image.open(target_wallpaper).convert("RGBA"), self.preview_canvas_w, self.preview_canvas_h)
            self.raw_depth_image = resize_to_fill(Image.open(target_depth_map).convert("L"), self.preview_canvas_w, self.preview_canvas_h)
            self.extracted_colors = get_dominant_colors(target_wallpaper, num_colors=5)
            
            # Update UI controls
            self.threshold_slider.set(self.config_data["threshold"])
            self.threshold_val_lbl.configure(text=f"Value: {self.config_data['threshold']}")
            
            self.blur_slider.set(self.config_data["blur_radius"])
            self.blur_val_lbl.configure(text=f"Radius: {self.config_data['blur_radius']}px")
            
            self.transition_slider.set(self.config_data.get("transition_width", 10))
            self.transition_val_lbl.configure(text=f"Width: {self.config_data.get('transition_width', 10)}px")
            
            self.font_combobox.set(self.config_data["font_family"])
            
            self.font_size_slider.set(self.config_data["font_size"])
            self.font_size_val_lbl.configure(text=f"{self.config_data['font_size']} px")
            
            if self.config_data["format_24h"]:
                self.format_switch.select()
            else:
                self.format_switch.deselect()
                
            if self.config_data.get("show_date", True):
                self.date_switch.select()
            else:
                self.date_switch.deselect()
                
            if self.config_data.get("sync_lockscreen", False):
                self.sync_lockscreen_switch.select()
            else:
                self.sync_lockscreen_switch.deselect()
                
            self.pos_x_slider.set(self.config_data["pos_x_ratio"])
            self.pos_y_slider.set(self.config_data["pos_y_ratio"])
            self.date_y_offset_slider.set(self.config_data.get("date_y_offset_ratio", -0.074))
            
            self.update_suggested_colors()
            self.update_preview()
            self.set_status("Package imported successfully!")
        except Exception as e:
            self.set_status(f"Import failed: {e}")
            
    def apply_to_desktop(self):
        self.save_config()
        self.set_status("Applying settings to desktop wallpaper...")
        
        import subprocess
        
        # Kill existing wallpaper daemon if it was run from this instance
        if self.renderer_process:
            try:
                self.renderer_process.terminate()
            except:
                pass
                
        # Run wallpaper daemon process (using pythonw to hide console windows)
        try:
            if sys.executable.endswith("python.exe"):
                pythonw_exe = sys.executable.lower().replace("python.exe", "pythonw.exe")
            else:
                pythonw_exe = sys.executable
                
            cmd = [pythonw_exe, "wallpaper_daemon.py"]
            self.renderer_process = subprocess.Popen(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
            self.set_status("Applied successfully!")
        except Exception as e:
            self.set_status(f"Failed to start wallpaper daemon: {e}")

if __name__ == "__main__":
    app = DepthClockGUI()
    app.mainloop()
