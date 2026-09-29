import sys
from unittest.mock import MagicMock

# Mock heavy/OS-specific dependencies for lightweight testing
sys.modules['numpy'] = MagicMock()
sys.modules['tkinter'] = MagicMock()
sys.modules['customtkinter'] = MagicMock()
sys.modules['win32api'] = MagicMock()
sys.modules['win32con'] = MagicMock()
sys.modules['ctypes'] = MagicMock()
sys.modules['winreg'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['depth_engine'] = MagicMock()

import unittest
import os
import tempfile
import time
import hashlib
from unittest.mock import patch

from gui import get_file_hash

class TestGetFileHash(unittest.TestCase):
    def test_get_file_hash_valid_file(self):
        # Create a temporary file with known content
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test data")
            filepath = f.name

        try:
            # Expected MD5 hash for "test data"
            expected_hash = hashlib.md5(b"test data").hexdigest()
            result = get_file_hash(filepath)
            self.assertEqual(result, expected_hash)
        finally:
            os.remove(filepath)

    def test_get_file_hash_invalid_file(self):
        # Test fallback to time

        # Patch time.time to return a fixed value
        fixed_time = 1234567890.123
        with patch('time.time', return_value=fixed_time):
            result = get_file_hash("non_existent_file_path_12345.xyz")
            self.assertEqual(result, str(int(fixed_time)))

    def test_get_file_hash_fallback_is_numeric_string(self):
        # Additional test without mocking time to verify it returns a numeric string
        result = get_file_hash("another_non_existent_file.xyz")
        self.assertTrue(result.isdigit(), "Fallback hash should be a numeric string")
        # Ensure it's a recent timestamp
        self.assertTrue(abs(int(result) - int(time.time())) < 10)

if __name__ == '__main__':
    unittest.main()
