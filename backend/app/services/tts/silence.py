"""SilenceTTSService：跨平台兜底 TTS（非 macOS / 无真实 TTS 引擎的环境）。

- 用 ffmpeg 生成与"文本字数+情绪语速"估算时长一致的静音音频（anullsrc）
- 保证视频合成链路在任何平台都能正常出片（无声轨道，时长严格对齐）
- 需要真实配音时：macOS 用 say 引擎；或接入厂商 TTS API（见 README 配置说明）
"""

import hashlib
import os
import subprocess

from app.core.config import settings
from app.schemas.audio import AudioResult
from app.services.tts.base import BaseTTSService, EMOTION_SPEED_FACTORS

CHARS_PER_SECOND = 4.5  # 中文正常语速（字/秒）


class SilenceTTSService(BaseTTSService):
    name = "silence"

    def __init__(self):
        os.makedirs(settings.tts_upload_dir, exist_ok=True)

    def generate_audio(self, text: str, voice_id: str, emotion: str) -> AudioResult:
        text = (text or "").strip()
        if not text:
            raise ValueError("合成文本为空")
        duration = self._estimate_duration(text, emotion)
        digest = hashlib.md5(f"{text}|{voice_id}".encode()).hexdigest()[:12]
        rel_dir = os.path.relpath(settings.tts_upload_dir, settings.upload_dir)
        filename = f"{digest}.mp3"
        mp3_path = os.path.join(settings.tts_upload_dir, filename)

        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error",
             "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
             "-t", f"{duration:.2f}", "-b:a", "128k", mp3_path],
            check=True, capture_output=True, timeout=60,
        )

        return AudioResult(
            audio_url=f"/uploads/{rel_dir}/{filename}".replace(os.sep, "/"),
            duration=round(duration, 2),
            text=text,
            voice_id=voice_id,
            emotion=emotion,
        )

    @staticmethod
    def _estimate_duration(text: str, emotion: str) -> float:
        """时长估算 = 字数 / 基础语速 / 情绪系数 × 伪随机抖动（与 Mock 一致）"""
        base = len(text) / CHARS_PER_SECOND
        base /= EMOTION_SPEED_FACTORS.get(emotion, 1.0)
        digest = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16)
        jitter = 0.92 + (digest % 17) / 100
        return max(1.0, base * jitter)
