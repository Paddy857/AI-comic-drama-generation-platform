"""BatchImageService：批量画面生成调度器。

接收一个完整分镜脚本（ShotScript），为每个镜头构建 ImageTask，
通过线程池并发提交，并统一管理整批任务的进度与结果。

调用方只需两步：
    batch_id = svc.submit_script(script, style="国漫水彩")
    status   = svc.get_batch_status(batch_id)   # 轮询直到 status == done

说明：任务状态存于进程内存，单实例部署够用；多实例部署时需将存储替换为 Redis/DB。
"""

import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Lock, Semaphore
from typing import Optional

from app.schemas.image import BatchJob, BatchTaskItem, ImageTask
from app.schemas.script import ShotScript
from app.services.image_gen.base import BaseImageGenerator
from app.services.image_gen.mock import MockImageGenerator

DEFAULT_NEGATIVE = "低质量, 模糊, 变形, 多余手指, 水印, 文字, 签名"


class BatchImageService:
    def __init__(self, generator: Optional[BaseImageGenerator] = None):
        self.generator = generator or MockImageGenerator()
        self._batches = {}   # batch_id -> BatchJob
        self._lock = Lock()
        self._executor = ThreadPoolExecutor(
            max_workers=8, thread_name_prefix="img-batch"
        )

    # ── 对外接口 ──────────────────────────────────────────

    def submit_script(
        self,
        script: ShotScript,
        style: str = "",
        aspect_ratio: str = "9:16",
        concurrency: int = 4,
    ) -> str:
        """并发提交剧本中所有分镜的生图任务，返回 batch_id。"""
        batch_id = f"batch_{uuid.uuid4().hex[:10]}"
        resolved_style = style or script.style or "国漫水彩"

        job = BatchJob(
            batch_id=batch_id,
            style=resolved_style,
            aspect_ratio=aspect_ratio,
            total=len(script.shots),
        )
        for shot in script.shots:
            job.tasks.append(
                BatchTaskItem(scene_id=shot.scene.scene_id, task_id="", status="pending")
            )
        with self._lock:
            self._batches[batch_id] = job

        semaphore = Semaphore(max(1, concurrency))
        for item, shot in zip(job.tasks, script.shots):
            task = ImageTask(
                scene_id=item.scene_id,
                prompt=self._build_prompt(shot.scene, resolved_style),
                negative_prompt=DEFAULT_NEGATIVE,
                style=resolved_style,
                aspect_ratio=aspect_ratio,
            )
            self._executor.submit(self._run_task_worker, batch_id, item, task, semaphore)
        return batch_id

    def submit_prompts(
        self,
        tasks: List[ImageTask],
        concurrency: int = 4,
    ) -> str:
        """并发提交一组现成的 ImageTask（prompt 已由调用方构造好），返回 batch_id。

        与 submit_script 的区别：不依赖 ShotScript，适合模板/自由创作链路直接喂入。
        """
        if not tasks:
            raise ValueError("tasks 不能为空")
        batch_id = f"batch_{uuid.uuid4().hex[:10]}"
        first = tasks[0]
        job = BatchJob(
            batch_id=batch_id,
            style=first.style or "",
            aspect_ratio=first.aspect_ratio or "9:16",
            total=len(tasks),
        )
        for t in tasks:
            job.tasks.append(
                BatchTaskItem(scene_id=t.scene_id, task_id="", status="pending")
            )
        with self._lock:
            self._batches[batch_id] = job

        semaphore = Semaphore(max(1, concurrency))
        for item, task in zip(job.tasks, tasks):
            self._executor.submit(self._run_task_worker, batch_id, item, task, semaphore)
        return batch_id

    def get_batch_status(self, batch_id: str) -> dict:
        """批量任务进度：total/completed/failed/pending/progress"""
        with self._lock:
            job = self._batches.get(batch_id)
            if not job:
                raise KeyError(f"批量任务不存在: {batch_id}")
            job.completed = sum(1 for t in job.tasks if t.status == "completed")
            job.failed = sum(1 for t in job.tasks if t.status == "failed")
            job.status = "done" if job.completed + job.failed == job.total else "running"
            data = job.model_dump()
            data["progress"] = job.progress  # progress 为 property，需手动序列化
            return data

    # ── 内部工具 ──────────────────────────────────────────

    def _run_task_worker(self, batch_id: str, item: BatchTaskItem, task: ImageTask, semaphore: Semaphore) -> None:
        """单个镜头的完整执行：提交 -> 轮询 -> 同步结果（受信号量并发约束）。"""
        with semaphore:
            task_id = self.generator.submit_task(task)
            item.task_id = task_id
            self._update(batch_id, item.scene_id, status="generating")
            while True:
                result = self.generator.get_result(task_id)
                if result.status == "completed":
                    self._update(
                        batch_id, item.scene_id, status="completed", url=result.image_url
                    )
                    return
                if result.status == "failed":
                    self._update(
                        batch_id, item.scene_id, status="failed",
                        url=result.image_url, error=result.error or "生成失败",
                    )
                    return
                time.sleep(0.5)

    @staticmethod
    def _build_prompt(scene, style: str) -> str:
        """由 Scene 构建正向提示词：画面描述 + 背景提示 + 角色提示 + 风格。"""
        parts = []
        if scene.description:
            parts.append(scene.description)
        parts.append(scene.bg_prompt)
        for cp in scene.character_prompts:
            parts.append(cp)
        parts.append(f"风格: {style}")
        return "，".join(parts)

    def _update(
        self,
        batch_id: str,
        scene_id: str,
        status: str,
        url: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """线程安全地同步单镜状态到 batch 存储中的对应条目。"""
        with self._lock:
            job = self._batches.get(batch_id)
            if not job:
                return
            for t in job.tasks:
                if t.scene_id == scene_id:
                    t.status = status
                    if url:
                        t.image_url = url
                    if error:
                        t.error = error
                    return
