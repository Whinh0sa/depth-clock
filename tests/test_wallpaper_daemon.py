import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock dependencies that are not needed for testing set_desktop_wallpaper
# and which might cause issues in non-Windows environments
sys.modules['win32api'] = MagicMock()
sys.modules['win32gui'] = MagicMock()
sys.modules['win32con'] = MagicMock()
sys.modules['win32process'] = MagicMock()
sys.modules['pystray'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['numpy'] = MagicMock()

import wallpaper_daemon

class TestWallpaperDaemon(unittest.TestCase):
    @patch('wallpaper_daemon.ctypes')
    def test_set_desktop_wallpaper_happy_path(self, mock_ctypes):
        """Test that set_desktop_wallpaper calls SystemParametersInfoW with correct arguments."""
        test_image_path = "/path/to/test_image.png"
        wallpaper_daemon.set_desktop_wallpaper(test_image_path)

        # SPI_SETDESKWALLPAPER = 20
        # SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE = 3
        mock_ctypes.windll.user32.SystemParametersInfoW.assert_called_once_with(20, 0, test_image_path, 3)

    @patch('wallpaper_daemon.ctypes')
    def test_set_desktop_wallpaper_empty_path(self, mock_ctypes):
        """Test with an empty path."""
        test_image_path = ""
        wallpaper_daemon.set_desktop_wallpaper(test_image_path)

        mock_ctypes.windll.user32.SystemParametersInfoW.assert_called_once_with(20, 0, test_image_path, 3)

    @patch('wallpaper_daemon.ctypes')
    def test_set_desktop_wallpaper_none_path(self, mock_ctypes):
        """Test with None as path."""
        test_image_path = None
        wallpaper_daemon.set_desktop_wallpaper(test_image_path)

        mock_ctypes.windll.user32.SystemParametersInfoW.assert_called_once_with(20, 0, test_image_path, 3)

if __name__ == '__main__':
    unittest.main()
