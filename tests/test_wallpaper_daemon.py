import sys
import unittest
from unittest.mock import MagicMock
from PIL import Image

# Mock dependencies before importing the module
sys.modules['win32api'] = MagicMock()
sys.modules['win32gui'] = MagicMock()
sys.modules['win32con'] = MagicMock()
sys.modules['win32process'] = MagicMock()
sys.modules['pystray'] = MagicMock()
sys.modules['ctypes'] = MagicMock()
sys.modules['ctypes.windll'] = MagicMock()
sys.modules['ctypes.windll.shcore'] = MagicMock()
sys.modules['ctypes.windll.user32'] = MagicMock()

import wallpaper_daemon

class TestWallpaperDaemon(unittest.TestCase):
    def test_resize_wider_than_target(self):
        # Image is 800x400 (aspect 2.0)
        # Target is 400x400 (aspect 1.0)
        # It should resize to height=400, width=800, then crop the middle 400x400
        img = Image.new("RGBA", (800, 400), color="blue")
        target_w, target_h = 400, 400
        result = wallpaper_daemon.resize_to_fill(img, target_w, target_h)
        self.assertEqual(result.size, (target_w, target_h))

    def test_resize_taller_than_target(self):
        # Image is 400x800 (aspect 0.5)
        # Target is 400x400 (aspect 1.0)
        # It should resize to width=400, height=800, then crop the middle 400x400
        img = Image.new("RGBA", (400, 800), color="red")
        target_w, target_h = 400, 400
        result = wallpaper_daemon.resize_to_fill(img, target_w, target_h)
        self.assertEqual(result.size, (target_w, target_h))

    def test_resize_same_aspect_ratio(self):
        # Image is 800x800 (aspect 1.0)
        # Target is 400x400 (aspect 1.0)
        # It should resize to 400x400 exactly
        img = Image.new("RGBA", (800, 800), color="green")
        target_w, target_h = 400, 400
        result = wallpaper_daemon.resize_to_fill(img, target_w, target_h)
        self.assertEqual(result.size, (target_w, target_h))

if __name__ == "__main__":
    unittest.main()
