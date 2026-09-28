import sys
from unittest.mock import MagicMock

# Mock windows specific modules before importing the module under test
sys.modules['win32api'] = MagicMock()
sys.modules['win32gui'] = MagicMock()
sys.modules['win32con'] = MagicMock()
sys.modules['win32process'] = MagicMock()
sys.modules['pystray'] = MagicMock()
import wallpaper_daemon
import pytest

def test_is_fullscreen_app_active_no_hwnd(monkeypatch):
    monkeypatch.setattr(wallpaper_daemon.win32gui, 'GetForegroundWindow', lambda: 0)
    assert wallpaper_daemon.is_fullscreen_app_active(1920, 1080) == False

def test_is_fullscreen_app_active_desktop_class(monkeypatch):
    monkeypatch.setattr(wallpaper_daemon.win32gui, 'GetForegroundWindow', lambda: 123)
    # Test all ignored classes
    for class_name in ["WorkerW", "Progman", "Shell_TrayWnd", "DV2ControlHost"]:
        monkeypatch.setattr(wallpaper_daemon.win32gui, 'GetClassName', lambda hwnd, cls_name=class_name: cls_name)
        assert wallpaper_daemon.is_fullscreen_app_active(1920, 1080) == False

def test_is_fullscreen_app_active_smaller_window(monkeypatch):
    monkeypatch.setattr(wallpaper_daemon.win32gui, 'GetForegroundWindow', lambda: 123)
    monkeypatch.setattr(wallpaper_daemon.win32gui, 'GetClassName', lambda hwnd: "SomeApp")

    # rect is (left, top, right, bottom)
    # width = right - left = 800 - 0 = 800
    # height = bottom - top = 600 - 0 = 600
    monkeypatch.setattr(wallpaper_daemon.win32gui, 'GetWindowRect', lambda hwnd: (0, 0, 800, 600))

    assert wallpaper_daemon.is_fullscreen_app_active(1920, 1080) == False

def test_is_fullscreen_app_active_equal_window(monkeypatch):
    monkeypatch.setattr(wallpaper_daemon.win32gui, 'GetForegroundWindow', lambda: 123)
    monkeypatch.setattr(wallpaper_daemon.win32gui, 'GetClassName', lambda hwnd: "SomeApp")

    # rect is (left, top, right, bottom)
    monkeypatch.setattr(wallpaper_daemon.win32gui, 'GetWindowRect', lambda hwnd: (0, 0, 1920, 1080))

    assert wallpaper_daemon.is_fullscreen_app_active(1920, 1080) == True

def test_is_fullscreen_app_active_larger_window(monkeypatch):
    monkeypatch.setattr(wallpaper_daemon.win32gui, 'GetForegroundWindow', lambda: 123)
    monkeypatch.setattr(wallpaper_daemon.win32gui, 'GetClassName', lambda hwnd: "SomeApp")

    # rect is (left, top, right, bottom)
    monkeypatch.setattr(wallpaper_daemon.win32gui, 'GetWindowRect', lambda hwnd: (-10, -10, 1930, 1090))

    assert wallpaper_daemon.is_fullscreen_app_active(1920, 1080) == True

def test_is_fullscreen_app_active_getwindowrect_exception(monkeypatch):
    monkeypatch.setattr(wallpaper_daemon.win32gui, 'GetForegroundWindow', lambda: 123)
    monkeypatch.setattr(wallpaper_daemon.win32gui, 'GetClassName', lambda hwnd: "SomeApp")

    def mock_get_window_rect(hwnd):
        raise Exception("Win32 exception")

    monkeypatch.setattr(wallpaper_daemon.win32gui, 'GetWindowRect', mock_get_window_rect)

    assert wallpaper_daemon.is_fullscreen_app_active(1920, 1080) == False
