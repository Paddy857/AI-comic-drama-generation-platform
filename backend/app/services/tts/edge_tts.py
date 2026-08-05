"""EdgeTTSService：基于微软 Edge-TTS 的免费高质量中文 TTS 实现。

- 免费、无需 Key，中文音色丰富（Xiaoxiao 温柔女声 / Yunxi 少年男声等）
- 依赖：pip install edge-tts（按需安装，未写入 requirements.txt）
- 情绪语速：通过 rate 参数（+10% / -15%）映射情绪系数
- 网络失败/异常时降级为静音音频兜底，保证全流程可出片

接入方式：backend/.env 配置 TTS_ENGINE=edge。
"""

import asyncio
import concurrent.futures
import hashlib
import logging
import os
import subprocess

from app.core.config import settings
from app.schemas.audio import AudioResult
from app.services.tts.base import BaseTTSService, EMOTION_SPEED_FACTORS

logger = logging.getLogger("tts")

VOICE_MAP = {
    "male_young": "zh-CN-YunxiNeural",        # 少年音
    "male_steady": "zh-CN-YunyangNeural",     # 沉稳男声
    "female_gentle": "zh-CN-XiaoxiaoNeural",  # 温柔女声
    "female_lively": "zh-CN-XiaoyiNeural",    # 活泼女声
}


def _run_async(coro):
    """安全执行 async 协程：无事件循环时直接 run，已有事件循环时移到新线程隔离"""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        return ex.submit(asyncio.run, coro).result()


class EdgeTTSService(BaseTTSService):
    name = "edge"

    def generate_audio(self, text: str, voice_id: str, emotion: str) -> AudioResult:
        text = (text or "").strip()
        if not text:
            raise ValueError("合成文本为空")
        try:
            import edge_tts  # pip install edge-tts
        except ImportError:
            raise RuntimeError("TTS_ENGINE=edge 需要安装依赖：pip install edge-tts（见 README 模型 API 配置）")

        edge_voice = VOICE_MAP.get(voice_id, VOICE_MAP["female_gentle"])
        factor = EMOTION_SPEED_FACTORS.get(emotion, 1.0)
        rate = f"{(factor - 1.0) * 100:+.0f}%"  # 愤怒 +20% 更快 / 悲伤 -15% 更慢

        os.makedirs(settings.tts_upload_dir, exist_ok=True)
        digest = hashlib.md5(f"{text}|{voice_id}|{emotion}".encode()).hexdigest()[:12]
        rel_dir = os.path.relpath(settings.tts_upload_dir, settings.upload_dir)
        filename = f"{digest}.mp3"
        audio_path = os.path.join(settings.tts_upload_dir, filename)

        try:
            _run_async(self._synth(edge_tts, text, edge_voice, rate, audio_path))
        except Exception as e:
            logger.warning("Edge-TTS 合成失败(%s)，降级为静音音频", e)
            from app.services.tts.silence import SilenceTTSService
            return SilenceTTSService().generate_audio(text, voice_id, emotion)

        return AudioResult(
            audio_url=f"/uploads/{rel_dir}/{filename}".replace(os.sep, "/"),
            duration=self._probe_duration(audio_path),
            text=text,
            voice_id=voice_id,
            emotion=emotion,
        )

    @staticmethod
    async def _synth(edge_tts, text: str, voice: str, rate: str, path: str) -> None:
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        await communicate.save(path)

    @staticmethod
    def _probe_duration(path: str) -> float:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=30,
        ).stdout.strip()
        return round(float(out), 3) if out else 0.0
