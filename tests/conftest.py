import sys
import unittest.mock as mock

# Mock Windows-specific modules for tests running on Linux CI
sys.modules['win32api'] = mock.MagicMock()
sys.modules['win32con'] = mock.MagicMock()
sys.modules['winreg'] = mock.MagicMock()
sys.modules['win32gui'] = mock.MagicMock()
