import unittest
from unittest.mock import patch, MagicMock
from depth_engine import download_model_file

class TestDepthEngineDownload(unittest.TestCase):

    @patch('depth_engine.ensure_app_dir')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('urllib.request.urlretrieve')
    def test_download_model_file_already_exists(self, mock_urlretrieve, mock_getsize, mock_exists, mock_ensure_app_dir):
        # Setup mocks
        mock_exists.return_value = True
        mock_getsize.return_value = 2 * 1024 * 1024 # 2MB, larger than 1MB

        # Call function
        result = download_model_file("http://example.com/model", "/path/to/model", "TestModel")

        # Verify
        mock_ensure_app_dir.assert_called_once()
        mock_exists.assert_called_once_with("/path/to/model")
        mock_getsize.assert_called_once_with("/path/to/model")
        mock_urlretrieve.assert_not_called()
        self.assertTrue(result)

    @patch('depth_engine.ensure_app_dir')
    @patch('os.path.exists')
    @patch('urllib.request.urlretrieve')
    def test_download_model_file_success(self, mock_urlretrieve, mock_exists, mock_ensure_app_dir):
        # Setup mocks
        # First exists check is False, meaning we need to download
        mock_exists.return_value = False

        # Call function
        result = download_model_file("http://example.com/model", "/path/to/model", "TestModel")

        # Verify
        mock_ensure_app_dir.assert_called_once()
        mock_exists.assert_called_once_with("/path/to/model")
        mock_urlretrieve.assert_called_once()
        self.assertEqual(mock_urlretrieve.call_args[0][0], "http://example.com/model")
        self.assertEqual(mock_urlretrieve.call_args[0][1], "/path/to/model")
        self.assertTrue('reporthook' in mock_urlretrieve.call_args[1])
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
