from fastapi import APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path

from src.config import settings
from src.engine.processor import StickerProcessor

router = APIRouter(prefix="/api/v1")
processor = StickerProcessor(
    storage_dir=settings.sticker_storage_dir,
    border_offset_px=settings.border_offset_px,
    dpi=settings.target_dpi
)

class SheetBuildRequest(BaseModel):
    max_stickers: Optional[int] = 6
    paper_size: Optional[str] = "LETTER"

@router.post("/process")
async def process_manual_upload(
    file: UploadFile = File(...),
    border_px: Optional[int] = Form(20)
):
    """Processes a manually uploaded image file and returns processed sticker paths."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")
        
    contents = await file.read()
    
    # Custom border px if provided
    proc = StickerProcessor(
        storage_dir=settings.sticker_storage_dir,
        border_offset_px=border_px or settings.border_offset_px,
        dpi=settings.target_dpi
    )
    
    result = proc.process_image_bytes(contents, filename_prefix=Path(file.filename).stem)
    return result

@router.get("/stickers")
async def list_stickers():
    """Lists raw, processed, and sheet artifacts in storage."""
    processed_dir = Path(settings.sticker_storage_dir) / "processed"
    sheets_dir = Path(settings.sticker_storage_dir) / "sheets"
    
    stickers = [p.name for p in processed_dir.glob("*_bordered.png")] if processed_dir.exists() else []
    sheets = [p.name for p in sheets_dir.glob("*.pdf")] if sheets_dir.exists() else []
    
    return {
        "stickers": stickers,
        "sheets": sheets
    }

@router.post("/sheets/build")
async def build_sticker_sheet(req: SheetBuildRequest):
    """Generates a printable 300 DPI sheet layout from recent processed stickers."""
    try:
        res = processor.generate_sheet_from_processed(max_stickers=req.max_stickers or 6)
        return res
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
