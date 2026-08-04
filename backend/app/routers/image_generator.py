"""画面生成调度器接口：单任务提交/轮询 + 剧本批量生成/进度"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.schemas.image import ASPECT_RATIOS, ImageResult, ImageTask
from app.schemas.script import ShotScript
from app.services.image_gen import BatchImageService, get_image_generator

router = APIRouter(prefix="/image-gen", tags=["画面生成调度"])

generator = get_image_generator()
batch_service = BatchImageService(generator=generator)


class BatchSubmitRequest(BaseModel):
    script: ShotScript = Field(..., description="分镜脚本（来自 /script-generator 的输出）")
    style: Optional[str] = Field(None, description="覆盖画风，缺省用脚本自带")
    aspect_ratio: Optional[str] = Field("9:16", description="长宽比")
    concurrency: int = Field(4, ge=1, le=8, description="并发数")


# ── 单任务 ──────────────────────────────────────────────

@router.post("/submit", summary="提交单个生图任务")
def submit_task(task: ImageTask) -> dict:
    if task.aspect_ratio not in ASPECT_RATIOS:
        raise HTTPException(status_code=400, detail=f"不支持的长宽比: {task.aspect_ratio}")
    task_id = generator.submit_task(task)
    return {"task_id": task_id, "scene_id": task.scene_id, "status": "pending"}


@router.get("/tasks/{task_id}", summary="轮询单个任务结果")
def get_task_result(task_id: str) -> ImageResult:
    try:
        return generator.get_result(task_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── 批量 ─────────────────────────────────────────────────

@router.post("/batch/submit", summary="提交整本分镜脚本的批量生图")
def submit_batch(req: BatchSubmitRequest) -> dict:
    try:
        batch_id = batch_service.submit_script(
            script=req.script,
            style=req.style or "",
            aspect_ratio=req.aspect_ratio,
            concurrency=req.concurrency,
        )
        return {"batch_id": batch_id, "total": len(req.script.shots), "status": "running"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"批量提交失败: {e}")


@router.get("/batch/{batch_id}", summary="查询批量任务进度")
def get_batch_status(batch_id: str) -> dict:
    try:
        return batch_service.get_batch_status(batch_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
