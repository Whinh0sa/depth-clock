import os
import sys
import time
import unittest.mock as mock

mock_win32api = mock.MagicMock()
mock_win32gui = mock.MagicMock()
mock_win32con = mock.MagicMock()
mock_win32process = mock.MagicMock()
mock_ctypes = mock.MagicMock()
mock_pystray = mock.MagicMock()

sys.modules['win32api'] = mock_win32api
sys.modules['win32gui'] = mock_win32gui
sys.modules['win32con'] = mock_win32con
sys.modules['win32process'] = mock_win32process
sys.modules['ctypes'] = mock_ctypes
sys.modules['pystray'] = mock_pystray

mock_win32api.GetSystemMetrics.side_effect = lambda x: 1920 if x == 0 else 1080

import wallpaper_daemon
from PIL import Image
import json
import numpy as np

# setup
os.makedirs(wallpaper_daemon.APP_DIR, exist_ok=True)
wp_path = os.path.join(wallpaper_daemon.APP_DIR, "test_wp.jpg")
depth_path = os.path.join(wallpaper_daemon.APP_DIR, "test_depth.png")
Image.new('RGB', (3840, 2160), color='red').save(wp_path)
Image.new('L', (3840, 2160), color=128).save(depth_path)

config = {
    "wallpaper_path": wp_path,
    "depth_map_path": depth_path,
    "threshold": 128,
    "blur_radius": 2,
    "transition_width": 10
}
with open(wallpaper_daemon.CONFIG_PATH, "w") as f:
    json.dump(config, f)

# benchmark
start = time.time()
for _ in range(5):
    wallpaper_daemon.render_and_apply()
end = time.time()

print(f"Baseline Elapsed time for 5 iterations: {end - start:.4f} seconds")
