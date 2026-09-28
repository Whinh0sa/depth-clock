import unittest
import tempfile
import os
import hashlib
import sys
from unittest.mock import patch, MagicMock

# Mock windows specific modules before importing gui
sys.modules['win32api'] = MagicMock()
sys.modules['win32con'] = MagicMock()
sys.modules['win32gui'] = MagicMock()
sys.modules['winreg'] = MagicMock()

from gui import get_file_hash

class TestGetFileHash(unittest.TestCase):
    def test_get_file_hash_valid_file(self):
        # Create a temporary file with known content
        known_content = b"test content for hash"
        expected_hash = hashlib.md5(known_content).hexdigest()

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(known_content)
            temp_filepath = temp_file.name

        try:
            # Calculate hash using the function
            result_hash = get_file_hash(temp_filepath)
            # Verify the hash matches the expected hash
            self.assertEqual(result_hash, expected_hash)
        finally:
            # Clean up the temporary file
            os.remove(temp_filepath)

    @patch('gui.time.time')
    def test_get_file_hash_invalid_file(self, mock_time):
        # Mock time.time() to return a specific value
        mock_time.return_value = 1672531200.0  # Some timestamp
        expected_fallback = str(int(1672531200.0))

        # Call with a non-existent file path
        result_hash = get_file_hash("non_existent_file.xyz")

        # Verify it falls back to the mocked timestamp string
        self.assertEqual(result_hash, expected_fallback)

if __name__ == '__main__':
    unittest.main()
