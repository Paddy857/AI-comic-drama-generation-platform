from typing import List, Optional

from pydantic import BaseModel, Field


class WordTimestamp(BaseModel):
    """字级别时间戳，用于字幕逐字对齐"""

    word: str = Field(..., description="单个字符/词")
    start: float = Field(..., description="开始时间（秒）")
    end: float = Field(..., description="结束时间（秒）")


class AudioResult(BaseModel):
    """TTS 合成结果"""

    audio_url: str = Field(..., description="音频链接（可播放的 URL 或静态文件路径）")
    duration: float = Field(..., description="音频总时长（秒）")
    timestamp_alignment: List[WordTimestamp] = Field(
        default_factory=list, description="字级别时间戳，用于字幕对齐"
    )
    text: str = Field(..., description="合成文本")
    voice_id: str = Field(..., description="使用的音色 ID")
    emotion: str = Field(..., description="情绪标签")


class VoiceInfo(BaseModel):
    """音色档案"""

    id: str
    name: str
    gender: str = "女"
    age: str = "青年"
    style: str = "现代"
    description: str = ""
    emotions: List[str] = Field(default_factory=list, description="支持的情绪标签")
