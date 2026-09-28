from PIL import Image

def resize_to_fill(img, target_w, target_h):
    """
    Resizes and crops an image to fill the target dimensions,
    maintaining the original aspect ratio (mimics Windows' default "Fill" option).
    """
    img_w, img_h = img.size
    img_aspect = img_w / img_h
    target_aspect = target_w / target_h

    if img_aspect > target_aspect:
        # Image is wider than target aspect ratio - crop sides
        new_h = target_h
        new_w = int(new_h * img_aspect)
        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        start_x = (new_w - target_w) // 2
        return img_resized.crop((start_x, 0, start_x + target_w, target_h))
    else:
        # Image is taller than target aspect ratio - crop top/bottom
        new_w = target_w
        new_h = int(new_w / img_aspect)
        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        start_y = (new_h - target_h) // 2
        return img_resized.crop((0, start_y, target_w, start_y + target_h))
