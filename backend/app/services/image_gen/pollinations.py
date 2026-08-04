"""PollinationsImageGenerator：基于 Pollinations.ai 免费文生图服务的真实生成器。

- submit_task：立即返回 task_id，后台线程调用 Pollinations API 出图
- 生成成功后下载图片到本地 uploads/image_gen/ 目录，返回本地可访问 URL（避免每次请求重新出图）
- 失败自动重试 3 次；全部失败则用 Pillow 生成带提示词的占位图回落，保证流水线不中断

线程安全：内部用锁保护任务存储，支持并发提交。
"""

import os
import threading
import time
import urllib.parse
import urllib.request
import uuid

from PIL import Image, ImageDraw, ImageFont

from app.core.config import settings
from app.schemas.image import ImageResult, ImageTask
from app.services.image_gen.base import BaseImageGenerator

# 长宽比 -> 像素尺寸（竖屏短视频优先）
_ASPECT_SIZE = {
    "9:16": (720, 1280),
    "16:9": (1280, 720),
    "1:1": (1024, 1024),
    "3:4": (768, 1024),
    "4:3": (1024, 768),
}

_MAX_RETRIES = 4


class PollinationsImageGenerator(BaseImageGenerator):
    name = "pollinations"

    def __init__(self):
        self._store = {}          # task_id -> ImageResult
        self._meta = {}           # task_id -> ImageTask
        self._lock = threading.Lock()
        os.makedirs(settings.image_gen_upload_dir, exist_ok=True)

    # ── 接口实现 ──────────────────────────────────────────

    def submit_task(self, task: ImageTask) -> str:
        task_id = f"img_{uuid.uuid4().hex[:12]}"
        result = ImageResult(
            task_id=task_id, scene_id=task.scene_id, status="pending", progress=0.0
        )
        with self._lock:
            self._store[task_id] = result
            self._meta[task_id] = task
        threading.Thread(target=self._generate, args=(task_id,), daemon=True).start()
        return task_id

    def get_result(self, task_id: str) -> ImageResult:
        with self._lock:
            result = self._store.get(task_id)
        if not result:
            raise KeyError(f"任务不存在: {task_id}")
        return result

    # ── 真实生成逻辑 ──────────────────────────────────────

    def _generate(self, task_id: str) -> None:
        task = self._meta[task_id]
        width, height = _ASPECT_SIZE.get(task.aspect_ratio, (720, 1280))
        url = self._build_url(task.prompt, width, height, task_id)

        for attempt in range(1, _MAX_RETRIES + 1):
            self._update(task_id, status="generating", progress=round(attempt / _MAX_RETRIES * 60, 1))
            try:
                data = self._fetch(url)
                if not data:
                    raise RuntimeError("空响应")
                local_path = self._save(task_id, data, width, height)
                self._update(
                    task_id,
                    status="completed",
                    progress=100,
                    image_url=f"/uploads/{local_path}",
                )
                return
            except Exception as e:
                last_err = str(e)
                if attempt < _MAX_RETRIES:
                    time.sleep(3 * attempt)  # 限流 500 时退避重试
        # 全部重试失败：回落本地占位图，标记失败原因但保留可访问图片
        fallback_url = self._fallback(task_id, task)
        self._update(
            task_id,
            status="failed",
            progress=100,
            image_url=fallback_url,
            error=f"Pollinations 生成失败: {last_err}，已回落占位图",
        )

    def _build_url(self, prompt: str, width: int, height: int, task_id: str) -> str:
        """构造 Pollinations 图片生成 URL（免费文生图服务，过长 prompt 易 500，先截断）"""
        seed = int(hashlib_md5(task_id)[:8], 16) % 999999  # 大 seed 会导致服务端 500，限制范围
        base = settings.pollinations_base_url.rstrip("/")
        trimmed = prompt.strip()[:120]
        return (
            f"{base}/prompt/{urllib.parse.quote(trimmed)}"
            f"?width={width}&height={height}&nologo=true&seed={seed}"
        )

    def _fetch(self, url: str) -> bytes:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 AIGC-Manju/1.0"},
        )
        with urllib.request.urlopen(req, timeout=settings.pollinations_timeout) as resp:
            return resp.read()

    def _save(self, task_id: str, data: bytes, width: int, height: int) -> str:
        """保存并统一缩放到目标尺寸（服务返回图为 576x1024 等固定比例）"""
        from io import BytesIO

        img = Image.open(BytesIO(data)).convert("RGB")
        if img.size != (width, height):
            img = img.resize((width, height), Image.LANCZOS)
        rel_dir = os.path.relpath(settings.image_gen_upload_dir, settings.upload_dir)
        rel_path = os.path.join(rel_dir, f"{task_id}.jpg")
        abs_path = os.path.join(settings.image_gen_upload_dir, f"{task_id}.jpg")
        img.save(abs_path, "JPEG", quality=88)
        return rel_path.replace(os.sep, "/")

    def _fallback(self, task_id: str, task: ImageTask) -> str:
        """Pollinations 不可用时生成一张带提示词的本地占位图"""
        width, height = _ASPECT_SIZE.get(task.aspect_ratio, (720, 1280))
        img = Image.new("RGB", (width, height), "#1e1b4b")
        draw = ImageDraw.Draw(img)
        # 垂直渐变底色
        for y in range(height):
            t = y / height
            color = (
                int(30 + 20 * t), int(27 + 16 * t), int(75 + 40 * t),
            )
            draw.line([(0, y), (width, y)], fill=color)
        try:
            font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 40)
        except OSError:
            font = ImageFont.load_default()
        text = f"[占位图] {task.scene_id}\n{task.prompt[:40]}"
        draw.multiline_text(
            (width // 2, height // 2),
            text,
            fill="#ffffff",
            font=font,
            anchor="mm",
            spacing=12,
            align="center",
        )
        rel_path = os.path.join(
            os.path.relpath(settings.image_gen_upload_dir, settings.upload_dir),
            f"{task_id}_fallback.jpg",
        ).replace(os.sep, "/")
        img.save(os.path.join(settings.image_gen_upload_dir, f"{task_id}_fallback.jpg"), "JPEG")
        return f"/uploads/{rel_path}"

    def _update(self, task_id: str, status: str, progress: float, image_url=None, error=None) -> None:
        with self._lock:
            r = self._store[task_id]
            r.status = status
            r.progress = progress
            if image_url:
                r.image_url = image_url
            if error:
                r.error = error


def hashlib_md5(s: str) -> str:
    import hashlib
    return hashlib.md5(s.encode()).hexdigest()
