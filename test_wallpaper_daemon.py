import unittest
from unittest.mock import patch, MagicMock
import sys

sys.modules['win32api'] = MagicMock()
sys.modules['win32gui'] = MagicMock()
sys.modules['win32con'] = MagicMock()
sys.modules['win32process'] = MagicMock()
sys.modules['pystray'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['PIL.ImageDraw'] = MagicMock()
sys.modules['PIL.ImageFont'] = MagicMock()
sys.modules['PIL.ImageFilter'] = MagicMock()

import wallpaper_daemon

class TestWallpaperDaemon(unittest.TestCase):
    @patch('wallpaper_daemon.subprocess.run')
    @patch('builtins.print')
    def test_set_lockscreen_wallpaper_subprocess_error(self, mock_print, mock_run):
        # Setup the mock to raise an exception
        mock_run.side_effect = Exception("Mocked Subprocess Error")

        # Call the function
        wallpaper_daemon.set_lockscreen_wallpaper("dummy/path/image.jpg")

        # Verify the exception was caught and printed
        mock_print.assert_called_with("Failed to sync lockscreen wallpaper:", mock_run.side_effect)

if __name__ == '__main__':
    unittest.main()
