"""MockTTSService：模拟 TTS，不产生真实音频文件。

- audio_url：返回固定格式的演示路径，前端可直接用于 UI 联调
- duration：按文本字数估算（中文约 4.5 字/秒），并叠加情绪语速系数 + 基于文本哈希的
  伪随机抖动（保证同一文本多次调用结果稳定，便于前端对接）
- timestamp_alignment：按字符均匀切分生成字级别时间戳
"""

import hashlib

from app.schemas.audio import AudioResult, WordTimestamp
from app.services.tts.base import BaseTTSService, EMOTIONS, EMOTION_SPEED_FACTORS

CHARS_PER_SECOND = 4.5  # 中文正常语速（字/秒）


class MockTTSService(BaseTTSService):
    name = "mock"

    def generate_audio(self, text: str, voice_id: str, emotion: str) -> AudioResult:
        text = (text or "").strip()
        if not text:
            raise ValueError("待合成文本不能为空")
        if emotion not in EMOTIONS:
            raise ValueError(f"不支持的 emotion: {emotion}，可选: {'/'.join(EMOTIONS)}")

        duration = self._estimate_duration(text, emotion)

        # 字级别时间戳：按字符均匀分配时长（跳过空白）
        chars = [c for c in text if not c.isspace()]
        per = duration / max(len(chars), 1)
        alignment = [
            WordTimestamp(word=c, start=round(i * per, 3), end=round((i + 1) * per, 3))
            for i, c in enumerate(chars)
        ]

        return AudioResult(
            audio_url=self._mock_url(voice_id, text),
            duration=round(duration, 2),
            timestamp_alignment=alignment,
            text=text,
            voice_id=voice_id,
            emotion=emotion,
        )

    @staticmethod
    def _estimate_duration(text: str, emotion: str) -> float:
        """估算时长 = 字数 / 基础语速 / 情绪语速系数 × 伪随机抖动(0.92~1.08)。
        语速系数 >1 表示更快（愤怒/紧张）→ 时长更短；<1 表示更慢（悲伤）→ 时长更长。"""
        base = len(text) / CHARS_PER_SECOND
        base /= EMOTION_SPEED_FACTORS.get(emotion, 1.0)
        digest = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16)
        jitter = 0.92 + (digest % 17) / 100
        return base * jitter

    @staticmethod
    def _mock_url(voice_id: str, text: str) -> str:
        """固定格式演示 URL（Mock 不落盘真实音频）"""
        digest = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
        return f"/uploads/mock_tts/{voice_id}_{digest}.mp3"
