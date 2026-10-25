import os
import sys
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
import win32event
import winerror
import pystray
from pystray import MenuItem as item
import base64

from wallpaper_sources import CURATED_WALLPAPERS, get_wallpaper_url
from auto_optimizer import resolve_font_path, auto_optimize_depth_clock

APP_DIR = os.path.join(os.path.expanduser("~"), ".depthclock")
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
TEMP_WALLPAPER_PATH = os.path.join(APP_DIR, "depth_wallpaper.png")
RANDOM_WP_PATH = os.path.join(APP_DIR, "random_wallpaper.jpg")
GALLERY_DIR = os.path.join(APP_DIR, "gallery")
GALLERY_DEPTH_DIR = os.path.join(APP_DIR, "gallery_depth")

INTERVAL_SECONDS = {
    "15 Minutes": 15 * 60,
    "30 Minutes": 30 * 60,
    "1 Hour": 60 * 60,
    "3 Hours": 3 * 3600,
    "6 Hours": 6 * 3600,
    "12 Hours": 12 * 3600,
    "Daily": 24 * 3600
}

_rotation_lock = threading.Lock()
_last_rotation_time = time.time()


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

# Cache state for render loop optimization
_cached_wp_path = None
_cached_wp_img = None
_cached_depth_path = None
_cached_depth_img = None
_cached_wp_screen_w = None
_cached_wp_screen_h = None
_cached_depth_screen_w = None
_cached_depth_screen_h = None

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
    safe_path = abs_path.replace("'", "''")
    ps_script = (
        f'[Windows.System.UserProfile.LockScreen, Windows.System.UserProfile, ContentType=WindowsRuntime] | Out-Null; '
        f'[Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime] | Out-Null; '
        f'$file = [Windows.Storage.StorageFile]::GetFileFromPathAsync(\'{safe_path}\').GetAwaiter().GetResult(); '
        f'[Windows.System.UserProfile.LockScreen]::SetImageFileAsync($file).GetAwaiter().GetResult();'
    )
    encoded_cmd = base64.b64encode(ps_script.encode('utf-16le')).decode('utf-8')
    try:
        # Run PowerShell silently via EncodedCommand
        subprocess.run(["powershell", "-WindowStyle", "Hidden", "-EncodedCommand", encoded_cmd], capture_output=True)
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
    global _cached_wp_path, _cached_wp_img, _cached_depth_path, _cached_depth_img
    global _cached_wp_screen_w, _cached_wp_screen_h, _cached_depth_screen_w, _cached_depth_screen_h

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
    if (_cached_wp_img is not None and
        _cached_wp_path == wallpaper_path and
        _cached_wp_screen_w == screen_w and
        _cached_wp_screen_h == screen_h):
        wp_img = _cached_wp_img
    else:
        wp_raw = Image.open(wallpaper_path).convert("RGBA")
        wp_img = resize_to_fill(wp_raw, screen_w, screen_h)
        _cached_wp_path = wallpaper_path
        _cached_wp_img = wp_img
        _cached_wp_screen_w = screen_w
        _cached_wp_screen_h = screen_h
    
    # 2. Draw text on a copy of the wallpaper
    bg_with_clock = wp_img.copy()
    draw = ImageDraw.Draw(bg_with_clock)
    
    pos_x = int(screen_w * config.get("pos_x_ratio", 0.5))
    pos_y = int(screen_h * config.get("pos_y_ratio", 0.3))
    
    try:
        resolved_path = resolve_font_path(font_family)
        if resolved_path and os.path.exists(resolved_path):
            font = ImageFont.truetype(resolved_path, font_size)
        else:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
        
    if show_date:
        date_str = time.strftime(config.get("date_format", "%a, %b %d"))
        date_font_size = max(12, int(font_size * 0.3))
        try:
            resolved_path = resolve_font_path(font_family)
            if resolved_path and os.path.exists(resolved_path):
                date_font = ImageFont.truetype(resolved_path, date_font_size)
            else:
                date_font = ImageFont.load_default()
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
        if (_cached_depth_img is not None and
            _cached_depth_path == depth_map_path and
            _cached_depth_screen_w == screen_w and
            _cached_depth_screen_h == screen_h):
            depth_img = _cached_depth_img
        else:
            depth_raw = Image.open(depth_map_path).convert("L")
            depth_img = resize_to_fill(depth_raw, screen_w, screen_h)
            _cached_depth_path = depth_map_path
            _cached_depth_img = depth_img
            _cached_depth_screen_w = screen_w
            _cached_depth_screen_h = screen_h

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
    global _last_rotation_time
    if not _rotation_lock.acquire(blocking=False):
        print("Wallpaper rotation already in progress, skipping.")
        return
    try:
        _last_rotation_time = time.time()
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
        else:
            config = {}

        change_mode = config.get("change_mode", "Online Curated")
        random_wp_source = config.get("random_wp_source", "Picsum Photos (Random)")
        cutout_mode = config.get("cutout_mode", "Gradient Depth (MiDaS)")
        current_wp = config.get("wallpaper_path", "")

        # Try gallery mode if selected
        if change_mode == "Local Gallery History" and os.path.exists(GALLERY_DIR) and os.path.exists(GALLERY_DEPTH_DIR):
            candidates = []
            for f in os.listdir(GALLERY_DIR):
                if f.endswith(".png"):
                    wp_f = os.path.join(GALLERY_DIR, f)
                    dp_f = os.path.join(GALLERY_DEPTH_DIR, f)
                    if os.path.exists(dp_f):
                        candidates.append((wp_f, dp_f))

            if candidates:
                if len(candidates) > 1:
                    pool = [c for c in candidates if c[0] != current_wp]
                    selected = random.choice(pool if pool else candidates)
                else:
                    selected = candidates[0]

                print(f"Rotating from gallery: {selected[0]}")
                config["wallpaper_path"] = selected[0]
                config["depth_map_path"] = selected[1]
                with open(CONFIG_PATH, "w") as f:
                    json.dump(config, f, indent=4)
                render_and_apply()
                return

        # Online Curated mode
        print(f"Fetching online wallpaper from source: {random_wp_source}...")
        screen_w = win32api.GetSystemMetrics(0)
        screen_h = win32api.GetSystemMetrics(1)
        url = get_wallpaper_url(random_wp_source, screen_w, screen_h)

        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)

        os.makedirs(APP_DIR, exist_ok=True)
        with urllib.request.urlopen(req) as response:
            with open(RANDOM_WP_PATH, 'wb') as out_file:
                out_file.write(response.read())

        # Generate depth/cutout map
        from depth_engine import DepthEngine
        engine = DepthEngine()

        if "Salient Subject" in cutout_mode:
            model_type = "u2net" if "176MB" in cutout_mode else "u2netp"
            u2net_path = os.path.join(APP_DIR, "u2net.onnx" if model_type == "u2net" else "u2netp.onnx")
            if not os.path.exists(u2net_path):
                from depth_engine import download_u2net
                download_u2net(model_type)
            depth = engine.compute_subject_mask(RANDOM_WP_PATH, model_type)
        else:
            depth = engine.compute_depth(RANDOM_WP_PATH)

        full_depth_path = os.path.join(APP_DIR, "wallpaper_depth.png")
        Image.fromarray(depth).save(full_depth_path)

        # Cache in gallery
        try:
            import hashlib
            import shutil
            os.makedirs(GALLERY_DIR, exist_ok=True)
            os.makedirs(GALLERY_DEPTH_DIR, exist_ok=True)
            with open(RANDOM_WP_PATH, 'rb') as f:
                h = hashlib.sha256(f.read()).hexdigest()
            cached_wp = os.path.join(GALLERY_DIR, f"{h}.png")
            cached_depth = os.path.join(GALLERY_DEPTH_DIR, f"{h}.png")
            if not os.path.exists(cached_wp):
                shutil.copy(RANDOM_WP_PATH, cached_wp)
            if not os.path.exists(cached_depth):
                shutil.copy(full_depth_path, cached_depth)
        except Exception as cache_err:
            print("Failed to cache in gallery:", cache_err)

        config["wallpaper_path"] = RANDOM_WP_PATH
        config["depth_map_path"] = full_depth_path

        # Automatically optimize depth clock layout for seamless overlap and contrast
        try:
            opt = auto_optimize_depth_clock(
                Image.open(RANDOM_WP_PATH),
                Image.fromarray(depth),
                screen_w,
                screen_h
            )
            config.update(opt)
            print("Auto-optimized layout:", opt)
        except Exception as opt_err:
            print("Auto-optimization warning:", opt_err)

        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=4)

        print("Random wallpaper processed and saved.")
        render_and_apply()
    except Exception as e:
        print("Error fetching random wallpaper:", e)
    finally:
        _rotation_lock.release()

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
    if sys.executable.lower().endswith("python.exe") or sys.executable.lower().endswith("pythonw.exe"):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cmd = ["python", os.path.join(script_dir, "gui.py")]
        cwd = script_dir
    else:
        cmd = [sys.executable]
        cwd = os.path.dirname(sys.executable)
    subprocess.Popen(cmd, cwd=cwd)

def on_next_wallpaper(icon, item):
    global _last_rotation_time
    _last_rotation_time = time.time()
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
    global paused, running, _last_rotation_time
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
        config = {}
        if os.path.exists(CONFIG_PATH):
            try:
                mtime = os.path.getmtime(CONFIG_PATH)
                if mtime > last_config_mtime:
                    last_config_mtime = mtime
                    config_modified = True
                with open(CONFIG_PATH, "r") as f:
                    config = json.load(f)
            except Exception:
                pass
                
        # Check auto-change wallpaper interval
        if config.get("auto_change_enabled", False):
            interval_str = config.get("auto_change_interval", "1 Hour")
            interval_sec = INTERVAL_SECONDS.get(interval_str, 3600)
            now = time.time()
            if (now - _last_rotation_time) >= interval_sec:
                print(f"Auto-change interval reached ({interval_str}). Rotating wallpaper...")
                _last_rotation_time = now
                threading.Thread(target=trigger_random_wallpaper, daemon=True).start()

        if current_minute != last_minute or config_modified:
            last_minute = current_minute
            print(f"Updating wallpaper: {time.strftime('%H:%M:%S')}")
            try:
                render_and_apply()
            except Exception as e:
                print(f"Error rendering: {e}")
                
        time.sleep(1.0)

# Global mutex handle to prevent garbage collection
daemon_mutex = None

def main():
    global daemon_mutex
    daemon_mutex = win32event.CreateMutex(None, False, "DepthClockDaemonMutex")
    if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
        print("Daemon is already running. Exiting.")
        sys.exit(0)

    # Start loop in a background thread
    loop_thread = threading.Thread(target=daemon_loop, daemon=True)
    loop_thread.start()
    
    # Run tray icon on main thread (required by OS window loops)
    icon = create_tray_icon()
    icon.run()

if __name__ == "__main__":
    main()
