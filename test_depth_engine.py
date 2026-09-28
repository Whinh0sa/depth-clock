import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Mock heavy data science dependencies prior to importing target application modules
sys.modules['numpy'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['onnxruntime'] = MagicMock()

import depth_engine

class TestDepthEngine(unittest.TestCase):

    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_ensure_app_dir_exists(self, mock_makedirs, mock_exists):
        # Setup: simulate directory already exists
        mock_exists.return_value = True

        # Action
        depth_engine.ensure_app_dir()

        # Assert
        mock_exists.assert_called_once_with(depth_engine.APP_DIR)
        mock_makedirs.assert_not_called()

    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_ensure_app_dir_not_exists(self, mock_makedirs, mock_exists):
        # Setup: simulate directory does not exist
        mock_exists.return_value = False

        # Action
        depth_engine.ensure_app_dir()

        # Assert
        mock_exists.assert_called_once_with(depth_engine.APP_DIR)
        mock_makedirs.assert_called_once_with(depth_engine.APP_DIR)

if __name__ == '__main__':
    unittest.main()
