import sys
import unittest.mock

# Mock Windows-specific APIs for Linux CI testing
sys.modules['win32api'] = unittest.mock.MagicMock()
sys.modules['win32con'] = unittest.mock.MagicMock()
sys.modules['winreg'] = unittest.mock.MagicMock()
sys.modules['win32gui'] = unittest.mock.MagicMock()
sys.modules['win32process'] = unittest.mock.MagicMock()
sys.modules['pywin32'] = unittest.mock.MagicMock()

# Mock heavy dependencies if needed
