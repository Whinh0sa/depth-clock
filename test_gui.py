import os
import tempfile
from PIL import Image
import pytest
from gui import get_dominant_colors

def create_temp_image(color_blocks):
    """Creates a temporary image with specified color blocks and returns its path."""
    # Create a 100x100 image
    img = Image.new('RGB', (100, 100))

    # Fill with color blocks
    num_blocks = len(color_blocks)
    if num_blocks > 0:
        block_height = 100 // num_blocks
        for i, color in enumerate(color_blocks):
            # Fill a horizontal strip with the color
            for y in range(i * block_height, (i + 1) * block_height if i < num_blocks - 1 else 100):
                for x in range(100):
                    img.putpixel((x, y), color)

    fd, path = tempfile.mkstemp(suffix='.png')
    os.close(fd)
    img.save(path)
    return path

def test_get_dominant_colors_normal():
    # Red, Green, Blue blocks
    path = create_temp_image([(255, 0, 0), (0, 255, 0), (0, 0, 255)])
    try:
        colors = get_dominant_colors(path)
        # Should contain hex codes for red, green, blue
        assert "#ff0000" in colors
        assert "#00ff00" in colors
        assert "#0000ff" in colors
        assert len(colors) == 3
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_get_dominant_colors_black():
    # Dark block, sum(rgb) < 50, so should be ignored
    path = create_temp_image([(10, 10, 10)])
    try:
        colors = get_dominant_colors(path)
        assert colors == []
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_get_dominant_colors_invalid_path():
    # Invalid path should be caught by exception handler and return empty list
    colors = get_dominant_colors("non_existent_file.png")
    assert colors == []
