from PIL import Image, ImageFilter
import cv2
import numpy as np
from typing import Tuple

def create_sticker_contour(
    rgba_image: Image.Image,
    border_offset_px: int = 20,
    border_color: Tuple[int, int, int] = (255, 255, 255)
) -> Tuple[Image.Image, Image.Image]:
    """
    Generates a die-cut white contour border around an RGBA image subject.
    
    Args:
        rgba_image: PIL Image in RGBA mode with transparent background.
        border_offset_px: Distance in pixels for the offset outline border.
        border_color: RGB tuple for the offset border (default white: 255, 255, 255).
        
    Returns:
        Tuple[Image.Image, Image.Image]: (Bordered RGBA image, Alpha mask image)
    """
    if rgba_image.mode != "RGBA":
        rgba_image = rgba_image.convert("RGBA")
        
    # Expand canvas padding to prevent border clipping at image edges
    pad = border_offset_px * 2
    new_w = rgba_image.width + (pad * 2)
    new_h = rgba_image.height + (pad * 2)
    
    canvas = Image.new("RGBA", (new_w, new_h), (0, 0, 0, 0))
    canvas.paste(rgba_image, (pad, pad), mask=rgba_image)
    
    np_img = np.array(canvas)
    alpha = np_img[:, :, 3]
    
    # Threshold alpha mask
    _, alpha_thresh = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)
    
    # Kernel dilation
    kernel_size = (border_offset_px * 2) + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    dilated_mask = cv2.dilate(alpha_thresh, kernel, iterations=1)
    
    # Smooth edges with Gaussian Blur and re-threshold
    blurred_mask = cv2.GaussianBlur(dilated_mask, (5, 5), 0)
    _, final_mask = cv2.threshold(blurred_mask, 128, 255, cv2.THRESH_BINARY)
    
    # Construct background color layer for border
    border_layer = np.zeros((new_h, new_w, 4), dtype=np.uint8)
    border_layer[:, :, 0] = border_color[0]
    border_layer[:, :, 1] = border_color[1]
    border_layer[:, :, 2] = border_color[2]
    border_layer[:, :, 3] = final_mask
    
    border_pil = Image.fromarray(border_layer, mode="RGBA")
    
    # Composite subject on top of white border
    composite = Image.alpha_composite(border_pil, canvas)
    mask_pil = Image.fromarray(final_mask, mode="L")
    
    return composite, mask_pil
