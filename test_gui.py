import sys
from unittest.mock import MagicMock

# Mock required modules to run in non-Windows environments
sys.modules['win32api'] = MagicMock()
sys.modules['win32con'] = MagicMock()
sys.modules['winreg'] = MagicMock()
sys.modules['customtkinter'] = MagicMock()
sys.modules['ctypes'] = MagicMock()
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()

import gui
from PIL import Image

def test_resize_to_fill_same_aspect_ratio():
    img = Image.new('RGB', (200, 200), color='red')
    resized = gui.resize_to_fill(img, 100, 100)
    assert resized.size == (100, 100)

def test_resize_to_fill_wider_than_target():
    img = Image.new('RGB', (400, 200), color='green') # Aspect 2:1
    resized = gui.resize_to_fill(img, 100, 100) # Target aspect 1:1
    assert resized.size == (100, 100)

def test_resize_to_fill_taller_than_target():
    img = Image.new('RGB', (200, 400), color='blue') # Aspect 1:2
    resized = gui.resize_to_fill(img, 100, 100) # Target aspect 1:1
    assert resized.size == (100, 100)

def test_resize_to_fill_exact_match():
    img = Image.new('RGB', (1920, 1080))
    resized = gui.resize_to_fill(img, 1920, 1080)
    assert resized.size == (1920, 1080)

def test_resize_to_fill_crop_correctness_wide():
    # Make a 400x200 image. Middle 200x200 is red, edges are black.
    img = Image.new('RGB', (400, 200), color='black')
    for x in range(100, 300):
        for y in range(200):
            img.putpixel((x, y), (255, 0, 0))

    resized = gui.resize_to_fill(img, 100, 100)
    assert resized.size == (100, 100)
    # Check middle pixel is red (it should crop edges and scale down the middle)
    assert resized.getpixel((50, 50)) == (255, 0, 0)

def test_resize_to_fill_crop_correctness_tall():
    # Make a 200x400 image. Middle 200x200 is green, top/bottom black.
    img = Image.new('RGB', (200, 400), color='black')
    for x in range(200):
        for y in range(100, 300):
            img.putpixel((x, y), (0, 255, 0))

    resized = gui.resize_to_fill(img, 100, 100)
    assert resized.size == (100, 100)
    assert resized.getpixel((50, 50)) == (0, 255, 0)
