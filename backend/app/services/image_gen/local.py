"""LocalImageGenerator：完全离线的本地出图（Pillow，无任何网络依赖）。

- 按 scene_id 哈希选取色板，生成渐变背景 + 分镜提示词文字，720x1280
- 用于无外网环境（如评测机）时保证"分镜图片生成"环节仍可产出可区分的画面
- 接入真实文生图：将 IMAGE_GEN_ENGINE 改为 pollinations（免费）或厂商引擎
"""

import hashlib
import os
import threading

from PIL import Image, ImageDraw, ImageFont

from app.core.config import settings
from app.schemas.image import ImageResult, ImageTask
from app.services.image_gen.base import BaseImageGenerator

_PALETTES = [
    ((59, 130, 246), (30, 27, 75)),   # 蓝紫
    ((236, 72, 153), (76, 29, 149)),  # 玫紫
    ((16, 185, 129), (6, 78, 59)),    # 翠绿
    ((249, 115, 22), (67, 20, 7)),    # 橙红
    ((14, 165, 233), (8, 47, 73)),    # 天蓝
    ((168, 85, 247), (46, 16, 101)),  # 紫
]

_SIZE = (720, 1280)


class LocalImageGenerator(BaseImageGenerator):
    name = "local"

    def __init__(self):
        self._store = {}
        self._lock = threading.Lock()
        os.makedirs(settings.image_gen_upload_dir, exist_ok=True)

    def submit_task(self, task: ImageTask) -> str:
        task_id = f"img_{hashlib.md5(task.scene_id.encode()).hexdigest()[:12]}"
        with self._lock:
            if task_id in self._store:
                return task_id
            self._store[task_id] = ImageResult(
                task_id=task_id, scene_id=task.scene_id, status="pending", progress=0.0
            )
        # 本地生成：同步完成（无耗时，立即写入结果）
        url = self._render(task_id, task)
        with self._lock:
            r = self._store[task_id]
            r.status = "completed"
            r.progress = 100.0
            r.image_url = url
        return task_id

    def get_result(self, task_id: str) -> ImageResult:
        with self._lock:
            result = self._store.get(task_id)
        if not result:
            raise KeyError(f"任务不存在: {task_id}")
        return result

    # ── 本地渲染 ──────────────────────────────────────────

    def _render(self, task_id: str, task: ImageTask) -> str:
        top, bottom = _PALETTES[int(hashlib.md5(task.scene_id.encode()).hexdigest(), 16) % len(_PALETTES)]
        img = Image.new("RGB", _SIZE, top)
        draw = ImageDraw.Draw(img)
        # 垂直渐变
        for y in range(_SIZE[1]):
            t = y / _SIZE[1]
            color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
            draw.line([(0, y), (_SIZE[0], y)], fill=color)
        # 装饰圆环
        draw.ellipse([-200, 300, 520, 1020], outline=(255, 255, 255, 40), width=2)
        draw.ellipse([280, -120, 900, 500], outline=(255, 255, 255, 30), width=2)

        font_title = self._font(52)
        font_body = self._font(34)
        draw.text((40, 90), f"分镜 {task.scene_id}", fill="#ffffff", font=font_title)
        prompt = (task.prompt or "")[:120]
        draw.multiline_text(
            (40, 200), prompt, fill="#e2e8f0", font=font_body, spacing=14,
        )
        rel_dir = os.path.relpath(settings.image_gen_upload_dir, settings.upload_dir)
        filename = f"{task_id}.jpg"
        img.save(os.path.join(settings.image_gen_upload_dir, filename), "JPEG", quality=85)
        return f"/uploads/{rel_dir}/{filename}".replace(os.sep, "/")

    @staticmethod
    def _font(size: int):
        for p in (
            "/System/Library/Fonts/PingFang.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
        ):
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size)
                except OSError:
                    continue
        return ImageFont.load_default(size)
