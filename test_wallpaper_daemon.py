import os
import unittest
from unittest.mock import patch

# Mock out windows-specific modules before importing wallpaper_daemon
import sys
from unittest.mock import MagicMock
sys.modules['win32api'] = MagicMock()
sys.modules['win32gui'] = MagicMock()
sys.modules['win32con'] = MagicMock()
sys.modules['win32process'] = MagicMock()
sys.modules['pystray'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['ctypes'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['PIL.ImageDraw'] = MagicMock()
sys.modules['PIL.ImageFont'] = MagicMock()
sys.modules['PIL.ImageFilter'] = MagicMock()
sys.modules['depth_engine'] = MagicMock()

import wallpaper_daemon

import base64

class TestWallpaperDaemon(unittest.TestCase):
    @patch('wallpaper_daemon.subprocess.run')
    def test_set_lockscreen_wallpaper_secure_arguments(self, mock_run):
        # The malicious path simulating command injection attempt, and spaces
        test_path = "C:\\dummy path\\with spaces\\'; Write-Host 'Injected'; #"

        wallpaper_daemon.set_lockscreen_wallpaper(test_path)

        # Verify subprocess.run was called once
        mock_run.assert_called_once()

        # Get the actual arguments passed to subprocess.run
        args, kwargs = mock_run.call_args
        cmd_list = args[0]

        # Verify that it uses a list for arguments to subprocess.run
        self.assertIsInstance(cmd_list, list)

        # Verify PowerShell is called with -EncodedCommand
        self.assertIn('powershell', cmd_list)
        self.assertIn('-EncodedCommand', cmd_list)

        command_idx = cmd_list.index('-EncodedCommand')
        encoded_script = cmd_list[command_idx + 1]

        # Decode the script block
        decoded_script = base64.b64decode(encoded_script).decode('utf-16le')

        # Ensure the absolute path was used
        expected_abs_path = os.path.abspath(test_path)

        # The single quote should be escaped in PowerShell by doubling it
        expected_safe_path = expected_abs_path.replace("'", "''")

        self.assertIn(f"GetFileFromPathAsync('{expected_safe_path}')", decoded_script)

if __name__ == '__main__':
    unittest.main()
