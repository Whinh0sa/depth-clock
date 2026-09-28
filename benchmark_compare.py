import time
import sys
from unittest.mock import MagicMock

# Mock win32 modules
sys.modules['win32api'] = MagicMock()
sys.modules['win32gui'] = MagicMock()
sys.modules['win32con'] = MagicMock()
sys.modules['win32process'] = MagicMock()
sys.modules['pystray'] = MagicMock()

import win32api
win32api.GetSystemMetrics.side_effect = lambda x: 1920 if x == 0 else 1080

import os
import json
import numpy as np
from PIL import Image

# Create dummy wallpaper and depth map
APP_DIR = os.path.join(os.path.expanduser("~"), ".depthclock")
os.makedirs(APP_DIR, exist_ok=True)

wp_path = os.path.join(APP_DIR, "bench_wp.png")
depth_path = os.path.join(APP_DIR, "bench_depth.png")
config_path = os.path.join(APP_DIR, "config.json")

# Create large random images to simulate real workload
# Let's not recreate them if they exist to speed up the benchmark start
if not os.path.exists(wp_path):
    Image.fromarray(np.random.randint(0, 255, (2160, 3840, 3), dtype=np.uint8)).save(wp_path)
if not os.path.exists(depth_path):
    Image.fromarray(np.random.randint(0, 255, (2160, 3840), dtype=np.uint8)).save(depth_path)

config = {
    "wallpaper_path": wp_path,
    "depth_map_path": depth_path,
    "threshold": 128,
    "blur_radius": 2,
    "transition_width": 10,
    "font_family": "Segoe UI",
    "font_size": 120,
    "color": "#FFFFFF",
    "format_24h": True,
    "show_date": True,
    "sync_lockscreen": False
}
with open(config_path, "w") as f:
    json.dump(config, f)

# Patch set_desktop_wallpaper so we don't actually change anything
import wallpaper_daemon
wallpaper_daemon.CONFIG_PATH = config_path
wallpaper_daemon.set_desktop_wallpaper = MagicMock()
wallpaper_daemon.set_lockscreen_wallpaper = MagicMock()

# We expect the first run to be slow (cache miss), and subsequent runs to be fast (cache hit)
times = []
for i in range(10):
    start = time.time()
    wallpaper_daemon.render_and_apply()
    end = time.time()
    times.append(end - start)

print("First run (cache miss): {:.4f}s".format(times[0]))
avg_subsequent = sum(times[1:]) / len(times[1:])
print("Average subsequent runs (cache hit): {:.4f}s".format(avg_subsequent))
print("Performance Improvement (Subsequent vs First): {:.2f}x faster".format(times[0] / avg_subsequent))
