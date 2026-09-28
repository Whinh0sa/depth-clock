import unittest
import sys
from unittest.mock import MagicMock
import tempfile
import os
import time

# Mock required modules before importing gui
sys.modules['win32api'] = MagicMock()
sys.modules['win32con'] = MagicMock()
sys.modules['win32gui'] = MagicMock()
sys.modules['ctypes'] = MagicMock()
sys.modules['ctypes.wintypes'] = MagicMock()
sys.modules['winreg'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['PIL.ImageTk'] = MagicMock()
sys.modules['PIL.ImageFilter'] = MagicMock()
sys.modules['PIL.ImageDraw'] = MagicMock()
sys.modules['PIL.ImageFont'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['customtkinter'] = MagicMock()
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()

# Now import gui
import gui
import hashlib

class TestGui(unittest.TestCase):
    def test_get_file_hash_valid(self):
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"hello world")
            tmp_path = tmp.name

        try:
            expected_hash = hashlib.md5(b"hello world").hexdigest()
            result = gui.get_file_hash(tmp_path)
            self.assertEqual(result, expected_hash)
        finally:
            os.unlink(tmp_path)

    def test_get_file_hash_invalid(self):
        # Pass a non-existent filepath
        non_existent_path = "this_file_does_not_exist_12345.txt"

        result = gui.get_file_hash(non_existent_path)

        # Check if the result is a numeric string (timestamp)
        self.assertTrue(result.isdigit(), "Result should be a numeric string representing a timestamp")

        # Further verify it's a valid timestamp (should be around current time)
        current_time = int(time.time())
        result_time = int(result)

        # Result should be very close to current time (within a few seconds)
        self.assertTrue(abs(current_time - result_time) < 5)

if __name__ == '__main__':
    unittest.main()
