"""PollinationsTTSService：基于 Pollinations.ai 免费在线 TTS 的真实实现。

- 免注册、免 Key：GET https://text.pollinations.ai/{text}?model=openai-audio&voice={voice}
- 与文生图（PollinationsImageGenerator）同平台，统一为「免费在线 API」引擎
- 合成 mp3 落盘 uploads/tts/ 返回本地可访问 URL；时长以 ffprobe 实测为准
- 网络不可用/超时/限流时自动重试 3 次，仍失败则降级为静音音频兜底（保证流水线出片），
  并在日志中打印 warning，便于排查

接入方式：backend/.env 配置 TTS_ENGINE=pollinations（默认）。
"""

import hashlib
import logging
import os
import subprocess
import time
import urllib.parse
import urllib.request

from app.core.config import settings
from app.schemas.audio import AudioResult
from app.services.tts.base import BaseTTSService

logger = logging.getLogger("tts")

# 平台音色 ID -> Pollinations（OpenAI TTS）音色
VOICE_MAP = {
    "male_young": "echo",        # 男声 年轻
    "male_steady": "onyx",       # 男声 沉稳醇厚
    "female_gentle": "shimmer",  # 女声 温柔柔和
    "female_lively": "nova",     # 女声 明亮活泼
}

_MAX_RETRIES = 3
_MAX_TEXT_LEN = 1000  # 台词一般很短，防御性截断避免超长 URL


class PollinationsTTSService(BaseTTSService):
    name = "pollinations"

    def __init__(self):
        os.makedirs(settings.tts_upload_dir, exist_ok=True)

    def generate_audio(self, text: str, voice_id: str, emotion: str) -> AudioResult:
        text = (text or "").strip()
        if not text:
            raise ValueError("合成文本为空")
        voice = VOICE_MAP.get(voice_id, "shimmer")
        digest = hashlib.md5(f"{text}|{voice_id}|{emotion}".encode()).hexdigest()[:12]
        rel_dir = os.path.relpath(settings.tts_upload_dir, settings.upload_dir)
        filename = f"{digest}.mp3"
        audio_path = os.path.join(settings.tts_upload_dir, filename)

        url = self._build_url(text, voice)
        last_err = None
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                data = self._fetch(url)
                if not data:
                    raise RuntimeError("空响应")
                with open(audio_path, "wb") as f:
                    f.write(data)
                return AudioResult(
                    audio_url=f"/uploads/{rel_dir}/{filename}".replace(os.sep, "/"),
                    duration=self._probe_duration(audio_path),
                    text=text,
                    voice_id=voice_id,
                    emotion=emotion,
                )
            except Exception as e:
                last_err = str(e)
                if attempt < _MAX_RETRIES:
                    time.sleep(2 * attempt)
        # 全部失败：降级静音音频兜底，保证全流程可出片（与图片生成回落占位图一致）
        logger.warning("Pollinations TTS 合成失败(%s)，降级为静音音频", last_err)
        from app.services.tts.silence import SilenceTTSService
        return SilenceTTSService().generate_audio(text, voice_id, emotion)

    def _build_url(self, text: str, voice: str) -> str:
        base = settings.pollinations_tts_base_url.rstrip("/")
        return f"{base}/{urllib.parse.quote(text[:_MAX_TEXT_LEN])}?model=openai-audio&voice={voice}"

    def _fetch(self, url: str) -> bytes:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 AIGC-Manju/1.0"},
        )
        with urllib.request.urlopen(req, timeout=settings.pollinations_tts_timeout) as resp:
            return resp.read()

    @staticmethod
    def _probe_duration(path: str) -> float:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=30,
        ).stdout.strip()
        return round(float(out), 3) if out else 0.0
