"""MockImageGenerator：模拟异步文生图。

- submit_task：立即返回 task_id，后台线程模拟生成（2-6 秒，逐步推进进度）
- get_result：返回当前状态（pending/generating/completed/failed）
- 完成后返回 Unsplash 占位图 URL（按 scene_id 哈希稳定选取，同一场景多次生成 URL 不变）

线程安全：内部用锁保护任务存储，支持并发提交。
"""

import hashlib
import random
import threading
import time
import uuid

from app.schemas.image import ImageResult, ImageTask
from app.services.image_gen.base import BaseImageGenerator

# Unsplash 占位图库（摄影图，按场景哈希选取保证稳定）
_UNSPLASH_IDS = [
    "1506905925349-21dda85d9c40",  # 山景
    "1495954484750-af469f2f9be5",  # 城市夜景
    "1518684079-3c830dcef090",     # 街道
    "1508615039623-a25605d2b022",  # 星空
    "1470071459604-3b5ec3a7fe05",  # 自然
    "1515378791036-0648a3ef77b2",  # 建筑
    "1477959858617-67f85cf4f1df",  # 城市
    "1441974231531-c6227db76b6e",  # 森林
    "1518709268805-4e9042af9f23",  # 霓虹
    "1500530855697-b586d89ba3ee",  # 水面
]


class MockImageGenerator(BaseImageGenerator):
    name = "mock"

    def __init__(self, min_seconds: float = 2.0, max_seconds: float = 6.0):
        self.min_seconds = min_seconds
        self.max_seconds = max_seconds
        self._store = {}          # task_id -> ImageResult
        self._meta = {}           # task_id -> (scene_id, prompt)
        self._lock = threading.Lock()

    # ── 接口实现 ──────────────────────────────────────────

    def submit_task(self, task: ImageTask) -> str:
        task_id = f"img_{uuid.uuid4().hex[:12]}"
        result = ImageResult(
            task_id=task_id, scene_id=task.scene_id, status="pending", progress=0.0
        )
        with self._lock:
            self._store[task_id] = result
            self._meta[task_id] = (task.scene_id, task.prompt)
        threading.Thread(
            target=self._simulate, args=(task_id,), daemon=True
        ).start()
        return task_id

    def get_result(self, task_id: str) -> ImageResult:
        with self._lock:
            result = self._store.get(task_id)
        if not result:
            raise KeyError(f"任务不存在: {task_id}")
        return result

    # ── Mock 模拟逻辑 ─────────────────────────────────────

    def _simulate(self, task_id: str) -> None:
        scene_id, prompt = self._meta[task_id]
        total = random.uniform(self.min_seconds, self.max_seconds)
        steps = 5
        for i in range(1, steps + 1):
            time.sleep(total / steps)
            progress = round(i / steps * 100, 1)
            with self._lock:
                r = self._store[task_id]
                r.status = "generating" if i < steps else "completed"
                r.progress = progress
                if i == steps:
                    r.image_url = self._placeholder_url(scene_id)
        with self._lock:
            self._store[task_id].image_url = self._placeholder_url(scene_id)

    @staticmethod
    def _placeholder_url(scene_id: str) -> str:
        """按 scene_id 稳定选取一张 Unsplash 占位图（竖屏 720x1280）"""
        idx = int(hashlib.md5(scene_id.encode()).hexdigest(), 16) % len(_UNSPLASH_IDS)
        photo_id = _UNSPLASH_IDS[idx]
        return f"https://images.unsplash.com/photo-{photo_id}?w=720&h=1280&fit=crop"
