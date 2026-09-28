import sys
import unittest.mock

# Mock out Windows-specific modules on non-Windows platforms
sys.modules['win32api'] = unittest.mock.MagicMock()
sys.modules['win32con'] = unittest.mock.MagicMock()
sys.modules['winreg'] = unittest.mock.MagicMock()
