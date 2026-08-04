from typing import List, Optional

from pydantic import BaseModel, Field

# 支持的长宽比（竖屏短视频优先）
ASPECT_RATIOS = ["9:16", "16:9", "1:1", "3:4", "4:3"]

# 任务状态流转：pending → generating → completed / failed
TASK_STATUSES = ["pending", "generating", "completed", "failed"]


class ImageTask(BaseModel):
    """单张图片生成任务"""

    scene_id: str = Field(..., description="对应分镜镜号（如 S001）")
    prompt: str = Field(..., description="正向生图提示词")
    negative_prompt: str = Field(
        default="低质量, 模糊, 变形, 多余手指, 水印, 文字, 签名",
        description="负向提示词",
    )
    style: str = Field("国漫水彩", description="画风，如：国漫水彩/韩漫厚涂/日系赛璐璐")
    aspect_ratio: str = Field("9:16", description="长宽比")


class ImageResult(BaseModel):
    """单任务生成结果"""

    task_id: str
    scene_id: str
    status: str = Field(..., description="pending/generating/completed/failed")
    progress: float = Field(0.0, description="进度 0-100")
    image_url: Optional[str] = Field(None, description="生成图片 URL，完成后有值")
    error: Optional[str] = Field(None, description="失败原因")


class BatchTaskItem(BaseModel):
    """批量任务中的单镜条目"""

    scene_id: str
    task_id: str
    status: str = "pending"
    image_url: Optional[str] = None
    error: Optional[str] = None


class BatchJob(BaseModel):
    """批量生成任务（一个剧本的所有分镜）"""

    batch_id: str
    status: str = Field("running", description="running/done")
    total: int = 0
    completed: int = 0
    failed: int = 0
    style: str = "国漫水彩"
    aspect_ratio: str = "9:16"
    tasks: List[BatchTaskItem] = Field(default_factory=list)

    @property
    def progress(self) -> float:
        if self.total == 0:
            return 0.0
        return round((self.completed + self.failed) / self.total * 100, 1)
