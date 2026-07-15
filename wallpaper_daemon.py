import os
import time
import json
import ctypes
import numpy as np
import threading
import random
import urllib.request
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import win32api
import win32gui
import win32con
import win32process
import pystray
from pystray import MenuItem as item

APP_DIR = os.path.join(os.path.expanduser("~"), ".depthclock")
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
TEMP_WALLPAPER_PATH = os.path.join(APP_DIR, "depth_wallpaper.png")
RANDOM_WP_PATH = os.path.join(APP_DIR, "random_wallpaper.jpg")

# Enable DPI Awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

# Global state
paused = False
running = True

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

def set_desktop_wallpaper(image_path):
    ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 3)

def set_lockscreen_wallpaper(image_path):
    """
    Sets the lockscreen wallpaper using native Windows UWP WinRT APIs called via PowerShell.
    Works natively on Windows 10/11 without requiring administrative rights.
    """
    abs_path = os.path.abspath(image_path)
    ps_cmd = (
        f'[Windows.System.UserProfile.LockScreen, Windows.System.UserProfile, ContentType=WindowsRuntime] | Out-Null; '
        f'[Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime] | Out-Null; '
        f'$file = [Windows.Storage.StorageFile]::GetFileFromPathAsync("{abs_path}").GetAwaiter().GetResult(); '
        f'[Windows.System.UserProfile.LockScreen]::SetImageFileAsync($file).GetAwaiter().GetResult();'
    )
    try:
        # Run PowerShell silently
        subprocess.run(["powershell", "-WindowStyle", "Hidden", "-Command", ps_cmd], capture_output=True)
        print("Lockscreen wallpaper sync complete.")
    except Exception as e:
        print("Failed to sync lockscreen wallpaper:", e)

def is_fullscreen_app_active(screen_w, screen_h):
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return False
        
    class_name = win32gui.GetClassName(hwnd)
    if class_name in ["WorkerW", "Progman", "Shell_TrayWnd", "DV2ControlHost"]:
        return False
        
    try:
        rect = win32gui.GetWindowRect(hwnd)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        
        if width >= screen_w and height >= screen_h:
            return True
    except:
        pass
    return False

def render_and_apply():
    if not os.path.exists(CONFIG_PATH):
        return False
        
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return False
        
    wallpaper_path = config.get("wallpaper_path", "")
    depth_map_path = config.get("depth_map_path", "")
    threshold = config.get("threshold", 128)
    blur_radius = config.get("blur_radius", 2)
    transition_width = config.get("transition_width", 10)
    
    font_family = config.get("font_family", "Segoe UI")
    font_size = config.get("font_size", 120)
    color = config.get("color", "#FFFFFF")
    format_24h = config.get("format_24h", True)
    show_date = config.get("show_date", True)
    sync_lockscreen = config.get("sync_lockscreen", False)
    
    if not os.path.exists(wallpaper_path):
        return False
        
    screen_w = win32api.GetSystemMetrics(0)
    screen_h = win32api.GetSystemMetrics(1)
    
    # 1. Load wallpaper and crop to cover screen
    wp_raw = Image.open(wallpaper_path).convert("RGBA")
    wp_img = resize_to_fill(wp_raw, screen_w, screen_h)
    
    # 2. Draw text on a copy of the wallpaper
    bg_with_clock = wp_img.copy()
    draw = ImageDraw.Draw(bg_with_clock)
    
    pos_x = int(screen_w * config.get("pos_x_ratio", 0.5))
    pos_y = int(screen_h * config.get("pos_y_ratio", 0.3))
    
    try:
        font_path = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", f"{font_family.lower()}.ttf")
        if not os.path.exists(font_path):
            font_path = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "arialbd.ttf")
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()
        
    if show_date:
        date_str = time.strftime(config.get("date_format", "%a, %b %d"))
        date_font_size = max(12, int(font_size * 0.3))
        try:
            date_font_path = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", f"{font_family.lower()}.ttf")
            if not os.path.exists(date_font_path):
                date_font_path = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "arialbd.ttf")
            date_font = ImageFont.truetype(date_font_path, date_font_size)
        except:
            date_font = ImageFont.load_default()
            
        date_y_offset = int(screen_h * config.get("date_y_offset_ratio", -0.074))
        draw.text((pos_x, pos_y + date_y_offset), date_str, font=date_font, fill=color, anchor="mm")
        
    time_format = "%H:%M" if format_24h else "%I:%M %p"
    time_str = time.strftime(time_format)
    if time_str.startswith("0") and not format_24h:
        time_str = time_str[1:]
        
    draw.text((pos_x, pos_y), time_str, font=font, fill=color, anchor="mm")
    
    # 3. Apply foreground mask
    if os.path.exists(depth_map_path):
        depth_raw = Image.open(depth_map_path).convert("L")
        depth_img = resize_to_fill(depth_raw, screen_w, screen_h)
        
        depth_np = np.array(depth_img, dtype=np.float32)
        w = max(1, transition_width)
        t = (depth_np - (threshold - w)) / (2 * w)
        t = np.clip(t, 0.0, 1.0)
        
        alpha_np = (255 * (3 * t**2 - 2 * t**3)).astype(np.uint8)
        mask = Image.fromarray(alpha_np)
        
        if blur_radius > 0:
            mask = mask.filter(ImageFilter.GaussianBlur(blur_radius))
            
        final_image = bg_with_clock.copy()
        final_image.paste(wp_img, (0, 0), mask)
    else:
        final_image = bg_with_clock
        
    final_image.convert("RGB").save(TEMP_WALLPAPER_PATH, "PNG")
    
    # Apply to Desktop
    set_desktop_wallpaper(TEMP_WALLPAPER_PATH)
    
    # Sync with Lockscreen if requested
    if sync_lockscreen:
        # Run in a background thread to prevent GUI/daemon hiccups
        threading.Thread(target=set_lockscreen_wallpaper, args=(TEMP_WALLPAPER_PATH,), daemon=True).start()
        
    return True

def trigger_random_wallpaper():
    try:
        print("Fetching random wallpaper...")
        sig = random.randint(1, 100000)
        screen_w = win32api.GetSystemMetrics(0)
        screen_h = win32api.GetSystemMetrics(1)
        url = f"https://picsum.photos/{screen_w}/{screen_h}?random={sig}"
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req) as response:
            with open(RANDOM_WP_PATH, 'wb') as out_file:
                out_file.write(response.read())
                
        # Generate depth map
        from depth_engine import DepthEngine
        engine = DepthEngine()
        depth = engine.compute_depth(RANDOM_WP_PATH)
        
        full_depth_path = os.path.join(APP_DIR, "wallpaper_depth.png")
        Image.fromarray(depth).save(full_depth_path)
        
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
        else:
            config = {}
            
        config["wallpaper_path"] = RANDOM_WP_PATH
        config["depth_map_path"] = full_depth_path
        
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=4)
            
        print("Random wallpaper processed and saved.")
    except Exception as e:
        print("Error fetching random wallpaper:", e)

# Tray actions
def on_quit(icon, item):
    global running
    running = False
    icon.stop()
    os._exit(0)

def on_toggle_pause(icon, item):
    global paused
    paused = not paused
    print("Daemon paused:", paused)

def on_launch_settings(icon, item):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cmd = ["python", os.path.join(script_dir, "gui.py")]
    subprocess.Popen(cmd, cwd=script_dir)

def on_next_wallpaper(icon, item):
    threading.Thread(target=trigger_random_wallpaper, daemon=True).start()

def create_tray_icon():
    # Create a simple 64x64 clock icon image on-the-fly
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw clock ring
    draw.ellipse((8, 8, 56, 56), fill="#2c3e50", outline="#00F2FE", width=4)
    # Draw hands
    draw.line((32, 32, 32, 18), fill="#00F2FE", width=4)
    draw.line((32, 32, 44, 32), fill="#00F2FE", width=4)
    
    # Define menu
    menu = (
        item("Configure Settings", on_launch_settings),
        item("Next Wallpaper", on_next_wallpaper),
        item("Pause Updates", on_toggle_pause, checked=lambda item: paused),
        item("Quit", on_quit)
    )
    
    icon = pystray.Icon("depthclock", image, "Depth Clock", menu)
    return icon

def daemon_loop():
    global paused, running
    screen_w = win32api.GetSystemMetrics(0)
    screen_h = win32api.GetSystemMetrics(1)
    
    last_minute = -1
    last_config_mtime = 0
    was_fullscreen_paused = False
    
    while running:
        # Fullscreen app check
        if is_fullscreen_app_active(screen_w, screen_h):
            if not was_fullscreen_paused:
                print("Fullscreen app detected. Suspending updates...")
                was_fullscreen_paused = True
            time.sleep(5.0)
            continue
            
        if was_fullscreen_paused:
            print("Returned to desktop. Resuming updates...")
            was_fullscreen_paused = False
            render_and_apply()
            
        if paused:
            time.sleep(1.0)
            continue
            
        current_time_struct = time.localtime()
        current_minute = current_time_struct.tm_min
        
        config_modified = False
        if os.path.exists(CONFIG_PATH):
            mtime = os.path.getmtime(CONFIG_PATH)
            if mtime > last_config_mtime:
                last_config_mtime = mtime
                config_modified = True
                
        if current_minute != last_minute or config_modified:
            last_minute = current_minute
            print(f"Updating wallpaper: {time.strftime('%H:%M:%S')}")
            try:
                render_and_apply()
            except Exception as e:
                print(f"Error rendering: {e}")
                
        time.sleep(1.0)

def main():
    # Start loop in a background thread
    loop_thread = threading.Thread(target=daemon_loop, daemon=True)
    loop_thread.start()
    
    # Run tray icon on main thread (required by OS window loops)
    icon = create_tray_icon()
    icon.run()

if __name__ == "__main__":
    main()
