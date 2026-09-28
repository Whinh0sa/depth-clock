import sys
from unittest.mock import MagicMock

# Mock heavy dependencies before importing gui
sys.modules['win32api'] = MagicMock()
sys.modules['win32con'] = MagicMock()
sys.modules['winreg'] = MagicMock()
sys.modules['win32gui'] = MagicMock()
sys.modules['win32process'] = MagicMock()
sys.modules['pystray'] = MagicMock()
sys.modules['ctypes'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['onnxruntime'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['customtkinter'] = MagicMock()
sys.modules['tkinter'] = MagicMock()
sys.modules['depth_engine'] = MagicMock()

# Now we can safely import gui
import unittest
import os
import hashlib
import tempfile
from unittest.mock import patch

from gui import get_file_hash

class TestGetFileHash(unittest.TestCase):

    def test_get_file_hash_valid_file(self):
        # Create a temporary file
        content = b"test content"
        expected_hash = hashlib.md5(content).hexdigest()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(content)
            temp_filepath = f.name

        try:
            result = get_file_hash(temp_filepath)
            self.assertEqual(result, expected_hash)
        finally:
            os.remove(temp_filepath)

    @patch('gui.time.time')
    def test_get_file_hash_fallback(self, mock_time):
        mock_time.return_value = 1630000000.123

        # Pass a non-existent filepath
        result = get_file_hash("non_existent_file.txt")

        # Should return the int representation of the timestamp
        self.assertEqual(result, "1630000000")
        self.assertTrue(result.isdigit())

if __name__ == '__main__':
    unittest.main()
