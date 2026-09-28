import pytest
from PIL import Image
from image_utils import resize_to_fill

def test_resize_to_fill_wider_image():
    img = Image.new('RGB', (200, 100))
    resized_img = resize_to_fill(img, 100, 100)
    assert resized_img.size == (100, 100)

def test_resize_to_fill_taller_image():
    img = Image.new('RGB', (100, 200))
    resized_img = resize_to_fill(img, 100, 100)
    assert resized_img.size == (100, 100)

def test_resize_to_fill_exact_aspect_ratio():
    img = Image.new('RGB', (200, 200))
    resized_img = resize_to_fill(img, 100, 100)
    assert resized_img.size == (100, 100)
