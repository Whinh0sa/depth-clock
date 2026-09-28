import unittest
import os
import hashlib
from unittest.mock import patch
import depth_engine

class TestDepthEngineHash(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.getcwd(), "test_downloads")
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)

        self.test_file_path = os.path.join(self.test_dir, "dummy_model.onnx")

        # Create a dummy file and calculate its hash
        self.dummy_data = b"This is a dummy model file for testing hash verification."

        with open(self.test_file_path, "wb") as f:
            f.write(self.dummy_data)

        self.dummy_hash = hashlib.sha256(self.dummy_data).hexdigest()
        self.incorrect_hash = "0" * 64

    def tearDown(self):
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    @patch('urllib.request.urlretrieve')
    def test_successful_download_with_correct_hash(self, mock_urlretrieve):
        # Mock urlretrieve to do nothing since the file is already created in setUp
        mock_urlretrieve.return_value = None

        result = depth_engine.download_model_file(
            url="http://example.com/dummy",
            target_path=self.test_file_path,
            name="Dummy Model",
            expected_hash=self.dummy_hash
        )

        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.test_file_path))

    @patch('urllib.request.urlretrieve')
    def test_failed_download_with_incorrect_hash(self, mock_urlretrieve):
        # Mock urlretrieve to do nothing since the file is already created in setUp
        mock_urlretrieve.return_value = None

        # Suppress stdout to keep test output clean
        with patch('sys.stdout'):
            result = depth_engine.download_model_file(
                url="http://example.com/dummy",
                target_path=self.test_file_path,
                name="Dummy Model",
                expected_hash=self.incorrect_hash
            )

        self.assertFalse(result)
        # Verify the file was removed
        self.assertFalse(os.path.exists(self.test_file_path))

if __name__ == '__main__':
    unittest.main()
