from PIL import Image, ImageDraw
import io
import math
from typing import List, Tuple
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.units import inch

class SheetGenerator:
    """Arranges sticker images into grid page layouts formatted for Cricut Joy 2 mats & standard paper sizes."""
    
    def __init__(self, dpi: int = 300, paper_size: str = "JOY2_LETTER"):
        self.dpi = dpi
        self.paper_size = paper_size.upper()
        
        # Page dimensions in inches
        if self.paper_size == "JOY2_MAT":
            # Cricut Joy 2 Standard Mat size (4.5" x 6.5")
            self.page_width_in = 4.5
            self.page_height_in = 6.5
            self.margin_px = int(0.25 * self.dpi)
        elif self.paper_size in ["JOY2_LETTER", "LETTER"]:
            # Cricut Joy 2 Letter Mat / US Letter (8.5" x 11")
            self.page_width_in = 8.5
            self.page_height_in = 11.0
            self.margin_px = int(0.5 * self.dpi)
        else: # A4
            self.page_width_in = 8.27
            self.page_height_in = 11.69
            self.margin_px = int(0.5 * self.dpi)
            
        # Target pixel bounds at given DPI
        self.page_width_px = int(self.page_width_in * self.dpi)
        self.page_height_px = int(self.page_height_in * self.dpi)

    def build_sheet(
        self,
        images: List[Image.Image],
        target_sticker_height_in: float = 2.0,
        add_registration_frame: bool = True
    ) -> Tuple[Image.Image, bytes]:
        """
        Packs sticker images into a grid sheet layout formatted for Cricut Joy 2.
        
        Args:
            images: List of transparent/bordered PIL RGBA images.
            target_sticker_height_in: Target height/width for each sticker in inches.
            add_registration_frame: Whether to draw a thin registration bounding box for Cricut sensors.
            
        Returns:
            Tuple[Image.Image, bytes]: (Assembled sheet PIL Image, High-DPI PDF bytes)
        """
        sheet_canvas = Image.new("RGBA", (self.page_width_px, self.page_height_px), (255, 255, 255, 255))
        draw = ImageDraw.Draw(sheet_canvas)
        
        # Optional Cricut Print-Then-Cut Registration Box Outline (1/4" inside margin)
        if add_registration_frame:
            rect_margin = int(0.25 * self.dpi)
            draw.rectangle(
                [(rect_margin, rect_margin), (self.page_width_px - rect_margin, self.page_height_px - rect_margin)],
                outline=(0, 0, 0, 255),
                width=int(0.04 * self.dpi) # 3pt solid line
            )
        
        target_size_px = int(target_sticker_height_in * self.dpi)
        spacing_px = int(0.15 * self.dpi) # 0.15 inch gap
        
        usable_w = self.page_width_px - (2 * self.margin_px)
        usable_h = self.page_height_px - (2 * self.margin_px)
        
        cols = max(1, usable_w // (target_size_px + spacing_px))
        rows = max(1, usable_h // (target_size_px + spacing_px))
        max_per_page = cols * rows
        
        x_offset = self.margin_px + max(0, (usable_w - (cols * (target_size_px + spacing_px))) // 2)
        y_offset = self.margin_px + max(0, (usable_h - (rows * (target_size_px + spacing_px))) // 2)
        
        col_idx = 0
        row_idx = 0
        
        pdf_pagesize = (self.page_width_in * inch, self.page_height_in * inch)
        pdf_buffer = io.BytesIO()
        pdf = pdf_canvas.Canvas(pdf_buffer, pagesize=pdf_pagesize)
        
        # Draw registration frame in PDF
        if add_registration_frame:
            rect_in = 0.25
            pdf.setLineWidth(2)
            pdf.rect(
                rect_in * inch,
                rect_in * inch,
                (self.page_width_in - (2 * rect_in)) * inch,
                (self.page_height_in - (2 * rect_in)) * inch,
                stroke=1,
                fill=0
            )
        
        for idx, img in enumerate(images[:max_per_page]):
            img_copy = img.copy()
            img_copy.thumbnail((target_size_px, target_size_px), Image.Resampling.LANCZOS)
            
            px = x_offset + (col_idx * (target_size_px + spacing_px))
            py = y_offset + (row_idx * (target_size_px + spacing_px))
            
            sheet_canvas.paste(img_copy, (px, py), mask=img_copy if img_copy.mode == "RGBA" else None)
            
            # ReportLab coordinate mapping
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
