import unittest
import os
import sys
from unittest.mock import MagicMock

# Mocking all dependencies as required by instructions for cross-platform/CI testing
sys.modules['numpy'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['onnxruntime'] = MagicMock()
sys.modules['win32api'] = MagicMock()
sys.modules['win32con'] = MagicMock()
sys.modules['winreg'] = MagicMock()
sys.modules['win32gui'] = MagicMock()
sys.modules['win32process'] = MagicMock()
sys.modules['pystray'] = MagicMock()
sys.modules['ctypes'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['PIL.ImageTk'] = MagicMock()
sys.modules['PIL.ImageFilter'] = MagicMock()
sys.modules['PIL.ImageDraw'] = MagicMock()
sys.modules['PIL.ImageFont'] = MagicMock()
sys.modules['customtkinter'] = MagicMock()
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()

class MockDepthEngine:
    APP_DIR = "mock_app_dir"
    MODEL_PATH = "mock_model_path"
    DepthEngine = MagicMock()
    download_model = MagicMock()

sys.modules['depth_engine'] = MockDepthEngine

import gui
import tempfile
import hashlib
import time

class TestGUI(unittest.TestCase):
    def test_get_file_hash_success(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test data")
            filepath = f.name

        try:
            expected_hash = hashlib.md5(b"test data").hexdigest()
            self.assertEqual(gui.get_file_hash(filepath), expected_hash)
        finally:
            os.remove(filepath)

    def test_get_file_hash_fallback(self):
        result = gui.get_file_hash("non_existent_file_path_12345.xyz")
        self.assertTrue(result.isdigit())

if __name__ == '__main__':
    unittest.main()
