from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from src.config import settings
from src.api.routes import router as api_router
from src.api.interceptor import handle_openai_image_proxy

app = FastAPI(
    title="StickerPipeline API",
    description="Automated Cricut Joy 2 & Epson EcoTank sticker generation and prep pipeline microservice.",
    version="1.0.5"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# Serve storage files if directory exists
storage_path = Path(settings.sticker_storage_dir)
if storage_path.exists():
    app.mount("/storage", StaticFiles(directory=str(storage_path)), name="storage")

@app.get("/health")
async def healthcheck():
    return {
        "status": "ok",
        "service": "sticker-pipeline",
        "version": "1.0.5"
    }

@app.get("/", response_class=HTMLResponse)
async def root_dashboard():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StickerPipeline - Cricut Joy 2 Studio</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --accent: #ec4899;
            --accent-hover: #db2777;
            --text: #f8fafc;
            --muted: #94a3b8;
            --border: rgba(255, 255, 255, 0.1);
        }
        body {
            font-family: 'Inter', sans-serif;
            background: radial-gradient(circle at top right, #1e1b4b, #0f172a);
            color: var(--text);
            margin: 0;
            padding: 0;
            min-height: 100vh;
        }
        .header {
            padding: 2rem 5%;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            backdrop-filter: blur(10px);
        }
        .logo {
            font-size: 1.5rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            background: linear-gradient(to right, #ec4899, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .container {
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 1.5rem;
        }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
        }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.5rem;
            backdrop-filter: blur(12px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        .dropzone {
            border: 2px dashed #ec4899;
            border-radius: 12px;
            padding: 2.5rem 1.5rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
            background: rgba(236, 72, 153, 0.05);
        }
        .dropzone:hover {
            background: rgba(236, 72, 153, 0.15);
            border-color: #f472b6;
        }
        .btn {
            background: linear-gradient(135deg, #ec4899, #8b5cf6);
            color: white;
            border: none;
            padding: 0.75rem 1.25rem;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        .btn:hover { opacity: 0.9; }
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
            max-height: 350px;
            overflow-y: auto;
        }
        .gallery-item {
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            padding: 0.5rem;
            border: 1px solid var(--border);
            text-align: center;
            position: relative;
        }
        .gallery-item img {
            width: 100%;
            height: 110px;
            object-fit: contain;
        }
        .badge {
            font-size: 0.75rem;
            background: rgba(236, 72, 153, 0.2);
            color: #f472b6;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
        }
        .form-group {
            margin-bottom: 1rem;
        }
        .form-group label {
            display: block;
            font-size: 0.85rem;
            color: var(--muted);
            margin-bottom: 0.4rem;
        }
        select, input[type="number"] {
            width: 100%;
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid var(--border);
            color: white;
            padding: 0.6rem;
            border-radius: 6px;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">
            <i class="fa-solid fa-scissors"></i> StickerPipeline Studio
        </div>
        <div>
            <span class="badge"><i class="fa-solid fa-sliders"></i> Cricut Joy 2 Format Configured</span>
            <a href="/docs" style="color: var(--muted); margin-left: 1rem; text-decoration: none;" target="_blank"><i class="fa-solid fa-code"></i> API Docs</a>
        </div>
    </div>

    <div class="container">
        <div class="grid">
            <div class="card">
                <h2><i class="fa-solid fa-cloud-arrow-up"></i> Image Ingress</h2>
                <p style="color: var(--muted);">Upload any image to generate background removal + 300 DPI die-cut white outline for Cricut Joy 2.</p>
                
                <form id="uploadForm" enctype="multipart/form-data">
                    <div class="dropzone" onclick="document.getElementById('fileInput').click()">
                        <i class="fa-solid fa-image fa-3x" style="color: #ec4899; margin-bottom: 1rem;"></i>
                        <p><strong>Click to Upload</strong> or drag image here</p>
                        <span style="font-size: 0.85rem; color: var(--muted);">PNG, JPG, WEBP up to 20MB</span>
                        <input type="file" id="fileInput" name="file" accept="image/*" style="display: none" onchange="uploadImage()">
                    </div>
                </form>
                <div id="status" style="margin-top: 1rem; color: #f472b6; font-weight: 500;"></div>
            </div>

            <div class="card">
                <h2><i class="fa-solid fa-sliders"></i> Cricut Joy 2 Sheet Configurator</h2>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div class="form-group">
                        <label><i class="fa-solid fa-ruler-combined"></i> Target Paper / Mat Preset</label>
                        <select id="paperPreset">
                            <option value="JOY2_LETTER" selected>Cricut Joy 2 Letter Mat (8.5" x 11")</option>
                            <option value="JOY2_MAT">Cricut Joy 2 Standard Mat (4.5" x 6.5")</option>
                            <option value="LETTER">Standard US Letter (8.5" x 11")</option>
                            <option value="A4">Standard A4 (8.27" x 11.69")</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label><i class="fa-solid fa-up-right-and-down-left-from-center"></i> Sticker Size (Inches)</label>
                        <select id="stickerSize">
                            <option value="1.5">1.5 in (Mini)</option>
                            <option value="2.0" selected>2.0 in (Standard)</option>
                            <option value="2.5">2.5 in (Medium)</option>
                            <option value="3.0">3.0 in (Large)</option>
                        </select>
                    </div>
                </div>

                <div class="form-group" style="margin-top: 0.5rem;">
                    <label style="display: inline-flex; align-items: center; gap: 0.5rem; cursor: pointer; color: white;">
                        <input type="checkbox" id="regFrame" checked style="width: auto;">
                        Include Cricut Sensor Registration Outline Box (3pt Line)
                    </label>
                </div>

                <button class="btn" style="width: 100%; margin-top: 0.5rem; justify-content: center;" onclick="buildSheet()">
                    <i class="fa-solid fa-file-pdf"></i> Generate Cricut Joy 2 Sheet (PDF/PNG)
                </button>

                <h3 style="font-size: 1rem; margin-top: 1.5rem;"><i class="fa-solid fa-images"></i> Processed Stickers Gallery</h3>
                <div class="gallery" id="stickerGallery">
                    <div style="color: var(--muted); padding: 1.5rem; text-align: center;">Loading stickers...</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function loadStickers() {
            try {
                const res = await fetch('/api/v1/stickers');
                const data = await res.json();
                const gallery = document.getElementById('stickerGallery');
                
                if (data.stickers.length === 0) {
                    gallery.innerHTML = '<div style="color: var(--muted); padding: 1.5rem; text-align: center;">No stickers processed yet. Generate images with [STICKER] tag or upload above!</div>';
                    return;
                }
                
                gallery.innerHTML = data.stickers.map(name => `
                    <div class="gallery-item">
                        <img src="/storage/processed/${name}" alt="${name}">
                        <div style="font-size: 0.75rem; color: var(--muted); margin-top: 0.4rem; word-break: break-all;">${name.replace('_bordered.png', '')}</div>
                    </div>
                `).join('');
            } catch (err) {
                console.error(err);
            }
        }

        async function uploadImage() {
            const input = document.getElementById('fileInput');
            if (!input.files || input.files.length === 0) return;
            
            const formData = new FormData();
            formData.append('file', input.files[0]);
            
            const status = document.getElementById('status');
            status.innerText = 'Processing background removal & white contour...';
            
            try {
                const res = await fetch('/api/v1/process', {
                    method: 'POST',
                    body: formData
                });
                
                if (res.ok) {
                    status.innerText = '✅ Sticker processed successfully!';
                    loadStickers();
                } else {
                    status.innerText = '❌ Failed to process image.';
                }
            } catch (err) {
                status.innerText = '❌ Error uploading file.';
            }
        }

        async function buildSheet() {
            const status = document.getElementById('status');
            const paperPreset = document.getElementById('paperPreset').value;
            const stickerSize = parseFloat(document.getElementById('stickerSize').value);
            const regFrame = document.getElementById('regFrame').checked;
            
            status.innerText = 'Generating 300 DPI Cricut Joy 2 printable sheet...';
            
            try {
                const res = await fetch('/api/v1/sheets/build', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        max_stickers: 12,
                        paper_size: paperPreset,
                        sticker_size_in: stickerSize,
                        add_registration_frame: regFrame
                    })
                });
                
                const data = await res.json();
                if (res.ok) {
                    const filename = data.sheet_pdf_path.split('/').pop();
                    status.innerHTML = `✅ Sheet created! <a href="/storage/sheets/${filename}" target="_blank" style="color: #ec4899; font-weight: 700; text-decoration: underline;">Download PDF Sheet (${data.paper_size})</a>`;
                } else {
                    status.innerText = '❌ Failed to build sheet: ' + (data.detail || 'No stickers available');
                }
            } catch (err) {
                status.innerText = '❌ Error generating sheet.';
            }
        }

        loadStickers();
    </script>
</body>
</html>"""

@app.post("/v1/images/generations")
async def proxy_images_generations(request: Request, background_tasks: BackgroundTasks):
    return await handle_openai_image_proxy(request, background_tasks)
