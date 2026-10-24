import os
import time
import json
import ctypes
import numpy as np
import threading
import random
import urllib.request
import subprocess

CURATED_WALLPAPERS = {
    "Curated Nature (Unsplash)": [
        "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1472214222541-d510753a8707?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1501854140801-50d01698950b?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1426604966848-d7adac402bff?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1433086966358-54859d0ed716?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1470813740244-df37b8c1edcb?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1504608524841-42fe6f032b4b?auto=format&fit=crop&q=80&w=1920"
    ],
    "Curated Space & Stars": [
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1506318137071-a8e063b4bec0?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1538370965046-79c0d6907d47?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1464802686167-b939a6910659?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1481819613568-3701cbc70156?auto=format&fit=crop&q=80&w=1920"
    ],
    "Curated Cities & Architecture": [
        "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1449034446853-66c86144b0ad?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1519501025264-65ba15a82390?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1449844908441-8829872d2607?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1444723121867-7a241cacace9?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1517581177682-a085bb7ffb15?auto=format&fit=crop&q=80&w=1920"
    ],
    "Curated Abstract": [
        "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1541701494587-cb58502866ab?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1579546929518-9e396f3cc809?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1546484396-fb3fc6f95f98?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1563089145-599997674dc9?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1558591710-4b4a1ae0f04d?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1500462918059-b1a0cb512f1d?auto=format&fit=crop&q=80&w=1920"
    ],
    "Curated Minimalist": [
        "https://images.unsplash.com/photo-1494438639946-1ebd1d20bf85?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1449247709967-d4461a6a6103?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1435820394963-a15297f976fd?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1507721999472-8ed4421c4af2?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1453928582365-b6ad33cbcf64?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1513542789411-b6a5d4f31634?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1506744626753-97992928574c?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1483728642387-6c3ba6c6276b?auto=format&fit=crop&q=80&w=1920"
    ],
    "Curated Animals": [
        "https://images.unsplash.com/photo-1543946207-39fdc172e1c3?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1456926631375-92c8ce872def?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1546182990-dffeafbe841d?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1534567153574-2b12153a87f0?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1437622368342-7a3d73a34c8f?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1555169062-013468b47731?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1564349683136-77e08dba1ef7?auto=format&fit=crop&q=80&w=1920",
        "https://images.unsplash.com/photo-1574144611814-484d8ee9638c?auto=format&fit=crop&q=80&w=1920"
    ]
}
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import win32api
import win32gui
import win32con
import win32process
import pystray
from pystray import MenuItem as item
import base64

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
    try:
        print("Fetching random wallpaper...")

        # Load config to check random_wp_source
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
        else:
            config = {}

        source = config.get("random_wp_source", "Picsum Photos (Random)")

        if source in CURATED_WALLPAPERS:
            url = random.choice(CURATED_WALLPAPERS[source])
        else:
            sig = random.randint(1, 100000)
            screen_w = win32api.GetSystemMetrics(0)
            screen_h = win32api.GetSystemMetrics(1)
            url = f"https://picsum.photos/{screen_w}/{screen_h}?random={sig}"
            if source == "Picsum Photos (Grayscale)":
                url += "&grayscale"
            elif source == "Picsum Photos (Blur)":
                url += "&blur"
            elif source == "Picsum Photos (Grayscale & Blur)":
                url += "&grayscale&blur"
        
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
    if sys.executable.lower().endswith("python.exe") or sys.executable.lower().endswith("pythonw.exe"):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cmd = ["python", os.path.join(script_dir, "gui.py")]
        cwd = script_dir
    else:
        cmd = [sys.executable]
        cwd = os.path.dirname(sys.executable)
    subprocess.Popen(cmd, cwd=cwd)

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
