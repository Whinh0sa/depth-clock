import sys
import unittest
from unittest.mock import MagicMock
from PIL import Image, ImageDraw

# Mock dependencies before importing the module to allow it to load without Windows APIs
sys.modules['win32api'] = MagicMock()
sys.modules['win32gui'] = MagicMock()
sys.modules['win32con'] = MagicMock()
sys.modules['win32process'] = MagicMock()
sys.modules['win32event'] = MagicMock()
sys.modules['winerror'] = MagicMock()
sys.modules['pystray'] = MagicMock()
sys.modules['ctypes'] = MagicMock()
sys.modules['numpy'] = MagicMock()

import wallpaper_daemon

class TestWallpaperDaemon(unittest.TestCase):

    def test_resize_to_fill_wider_image(self):
        """Test resizing when original image is wider than target aspect ratio (img_aspect > target_aspect)."""
        # Create an image of 200x100
        # Target aspect ratio is 1.0 (100x100), image aspect is 2.0
        # It should scale height to 100, which makes width 200.
        # Then crop to 100x100 from the center, meaning it should crop out x=0 to 50, and x=150 to 200.
        # So we should be left with what was originally at x=50 to 150.

        # We will color the left 50px Red, the middle 100px Green, and the right 50px Blue.
        img = Image.new('RGB', (200, 100))
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, 50, 100], fill='red')
        draw.rectangle([50, 0, 150, 100], fill='green')
        draw.rectangle([150, 0, 200, 100], fill='blue')

        result = wallpaper_daemon.resize_to_fill(img, 100, 100)

        # Check dimensions
        self.assertEqual(result.size, (100, 100))

        # Check center pixel color (should be green)
        center_pixel = result.getpixel((50, 50))
        # Lanczos resampling might alter pure colors slightly, but it should be very close to green
        # Pure green is (0, 128, 0). Actually string 'green' maps to (0, 128, 0).
        self.assertEqual(center_pixel, (0, 128, 0))

        # Check edge pixel to make sure it's green too (it shouldn't be red or blue)
        edge_pixel = result.getpixel((5, 50))
        self.assertEqual(edge_pixel, (0, 128, 0))

    def test_resize_to_fill_taller_image(self):
        """Test resizing when original image is taller than target aspect ratio (img_aspect < target_aspect)."""
        # Create an image of 100x200
        # Target aspect ratio is 1.0 (100x100), image aspect is 0.5
        # It should scale width to 100, which makes height 200.
        # Then crop to 100x100 from the center, meaning it should crop out y=0 to 50, and y=150 to 200.

        # We will color the top 50px Red, the middle 100px Green, and the bottom 50px Blue.
        img = Image.new('RGB', (100, 200))
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, 100, 50], fill='red')
        draw.rectangle([0, 50, 100, 150], fill='green')
        draw.rectangle([0, 150, 100, 200], fill='blue')

        result = wallpaper_daemon.resize_to_fill(img, 100, 100)

        # Check dimensions
        self.assertEqual(result.size, (100, 100))

        # Check center pixel color (should be green)
        center_pixel = result.getpixel((50, 50))
        self.assertEqual(center_pixel, (0, 128, 0))

        # Check top pixel (should be green, not red)
        top_pixel = result.getpixel((50, 5))
        self.assertEqual(top_pixel, (0, 128, 0))

    def test_resize_to_fill_same_aspect(self):
        """Test resizing when original image has the exact same aspect ratio as target."""
        # Image is 200x200 (aspect 1.0)
        # Target is 100x100 (aspect 1.0)
        # Should just scale without cropping anything out (other than what resize inherently does)

        img = Image.new('RGB', (200, 200), color='white')

        result = wallpaper_daemon.resize_to_fill(img, 100, 100)

        # Check dimensions
        self.assertEqual(result.size, (100, 100))

        # Check pixel color
        center_pixel = result.getpixel((50, 50))
        self.assertEqual(center_pixel, (255, 255, 255))

    def test_wallpaper_sources_urls(self):
        """Test URL generation from wallpaper_sources."""
        from wallpaper_sources import CURATED_WALLPAPERS, get_wallpaper_url
        
        # Test curated source
        for category in CURATED_WALLPAPERS.keys():
            url = get_wallpaper_url(category, 1920, 1080)
            self.assertIn(url, CURATED_WALLPAPERS[category])
            
        # Test picsum sources
        picsum_url = get_wallpaper_url("Picsum Photos (Random)", 1920, 1080)
        self.assertTrue(picsum_url.startswith("https://picsum.photos/1920/1080?random="))
        
        gray_url = get_wallpaper_url("Picsum Photos (Grayscale)", 1920, 1080)
        self.assertIn("&grayscale", gray_url)
        
        blur_url = get_wallpaper_url("Picsum Photos (Blur)", 1920, 1080)
        self.assertIn("&blur", blur_url)

    def test_interval_seconds_mapping(self):
        """Verify daemon interval definitions."""
        self.assertEqual(wallpaper_daemon.INTERVAL_SECONDS["15 Minutes"], 900)
        self.assertEqual(wallpaper_daemon.INTERVAL_SECONDS["30 Minutes"], 1800)
        self.assertEqual(wallpaper_daemon.INTERVAL_SECONDS["1 Hour"], 3600)
        self.assertEqual(wallpaper_daemon.INTERVAL_SECONDS["3 Hours"], 10800)
        self.assertEqual(wallpaper_daemon.INTERVAL_SECONDS["6 Hours"], 21600)
        self.assertEqual(wallpaper_daemon.INTERVAL_SECONDS["12 Hours"], 43200)
        self.assertEqual(wallpaper_daemon.INTERVAL_SECONDS["Daily"], 86400)


if __name__ == '__main__':
    unittest.main()

