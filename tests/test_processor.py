import pytest
from PIL import Image, ImageDraw
import numpy as np
import io

from src.engine.contour import create_sticker_contour
from src.engine.processor import StickerProcessor
from src.engine.sheet import SheetGenerator

def create_synthetic_image() -> Image.Image:
    """Creates a synthetic RGB sticker test image (red circle on white background)."""
    img = Image.new("RGB", (300, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse((50, 50, 250, 250), fill=(220, 50, 50), outline=(0, 0, 0), width=4)
    return img

def test_create_sticker_contour():
    # Create synthetic RGBA image with alpha channel
    rgba = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    draw = ImageDraw.Draw(rgba)
    draw.ellipse((40, 40, 160, 160), fill=(255, 0, 0, 255))
    
    # Process contour
    bordered, mask = create_sticker_contour(rgba, border_offset_px=15, border_color=(255, 255, 255))
    
    assert isinstance(bordered, Image.Image)
    assert bordered.size[0] >= 200 and bordered.size[1] >= 200
    assert bordered.mode == "RGBA"

def test_sheet_generator():
    img1 = Image.new("RGBA", (200, 200), (255, 255, 255, 255))
    img2 = Image.new("RGBA", (200, 200), (255, 255, 255, 255))
    
    generator = SheetGenerator(dpi=300, paper_size="LETTER")
    sheet_img, pdf_bytes = generator.build_sheet([img1, img2])
    
    assert isinstance(sheet_img, Image.Image)
    assert len(pdf_bytes) > 0

def test_sticker_processor_pipeline(tmp_path):
    storage_dir = tmp_path / "stickers"
    processor = StickerProcessor(storage_dir=str(storage_dir), border_offset_px=10)
    
    test_img = create_synthetic_image()
    buf = io.BytesIO()
    test_img.save(buf, format="PNG")
    raw_bytes = buf.getvalue()
    
    result = processor.process_image_bytes(raw_bytes, filename_prefix="test_item")
    
    assert result["raw_path"] is not None
    assert result["nobg_path"] is not None
    assert result["bordered_path"] is not None
    assert (storage_dir / "raw").exists()
    assert (storage_dir / "processed").exists()
