"""画面生成调度器包

接入真实文生图厂商（Kolors / 混元DiT / 通义万相 / Pollinations 等）：
1. 在 image_gen/ 下新建实现文件，继承 BaseImageGenerator
2. 在 get_image_generator() 工厂按引擎名注册
"""

from app.core.config import settings
from app.services.image_gen.base import BaseImageGenerator
from app.services.image_gen.batch import BatchImageService
from app.services.image_gen.mock import MockImageGenerator


def get_image_generator() -> BaseImageGenerator:
    """按配置返回生成器实现。
    - pollinations（默认）：免费真实文生图（需外网，失败自动回落占位图）
    - local：完全离线（Pillow 本地渲染，无网络也能出图，适合评测环境）
    - mock：本地模拟（返回占位 URL）
    """
    engine = settings.image_gen_engine.lower()
    if engine == "pollinations":
        from app.services.image_gen.pollinations import PollinationsImageGenerator

        return PollinationsImageGenerator()
    if engine == "local":
        from app.services.image_gen.local import LocalImageGenerator

        return LocalImageGenerator()
    return MockImageGenerator()
