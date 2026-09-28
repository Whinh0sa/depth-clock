import os
import pytest
from unittest.mock import patch, MagicMock

# Import the module to be tested
import depth_engine

def test_download_model_file_error_cleanup(tmp_path):
    # Set up a temporary target path
    target_path = os.path.join(tmp_path, "test_model.onnx")

    # We want to mock urlretrieve to simulate failure halfway through a download.
    # To do this, we create a file at the target_path and then raise an exception.
    def mock_urlretrieve(url, filename, reporthook=None):
        with open(filename, 'w') as f:
            f.write("partial data")
        raise Exception("Mocked download error")

    with patch('urllib.request.urlretrieve', side_effect=mock_urlretrieve):
        # We don't want tests trying to mess with actual user directories,
        # so let's mock ensure_app_dir just in case it's doing something we don't want,
        # though it shouldn't matter since we pass our own target path.
        # But we do need to avoid hitting actual internet for other requests.
        # We also redirect stdout to avoid polluting test output.
        result = depth_engine.download_model_file("http://fake.url", target_path, "Test Model")

        # Function should return False upon failure
        assert result is False

        # The partial file should have been cleaned up
        assert not os.path.exists(target_path)
