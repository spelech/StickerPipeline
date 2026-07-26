from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.api.routes import router as api_router
from src.api.interceptor import handle_openai_image_proxy

app = FastAPI(
    title="StickerPipeline API",
    description="Automated Cricut Joy 2 & Epson EcoTank sticker generation and prep pipeline microservice.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/health")
async def healthcheck():
    return {
        "status": "ok",
        "service": "sticker-pipeline",
        "version": "1.0.0"
    }

@app.post("/v1/images/generations")
async def proxy_images_generations(request: Request, background_tasks: BackgroundTasks):
    return await handle_openai_image_proxy(request, background_tasks)
