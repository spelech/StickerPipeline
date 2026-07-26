import httpx
import base64
import json
import logging
from typing import Dict, Any
from fastapi import Request, Response, BackgroundTasks
from src.config import settings
from src.engine.processor import StickerProcessor

logger = logging.getLogger("sticker-pipeline.interceptor")
processor = StickerProcessor(
    storage_dir=settings.sticker_storage_dir,
    border_offset_px=settings.border_offset_px,
    dpi=settings.target_dpi
)

def _process_image_background(img_bytes: bytes, prefix: str):
    try:
        res = processor.process_image_bytes(img_bytes, filename_prefix=prefix)
        logger.info(f"Successfully auto-processed sticker {res['id']}")
    except Exception as e:
        logger.error(f"Failed background sticker processing: {e}")

async def handle_openai_image_proxy(request: Request, background_tasks: BackgroundTasks) -> Response:
    """Proxies /v1/images/generations to upstream LiteLLM and captures generated sticker images."""
    body = await request.json()
    prompt = body.get("prompt", "")
    
    # Check if request has sticker tag or metadata marker
    is_sticker = "[STICKER]" in prompt.upper() or "STICKER" in body.get("model", "").upper() or body.get("is_sticker", False)
    
    # Force b64_json format so we can extract image bytes directly
    upstream_body = dict(body)
    if is_sticker:
        upstream_body["response_format"] = "b64_json"
        
    async with httpx.AsyncClient(timeout=120.0) as client:
        url = f"{settings.upstream_llm_url.rstrip('/')}/images/generations"
        headers = {k: v for k, v in request.headers.items() if k.lower() not in ["host", "content-length"]}
        
        try:
            resp = await client.post(url, json=upstream_body, headers=headers)
        except Exception as e:
            return Response(content=f'{{"error": "{str(e)}"}}', status_code=502, media_type="application/json")
            
        content_bytes = getattr(resp, "content", resp.text.encode("utf-8") if hasattr(resp, "text") else json.dumps(resp.json()).encode("utf-8"))
        
        if resp.status_code == 200 and is_sticker:
            resp_data = resp.json()
            items = resp_data.get("data", [])
            for idx, item in enumerate(items):
                if "b64_json" in item:
                    img_bytes = base64.b64decode(item["b64_json"])
                    background_tasks.add_task(_process_image_background, img_bytes, f"gen_{idx}")
                elif "url" in item:
                    # Download URL image asynchronously
                    async with httpx.AsyncClient() as img_client:
                        r = await img_client.get(item["url"])
                        if r.status_code == 200:
                            background_tasks.add_task(_process_image_background, r.content, f"gen_{idx}")
                            
            return Response(content=content_bytes, status_code=resp.status_code, media_type="application/json")
        else:
            return Response(content=content_bytes, status_code=resp.status_code, media_type="application/json")
