import os
from PIL import Image

# Curated high-impact, modern display and clock fonts natively available on Windows
WINDOWS_FONTS_MAP = {
    "Segoe UI": ["segoeui.ttf", "segoeuib.ttf"],
    "Impact": ["impact.ttf"],
    "Arial": ["arialbd.ttf", "arial.ttf"],
    "Georgia": ["georgiab.ttf", "georgia.ttf"],
    "Courier New": ["courbd.ttf", "cour.ttf"],
    "Consolas": ["consolab.ttf", "consola.ttf"],
    "Trebuchet MS": ["trebucbd.ttf", "trebuc.ttf"],
    "Verdana": ["verdanab.ttf", "verdana.ttf"],
    "Century Gothic": ["GOTHICB.TTF", "GOTHIC.TTF"],
    "Bahnschrift": ["bahnschrift.ttf"],
    "Franklin Gothic Medium": ["framd.ttf"],
    "Comic Sans MS": ["comicbd.ttf", "comic.ttf"],
    "Calibri": ["calibrib.ttf", "calibri.ttf"],
    "Cambria": ["cambriab.ttf", "cambria.ttc"],
    "Palatino Linotype": ["palab.ttf", "pala.ttf"],
    "Corbel": ["corbelb.ttf", "corbel.ttf"],
    "Candara": ["Candarab.ttf", "Candara.ttf"],
    "Lucida Console": ["lucon.ttf"],
    "Tahoma": ["tahomabd.ttf", "tahoma.ttf"],
    "Times New Roman": ["timesbd.ttf", "times.ttf"]
}

def get_available_fonts():
    """
    Returns list of curated font family names physically installed on Windows,
    with Segoe UI always verified first as default.
    """
    windir = os.environ.get("WINDIR", "C:\\Windows")
    fonts_dir = os.path.join(windir, "Fonts")
    
    available = []
    for family, files in WINDOWS_FONTS_MAP.items():
        for filename in files:
            if os.path.exists(os.path.join(fonts_dir, filename)):
                available.append(family)
                break
                
    if not available:
        available = ["Segoe UI", "Arial", "Impact"]
    return available

def resolve_font_path(font_family):
    """
    Directly and reliably maps a font family name to its physical TTF/TTC file
    in %WINDIR%\\Fonts for Pillow ImageFont.truetype rendering.
    """
    windir = os.environ.get("WINDIR", "C:\\Windows")
    fonts_dir = os.path.join(windir, "Fonts")
    
    # 1. Lookup in curated map
    if font_family in WINDOWS_FONTS_MAP:
        for filename in WINDOWS_FONTS_MAP[font_family]:
            p = os.path.join(fonts_dir, filename)
            if os.path.exists(p):
                return p
                
    # 2. Case-insensitive / whitespace-stripped search
    clean = font_family.lower().replace(" ", "")
    candidates = [
        f"{font_family.lower()}.ttf",
        f"{clean}.ttf",
        f"{clean}b.ttf",
        f"{clean}bd.ttf",
        "segoeuib.ttf",
        "segoeui.ttf",
        "arialbd.ttf",
        "arial.ttf"
    ]
    for c in candidates:
        p = os.path.join(fonts_dir, c)
        if os.path.exists(p):
            return p

    # Fallback default
    for fallback in ["segoeui.ttf", "arial.ttf"]:
        p = os.path.join(fonts_dir, fallback)
        if os.path.exists(p):
            return p
    return None

def auto_optimize_depth_clock(wallpaper_img, depth_map_img, screen_w=1920, screen_h=1080):
    """
    Intelligent iOS-style depth clock layout and styling optimizer.
    Uses pure Pillow operations without external C dependencies.
    
    Analyzes wallpaper composition and depth mask to automatically determine:
    1. Optimal foreground threshold for clean edges and natural overlap.
    2. Optimal (X, Y) clock position so the clock sits behind the subject with ~10-25% subtle overlap.
    3. WCAG contrast-calculated text color (White vs Dark Charcoal) based on visible background luminance.
    4. Proportional font size.
    
    Returns a dict with: threshold, pos_x_ratio, pos_y_ratio, color, font_size, blur_radius, transition_width
    """
    # Downscale for high-speed sampling (e.g. 96x54)
    dw, dh = 96, 54
    wp_small = wallpaper_img.convert("RGB").resize((dw, dh), Image.Resampling.BILINEAR)
    dp_small = depth_map_img.convert("L").resize((dw, dh), Image.Resampling.BILINEAR)
    
    if hasattr(dp_small, "get_flattened_data"):
        dp_pixels = list(dp_small.get_flattened_data())
    else:
        dp_pixels = list(dp_small.getdata())
        
    if hasattr(wp_small, "get_flattened_data"):
        wp_pixels = list(wp_small.get_flattened_data())
    else:
        wp_pixels = list(wp_small.getdata())
    
    # --- 1. Compute Optimal Foreground Threshold ---
    non_zero = sorted([p for p in dp_pixels if p > 25])
    if len(non_zero) > 0:
        # Use 35th percentile of foreground depth to create clean, prominent depth layers
        idx = int(len(non_zero) * 0.35)
        thresh = non_zero[idx]
        threshold = max(35, min(210, thresh))
    else:
        threshold = 128
        
    # --- 2. Evaluate Candidate Clock Positions for Ideal Overlap ---
    # Clock width ~ 44%, height ~ 20%
    cw = int(0.44 * dw)
    ch = int(0.20 * dh)
    
    best_score = -999999.0
    best_x = 0.5
    best_y = 0.28
    
    # Test candidate coordinates
    x_steps = [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]
    y_steps = [0.18, 0.22, 0.26, 0.30, 0.34, 0.38, 0.42, 0.46, 0.50]
    
    for rx in x_steps:
        for ry in y_steps:
            cx = int(rx * dw)
            cy = int(ry * dh)
            
            x0 = max(0, cx - cw // 2)
            x1 = min(dw, cx + cw // 2)
            y0 = max(0, cy - ch // 2)
            y1 = min(dh, cy + ch // 2)
            
            total_clock_pixels = (x1 - x0) * (y1 - y0)
            if total_clock_pixels <= 0:
                continue
                
            fg_count = 0
            for py in range(y0, y1):
                row_offset = py * dw
                for px in range(x0, x1):
                    if dp_pixels[row_offset + px] >= threshold:
                        fg_count += 1
                        
            overlap_ratio = fg_count / total_clock_pixels
            
            # Score: Ideal overlap is 12% to 25% (tucked behind subject, perfectly readable)
            if 0.05 <= overlap_ratio <= 0.35:
                overlap_score = 100.0 - abs(overlap_ratio - 0.18) * 250.0
            elif overlap_ratio < 0.05:
                # Rewards getting closer to subject boundary rather than floating in empty sky
                overlap_score = overlap_ratio * 400.0
            else:
                # Too much overlap penalizes heavily (clock obscured)
                overlap_score = max(0.0, 100.0 - (overlap_ratio - 0.35) * 500.0)
                
            # Composition preferences:
            center_penalty = abs(rx - 0.5) * 45.0  # slight preference for horizontal center
            top_bias = (0.50 - ry) * 35.0          # preference for upper portion of screen
            
            total_score = overlap_score - center_penalty + top_bias
            if total_score > best_score:
                best_score = total_score
                best_x = rx
                best_y = ry
                
    # --- 3. Compute High-Contrast Color via Relative Luminance ---
    cx = int(best_x * dw)
    cy = int(best_y * dh)
    x0 = max(0, cx - cw // 2)
    x1 = min(dw, cx + cw // 2)
    y0 = max(0, cy - ch // 2)
    y1 = min(dh, cy + ch // 2)
    
    total_r, total_g, total_b, sample_count = 0, 0, 0, 0
    for py in range(y0, y1):
        row_offset = py * dw
        for px in range(x0, x1):
            # Only sample visible background area (not covered by foreground mask)
            if dp_pixels[row_offset + px] < threshold:
                r, g, b = wp_pixels[row_offset + px]
                total_r += r
                total_g += g
                total_b += b
                sample_count += 1
                
    if sample_count == 0:
        # Fallback to entire clock region
        for py in range(y0, y1):
            row_offset = py * dw
            for px in range(x0, x1):
                r, g, b = wp_pixels[row_offset + px]
                total_r += r
                total_g += g
                total_b += b
                sample_count += 1
                
    avg_r = (total_r / max(1, sample_count)) / 255.0
    avg_g = (total_g / max(1, sample_count)) / 255.0
    avg_b = (total_b / max(1, sample_count)) / 255.0
    
    def to_linear(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        
    bg_lum = 0.2126 * to_linear(avg_r) + 0.7152 * to_linear(avg_g) + 0.0722 * to_linear(avg_b)
    
    # Contrast ratio against white (1.0) vs dark charcoal (0.015)
    cr_white = (1.0 + 0.05) / (bg_lum + 0.05)
    cr_dark = (bg_lum + 0.05) / (0.015 + 0.05)
    
    best_color = "#FFFFFF" if cr_white >= cr_dark else "#111827"
    font_size = max(80, min(240, int(screen_h * 0.13)))
    
    return {
        "threshold": threshold,
        "pos_x_ratio": round(best_x, 3),
        "pos_y_ratio": round(best_y, 3),
        "color": best_color,
        "font_size": font_size,
        "blur_radius": 2,
        "transition_width": 10
    }
