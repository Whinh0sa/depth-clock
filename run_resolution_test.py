import sys
from unittest.mock import MagicMock

# Mock win32 modules
sys.modules['win32api'] = MagicMock()
sys.modules['win32gui'] = MagicMock()
sys.modules['win32con'] = MagicMock()
sys.modules['win32process'] = MagicMock()
sys.modules['pystray'] = MagicMock()

import win32api
metrics = {0: 1920, 1: 1080}
win32api.GetSystemMetrics.side_effect = lambda x: metrics.get(x, 0)

import wallpaper_daemon
wallpaper_daemon.set_desktop_wallpaper = MagicMock()
wallpaper_daemon.set_lockscreen_wallpaper = MagicMock()

# Initial run (should cache at 1920x1080)
print("Running at 1920x1080...")
wallpaper_daemon.render_and_apply()
print("Success.")

# Change resolution (simulating a screen change)
metrics[0] = 1280
metrics[1] = 720
print("Running at 1280x720...")
try:
    wallpaper_daemon.render_and_apply()
    print("Success. No crash!")
except Exception as e:
    print(f"Error: {e}")
