import pytest
from fastapi.testclient import TestClient
from PIL import Image
import io
import json

from src.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "sticker-pipeline"

def test_manual_process_upload_endpoint():
    # Create test synthetic PNG image
    img = Image.new("RGBA", (150, 150), (255, 0, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    
    response = client.post(
        "/api/v1/process",
        files={"file": ("test_upload.png", buf, "image/png")},
        data={"border_px": 15}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "bordered_path" in data

def test_list_stickers_endpoint():
    response = client.get("/api/v1/stickers")
    assert response.status_code == 200
    data = response.json()
    assert "stickers" in data
    assert "sheets" in data

def test_openai_image_generations_interceptor(monkeypatch):
    # Mock httpx response from upstream LLM/SD
    img = Image.new("RGB", (200, 200), (0, 255, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    import base64
    b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
    
    mock_dict = {
        "created": 123456789,
        "data": [{"b64_json": b64_str}]
    }
    
    class MockResponse:
        status_code = 200
        content = json.dumps(mock_dict).encode("utf-8")
        text = json.dumps(mock_dict)
        def json(self):
            return mock_dict
            
    async def mock_post(*args, **kwargs):
        return MockResponse()
        
    import httpx
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    
    response = client.post(
        "/v1/images/generations",
        json={"prompt": "A cute sticker of a panda [STICKER]", "n": 1, "size": "1024x1024"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
