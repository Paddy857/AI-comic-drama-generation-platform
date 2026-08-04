"""BaseImageGenerator：图片生成器抽象接口

后续接入真实文生图厂商（Kolors / 混元DiT / 通义万相 / SD-WebUI 等）时，
实现本抽象类并在工厂中注册即可，上层调度器（BatchImageService）无需改动。
"""

from abc import ABC, abstractmethod

from app.schemas.image import ImageResult, ImageTask


class BaseImageGenerator(ABC):
    name: str = "base"

    @abstractmethod
    def submit_task(self, task: ImageTask) -> str:
        """异步提交生成任务，立即返回 task_id（生成在后台进行）。"""
        raise NotImplementedError

    @abstractmethod
    def get_result(self, task_id: str) -> ImageResult:
        """按 task_id 轮询任务结果（支持 pending/generating/completed/failed 状态）。"""
        raise NotImplementedError
