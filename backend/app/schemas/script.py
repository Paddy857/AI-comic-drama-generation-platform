from typing import List, Optional

from pydantic import BaseModel, Field


class Dialogue(BaseModel):
    """单条对白，emotion 用于后期 TTS 配音情绪控制"""

    speaker: str = Field(..., description="说话角色名")
    line: str = Field(..., description="台词内容")
    emotion: str = Field(
        ..., description="情绪标签（用于配音）：平静/开心/愤怒/悲伤/紧张/疑惑/嘲讽/惊喜"
    )


class Scene(BaseModel):
    """单个镜头的画面设定"""

    scene_id: str = Field(..., description="镜号，如 S001")
    bg_prompt: str = Field(..., description="背景生图提示词，描述场景/构图/光影/氛围")
    character_prompts: List[str] = Field(
        default_factory=list,
        description="角色生图提示词，每个出场角色一条，含外貌/服装/表情/动作",
    )
    camera_angle: str = Field(..., description="镜头视角，如：平视全景/俯拍特写/低机位仰拍/过肩中景")
    location: Optional[str] = Field(None, description="地点")
    time_of_day: Optional[str] = Field(None, description="时间段：日/夜/晨/黄昏")
    description: Optional[str] = Field(None, description="画面内容文字描述")


class Shot(BaseModel):
    """一个分镜 = 画面(Scene) + 对白/旁白"""

    shot_id: str = Field(..., description="镜号，如 S001")
    scene: Scene
    dialogues: List[Dialogue] = Field(default_factory=list, description="本镜对白列表")
    narration: Optional[str] = Field(None, description="旁白，无旁白为 null")
    duration_sec: float = Field(4.0, description="预估时长（秒）")
    mood: Optional[str] = Field(None, description="本镜情绪基调")


class ShotScript(BaseModel):
    """完整分镜脚本：小说 → 分镜 的转换输出"""

    title: str = Field(..., description="作品标题")
    style: Optional[str] = Field(None, description="画风，如：国漫水彩/韩漫厚涂")
    total_shots: int = Field(..., description="镜头总数")
    shots: List[Shot] = Field(..., description="全部镜头")


class ScriptConvertRequest(BaseModel):
    """小说转分镜 请求体"""

    novel: str = Field(..., description="小说原文（1000-10000字效果最佳）")
    title: Optional[str] = Field(None, description="作品标题，缺省自动生成")
    style: Optional[str] = Field(None, description="目标画风")
    target_shots: Optional[int] = Field(None, ge=4, le=30, description="目标镜头数，缺省按文本长度自动计算")
