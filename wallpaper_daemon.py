import os
import time
import json
import ctypes
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import win32api

APP_DIR = os.path.join(os.path.expanduser("~"), ".depthclock")
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
TEMP_WALLPAPER_PATH = os.path.join(APP_DIR, "depth_wallpaper.png")

# Enable DPI Awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

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
    
    # Get primary screen size
    screen_w = win32api.GetSystemMetrics(0)
    screen_h = win32api.GetSystemMetrics(1)
    
    # Clock and Date configurations
    font_family = config.get("font_family", "Segoe UI")
    font_size = config.get("font_size", 120)
    color = config.get("color", "#FFFFFF")
    
    # Use relative ratios to calculate pixel coordinates (immune to DPI scaling differences)
    pos_x = int(screen_w * config.get("pos_x_ratio", 0.5))
    pos_y = int(screen_h * config.get("pos_y_ratio", 0.3))
    format_24h = config.get("format_24h", True)
    show_date = config.get("show_date", True)
    
    if not os.path.exists(wallpaper_path):
        return False
        
    # 1. Load wallpaper and crop to cover screen
    wp_raw = Image.open(wallpaper_path).convert("RGBA")
    wp_img = resize_to_fill(wp_raw, screen_w, screen_h)
    
    # 2. Draw text on a copy of the wallpaper
    bg_with_clock = wp_img.copy()
    draw = ImageDraw.Draw(bg_with_clock)
    
    # Load fonts
    try:
        font_path = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", f"{font_family.lower()}.ttf")
        if not os.path.exists(font_path):
            font_path = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "arialbd.ttf")
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()
        
    # Draw Date if enabled (placed dynamically relative to the time)
    if show_date:
        date_str = time.strftime(config.get("date_format", "%a, %b %d"))
        date_font_size = max(12, int(font_size * 0.3))
        try:
            # Re-use font family for date
            date_font_path = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", f"{font_family.lower()}.ttf")
            if not os.path.exists(date_font_path):
                date_font_path = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "arialbd.ttf")
            date_font = ImageFont.truetype(date_font_path, date_font_size)
        except:
            date_font = ImageFont.load_default()
            
        # Draw Date centered with Y offset from the main clock text (scale offset using ratio)
        date_y_offset = int(screen_h * config.get("date_y_offset_ratio", -0.074))
        draw.text((pos_x, pos_y + date_y_offset), date_str, font=date_font, fill=color, anchor="mm")
        
    # Draw Time
    time_format = "%H:%M" if format_24h else "%I:%M %p"
    time_str = time.strftime(time_format)
    if time_str.startswith("0") and not format_24h:
        time_str = time_str[1:] # strip leading zero for 12h format
        
    draw.text((pos_x, pos_y), time_str, font=font, fill=color, anchor="mm")
    
    # 3. Apply foreground mask on top
    if os.path.exists(depth_map_path):
        depth_raw = Image.open(depth_map_path).convert("L")
        depth_img = resize_to_fill(depth_raw, screen_w, screen_h)
        
        # Threshold depth to create foreground mask
        mask = depth_img.point(lambda p: 255 if p >= threshold else 0)
        if blur_radius > 0:
            mask = mask.filter(ImageFilter.GaussianBlur(blur_radius))
            
        final_image = bg_with_clock.copy()
        final_image.paste(wp_img, (0, 0), mask)
    else:
        final_image = bg_with_clock
        
    # Save as PNG
    final_image.convert("RGB").save(TEMP_WALLPAPER_PATH, "PNG")
    
    # Set as desktop background
    set_desktop_wallpaper(TEMP_WALLPAPER_PATH)
    return True

def main():
    print("Depth Clock Daemon started.")
    render_and_apply()
    
    last_minute = -1
    last_config_mtime = 0
    
    while True:
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

if __name__ == "__main__":
    main()
