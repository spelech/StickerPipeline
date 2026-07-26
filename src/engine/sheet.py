from PIL import Image
import io
import math
from typing import List, Tuple
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.units import inch

class SheetGenerator:
    """Arranges sticker images into grid page layouts and generates high-DPI PDF/PNG sheets."""
    
    def __init__(self, dpi: int = 300, paper_size: str = "LETTER"):
        self.dpi = dpi
        self.paper_size = paper_size.upper()
        
        # Dimensions in inches
        if self.paper_size == "LETTER":
            self.page_width_in = 8.5
            self.page_height_in = 11.0
        else: # Default A4 or Joy mat
            self.page_width_in = 8.27
            self.page_height_in = 11.69
            
        # Target pixel bounds at given DPI
        self.page_width_px = int(self.page_width_in * self.dpi)
        self.page_height_px = int(self.page_height_in * self.dpi)
        
        # Printable margins (0.5 inch margins for Cricut registration bounds)
        self.margin_px = int(0.5 * self.dpi)

    def build_sheet(
        self,
        images: List[Image.Image],
        target_sticker_height_in: float = 2.5
    ) -> Tuple[Image.Image, bytes]:
        """
        Packs sticker images into a grid sheet layout.
        
        Returns:
            Tuple[Image.Image, bytes]: (Assembled sheet PIL Image, High-DPI PDF bytes)
        """
        sheet_canvas = Image.new("RGBA", (self.page_width_px, self.page_height_px), (255, 255, 255, 255))
        
        target_size_px = int(target_sticker_height_in * self.dpi)
        
        usable_w = self.page_width_px - (2 * self.margin_px)
        usable_h = self.page_height_px - (2 * self.margin_px)
        
        cols = max(1, usable_w // (target_size_px + 20))
        rows = max(1, usable_h // (target_size_px + 20))
        max_per_page = cols * rows
        
        x_offset = self.margin_px
        y_offset = self.margin_px
        col_idx = 0
        row_idx = 0
        
        pdf_buffer = io.BytesIO()
        pdf = pdf_canvas.Canvas(pdf_buffer, pagesize=letter)
        
        for idx, img in enumerate(images[:max_per_page]):
            # Resize image keeping aspect ratio
            img_copy = img.copy()
            img_copy.thumbnail((target_size_px, target_size_px), Image.Resampling.LANCZOS)
            
            px = x_offset + (col_idx * (target_size_px + 20))
            py = y_offset + (row_idx * (target_size_px + 20))
            
            sheet_canvas.paste(img_copy, (px, py), mask=img_copy if img_copy.mode == "RGBA" else None)
            
            # Draw to PDF ReportLab canvas (converting coordinates from top-left to bottom-left)
            pdf_x = (px / self.dpi) * inch
            pdf_y = ((self.page_height_px - py - img_copy.height) / self.dpi) * inch
            pdf_w = (img_copy.width / self.dpi) * inch
            pdf_h = (img_copy.height / self.dpi) * inch
            
            img_bytes_io = io.BytesIO()
            img_copy.save(img_bytes_io, format="PNG")
            img_bytes_io.seek(0)
            
            pdf.drawImage(
                image=pdf_canvas.ImageReader(img_bytes_io),
                x=pdf_x,
                y=pdf_y,
                width=pdf_w,
                height=pdf_h,
                mask='auto'
            )
            
            col_idx += 1
            if col_idx >= cols:
                col_idx = 0
                row_idx += 1
                
        pdf.save()
        pdf_bytes = pdf_buffer.getvalue()
        
        return sheet_canvas, pdf_bytes
