import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.routers import (
    assets,
    auth,
    characters,
    generate,
    image_generator,
    projects,
    scenes,
    script_generator,
    shots,
    templates,
    tts,
    video,
)

app = FastAPI(
    title="AI漫剧制作平台 API",
    description="模板驱动的AI漫剧批量生产平台",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
os.makedirs(settings.upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# Routers
app.include_router(auth.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(templates.router, prefix="/api")
app.include_router(generate.router, prefix="/api")
app.include_router(characters.router, prefix="/api")
app.include_router(scenes.router, prefix="/api")
app.include_router(shots.router, prefix="/api")
app.include_router(assets.router, prefix="/api")
app.include_router(script_generator.router, prefix="/api")
app.include_router(tts.router, prefix="/api")
app.include_router(image_generator.router, prefix="/api")
app.include_router(video.router, prefix="/api")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "AI漫剧制作平台后端运行中"}


# ── 生产模式：托管前端构建产物（frontend/dist），单命令访问全站 ──
_FRONTEND_DIST = os.path.abspath(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "frontend", "dist")
)


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_frontend(full_path: str):
    if full_path.startswith(("api/", "uploads/")):
        raise HTTPException(status_code=404, detail="Not Found")
    if os.path.isdir(_FRONTEND_DIST):
        target = os.path.join(_FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(target):
            return FileResponse(target)
        index = os.path.join(_FRONTEND_DIST, "index.html")
        if os.path.isfile(index):
            return FileResponse(index)  # SPA history 回退
    raise HTTPException(status_code=404, detail="前端未构建，请先运行 npm run build 或使用开发模式")
