"""SayTTSService：基于 macOS 自带 say 命令的本地离线 TTS（无需网络与任何 API）。

- 使用系统离线中文语音（默认 Tingting 女声），合成 aiff 后经 ffmpeg 转 mp3
- 语速按情绪系数调整（say -r，words per minute）：悲伤变慢、愤怒/惊喜变快
- 说明：say 不提供字级时间戳，字幕由视频合成层按整句烧录
"""

import hashlib
import os
import subprocess

from app.core.config import settings
from app.schemas.audio import AudioResult
from app.services.tts.base import BaseTTSService, EMOTION_SPEED_FACTORS

_BASE_RATE = 175  # say 默认语速（words per minute）

# 平台音色 ID -> macOS say 语音（仅使用离线内置的中文语音）
_VOICE_MAP = {
    "male_young": "Sinji",
    "male_steady": "Sinji",
    "female_gentle": "Tingting",
    "female_lively": "Meijia",
}


class SayTTSService(BaseTTSService):
    name = "say"

    def __init__(self, default_voice: str = "Tingting"):
        self.default_voice = default_voice
        os.makedirs(settings.tts_upload_dir, exist_ok=True)

    def generate_audio(self, text: str, voice_id: str, emotion: str) -> AudioResult:
        text = (text or "").strip()
        if not text:
            raise ValueError("合成文本为空")
        voice = _VOICE_MAP.get(voice_id, self.default_voice)
        digest = hashlib.md5(f"{text}|{voice_id}|{emotion}".encode()).hexdigest()[:12]
        rel_dir = os.path.relpath(settings.tts_upload_dir, settings.upload_dir)
        filename = f"{digest}.mp3"
        mp3_path = os.path.join(settings.tts_upload_dir, filename)
        aiff_path = os.path.join(settings.tts_upload_dir, f"{digest}.aiff")

        factor = EMOTION_SPEED_FACTORS.get(emotion, 1.0)
        rate = max(90, min(300, int(_BASE_RATE * factor)))
        try:
            subprocess.run(
                ["say", "-v", voice, "-r", str(rate), "-o", aiff_path, text],
                check=True, capture_output=True, timeout=180,
            )
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-i", aiff_path,
                 "-b:a", "160k", mp3_path],
                check=True, capture_output=True, timeout=120,
            )
        finally:
            if os.path.exists(aiff_path):
                os.remove(aiff_path)

        return AudioResult(
            audio_url=f"/uploads/{rel_dir}/{filename}".replace(os.sep, "/"),
            duration=self._probe_duration(mp3_path),
            text=text,
            voice_id=voice_id,
            emotion=emotion,
        )

    @staticmethod
    def _probe_duration(path: str) -> float:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=30,
        ).stdout.strip()
        return round(float(out), 3) if out else 0.0
