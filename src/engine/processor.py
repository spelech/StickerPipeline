import os
import io
import time
import json
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image
import numpy as np

try:
    from rembg import remove, new_session
    HAS_REMBG = True
except ImportError:
    HAS_REMBG = False

from src.engine.contour import create_sticker_contour
from src.engine.sheet import SheetGenerator

class StickerProcessor:
    """Coordinates rembg background removal, OpenCV border generation, and storage management."""
    
    def __init__(self, storage_dir: str = "/app/storage", border_offset_px: int = 20, dpi: int = 300):
        try:
            self.storage_dir = Path(storage_dir)
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            self.storage_dir = Path("./storage")
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            
        self.border_offset_px = border_offset_px
        self.dpi = dpi
        
        self.raw_dir = self.storage_dir / "raw"
        self.processed_dir = self.storage_dir / "processed"
        self.sheets_dir = self.storage_dir / "sheets"
        self.metadata_dir = self.storage_dir / "metadata"
        
        for d in [self.raw_dir, self.processed_dir, self.sheets_dir, self.metadata_dir]:
            d.mkdir(parents=True, exist_ok=True)
            
        # Lazy load rembg session on demand
        self._rembg_session = None
        self.sheet_generator = SheetGenerator(dpi=self.dpi)

    @property
    def rembg_session(self):
        if self._rembg_session is None and HAS_REMBG:
            try:
                self._rembg_session = new_session(model_name="u2net")
            except Exception:
                self._rembg_session = None
        return self._rembg_session

    def _fallback_remove_bg(self, img: Image.Image) -> Image.Image:
        """Fallback background removal using luminance/color thresholding if rembg is not installed."""
        img_rgba = img.convert("RGBA")
        np_arr = np.array(img_rgba)
        
        # Mask white background pixels
        r, g, b, a = np_arr[:, :, 0], np_arr[:, :, 1], np_arr[:, :, 2], np_arr[:, :, 3]
        mask = (r > 235) & (g > 235) & (b > 235)
        np_arr[mask, 3] = 0
        
        return Image.fromarray(np_arr, mode="RGBA")

    def process_image_bytes(self, image_bytes: bytes, filename_prefix: Optional[str] = None) -> Dict[str, Any]:
        """
        Processes raw image binary payload:
        1. Saves raw image.
        2. Performs background removal via rembg (or fallback).
        3. Generates die-cut white contour offset border.
        4. Saves processed artifacts and JSON metadata.
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        prefix = filename_prefix or f"{timestamp}_{unique_id}"
        
        # Load PIL image
        raw_pil = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        
        # Save raw image
        raw_filename = f"{prefix}_raw.png"
        raw_path = self.raw_dir / raw_filename
        raw_pil.save(raw_path, format="PNG")
        
        # Background removal
        if HAS_REMBG and self.rembg_session:
            nobg_pil = remove(raw_pil, session=self.rembg_session)
        else:
            nobg_pil = self._fallback_remove_bg(raw_pil)
            
        nobg_filename = f"{prefix}_nobg.png"
        nobg_path = self.processed_dir / nobg_filename
        nobg_pil.save(nobg_path, format="PNG")
        
        # White contour outline
        bordered_pil, alpha_mask = create_sticker_contour(
            nobg_pil,
            border_offset_px=self.border_offset_px,
            border_color=(255, 255, 255)
        )
        bordered_filename = f"{prefix}_bordered.png"
        bordered_path = self.processed_dir / bordered_filename
        bordered_pil.save(bordered_path, format="PNG")
        
        # Metadata
        metadata = {
            "id": prefix,
            "timestamp": timestamp,
            "raw_filename": raw_filename,
            "nobg_filename": nobg_filename,
            "bordered_filename": bordered_filename,
            "dimensions": {"width": raw_pil.width, "height": raw_pil.height},
            "border_offset_px": self.border_offset_px,
            "dpi": self.dpi
        }
        
        metadata_path = self.metadata_dir / f"{prefix}.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
            
        return {
            "id": prefix,
            "raw_path": str(raw_path),
            "nobg_path": str(nobg_path),
            "bordered_path": str(bordered_path),
            "metadata": metadata
        }

    def generate_sheet_from_processed(self, max_stickers: int = 6) -> Dict[str, Any]:
        """Collects recent bordered sticker PNGs and generates a printable page layout sheet."""
        bordered_files = list(self.processed_dir.glob("*_bordered.png"))
        if not bordered_files:
            raise FileNotFoundError("No processed bordered stickers available to generate sheet.")
            
        images = [Image.open(p).convert("RGBA") for p in bordered_files[:max_stickers]]
        sheet_img, pdf_bytes = self.sheet_generator.build_sheet(images)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        sheet_img_filename = f"sheet_{timestamp}.png"
        sheet_pdf_filename = f"sheet_{timestamp}.pdf"
        
        sheet_img_path = self.sheets_dir / sheet_img_filename
        sheet_pdf_path = self.sheets_dir / sheet_pdf_filename
        
        sheet_img.save(sheet_img_path, format="PNG", dpi=(self.dpi, self.dpi))
        with open(sheet_pdf_path, "wb") as f:
            f.write(pdf_bytes)
            
        return {
            "sheet_img_path": str(sheet_img_path),
            "sheet_pdf_path": str(sheet_pdf_path),
            "sticker_count": len(images)
        }
