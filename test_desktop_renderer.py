import sys
import pytest
from unittest.mock import MagicMock, patch

# Mock windows-specific and UI modules
sys.modules['win32gui'] = MagicMock()
sys.modules['win32con'] = MagicMock()
sys.modules['win32api'] = MagicMock()
sys.modules['win32process'] = MagicMock()
sys.modules['ctypes'] = MagicMock()
sys.modules['tkinter'] = MagicMock()

import desktop_renderer
import win32gui
import win32con

class TestGetDesktopWorkerW:
    @patch('desktop_renderer.win32gui')
    def test_get_desktop_worker_w_happy_path(self, mock_win32gui):
        # Setup mocks
        mock_progman_hwnd = 1234
        mock_shell_worker_hwnd = 5678
        mock_worker_w_hwnd = 9012

        mock_win32gui.FindWindow.return_value = mock_progman_hwnd

        def mock_find_window_ex(parent, child_after, class_name, window_name):
            if class_name == "SHELLDLL_DefView" and parent == mock_shell_worker_hwnd:
                return 42 # Valid handle
            if class_name == "WorkerW" and child_after == mock_shell_worker_hwnd:
                return mock_worker_w_hwnd
            return 0

        mock_win32gui.FindWindowEx.side_effect = mock_find_window_ex

        def mock_enum_windows_with_side_effect(callback, extra):
            mock_win32gui.GetClassName.return_value = "WorkerW"
            callback(mock_shell_worker_hwnd, extra)

        mock_win32gui.EnumWindows = mock_enum_windows_with_side_effect

        # Call the function
        result = desktop_renderer.get_desktop_worker_w()

        # Verify
        mock_win32gui.FindWindow.assert_called_with("Progman", None)
        mock_win32gui.SendMessageTimeout.assert_called_once()
        assert result == mock_worker_w_hwnd

    @patch('desktop_renderer.win32gui')
    def test_get_desktop_worker_w_fallback_no_worker_w(self, mock_win32gui):
        # Setup mocks
        mock_progman_hwnd = 1234
        mock_shell_worker_hwnd = 5678

        mock_win32gui.FindWindow.return_value = mock_progman_hwnd

        def mock_find_window_ex(parent, child_after, class_name, window_name):
            if class_name == "SHELLDLL_DefView" and parent == mock_shell_worker_hwnd:
                return 42 # Valid handle
            if class_name == "WorkerW" and child_after == mock_shell_worker_hwnd:
                return 0 # Sibling not found
            return 0

        mock_win32gui.FindWindowEx.side_effect = mock_find_window_ex

        def mock_enum_windows_with_side_effect(callback, extra):
            mock_win32gui.GetClassName.return_value = "WorkerW"
            callback(mock_shell_worker_hwnd, extra)

        mock_win32gui.EnumWindows = mock_enum_windows_with_side_effect

        # Call the function
        result = desktop_renderer.get_desktop_worker_w()

        # Verify fallback to progman
        assert result == mock_progman_hwnd

    @patch('desktop_renderer.win32gui')
    def test_get_desktop_worker_w_fallback_no_shell_worker(self, mock_win32gui):
        # Setup mocks
        mock_progman_hwnd = 1234
        mock_win32gui.FindWindow.return_value = mock_progman_hwnd

        # EnumWindows does not find any matching shell_worker
        def mock_enum_windows_empty(callback, extra):
            pass # simulate no windows matched

        mock_win32gui.EnumWindows = mock_enum_windows_empty

        # Call the function
        result = desktop_renderer.get_desktop_worker_w()

        # Verify fallback to progman
        assert result == mock_progman_hwnd
