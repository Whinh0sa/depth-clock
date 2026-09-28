import sys
from unittest.mock import MagicMock

# Mock win32 modules
sys.modules['win32api'] = MagicMock()
sys.modules['win32gui'] = MagicMock()
sys.modules['win32con'] = MagicMock()
sys.modules['win32process'] = MagicMock()
sys.modules['pystray'] = MagicMock()

import pytest
sys.exit(pytest.main(["."]))
