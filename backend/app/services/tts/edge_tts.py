"""EdgeTTSService：微软 Edge-TTS（免费）接入预留实现。

接入步骤（后续有需要时启用）：
1. 安装依赖：pip install edge-tts
2. 将 backend/.env 中的 TTS_ENGINE 改为 edge
3. 可选：在下方 VOICE_MAP 中补充 edge-tts 音色 ID（如 zh-CN-YunxiNeural 少年 / zh-CN-XiaoxiaoNeural 女声）
4. 真实调用时，uncomment 下方被注释的 edge_tts 逻辑即可

edge-tts 音色 ID 参考：
- zh-CN-XiaoxiaoNeural  女声 温柔（推荐女角）
- zh-CN-YunxiNeural    男声 少年音（推荐男角）
- zh-CN-YunyangNeural  男声 新闻/沉稳（推荐反派/旁白）
- zh-CN-XiaoyiNeural   女声 活泼
"""

import asyncio
import os

from app.core.config import settings
from app.schemas.audio import AudioResult, WordTimestamp
from app.services.tts.base import BaseTTSService

VOICE_MAP = {
    "male_young": "zh-CN-YunxiNeural",
    "male_steady": "zh-CN-YunyangNeural",
    "female_gentle": "zh-CN-XiaoxiaoNeural",
    "female_lively": "zh-CN-XiaoyiNeural",
}


class EdgeTTSService(BaseTTSService):
    """基于微软 Edge-TTS 的实现（免费、无 Key）。

    注意：Edge-TTS 为 async API，此处用 asyncio.run 包装成同步接口以符合抽象基类签名。
    """

    name = "edge"

    def generate_audio(self, text: str, voice_id: str, emotion: str) -> AudioResult:
        # import edge_tts  # pip install edge-tts
        edge_voice = VOICE_MAP.get(voice_id, VOICE_MAP["female_gentle"])

        os.makedirs(settings.tts_upload_dir, exist_ok=True)
        audio_path = os.path.join(settings.tts_upload_dir, f"{voice_id}.mp3")

        async def _synth() -> list:
            # communicate = edge_tts.Communicate(text, edge_voice)
            # await communicate.save(audio_path)
            # # 逐字时间戳（edge-tts 通过 stream() 逐字返回）
            # timestamps = []
            # async for chunk in communicate.stream():
            #     if chunk["type"] == "WordBoundary":
            #         timestamps.append(WordTimestamp(
            #             word=chunk["text"], start=chunk["offset"] / 1e7, end=(chunk["offset"] + chunk["duration"]) / 1e7,
            #         ))
            return []  # TODO: 接入后替换

        timestamps = asyncio.run(_synth())
        return AudioResult(
            audio_url=f"/{audio_path}",
            duration=0.0,  # TODO: 用 pydub/ffprobe 读取真实时长
            timestamp_alignment=timestamps,
            text=text,
            voice_id=voice_id,
            emotion=emotion,
        )
