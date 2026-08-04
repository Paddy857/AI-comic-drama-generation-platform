"""TTS 抽象接口与共享常量"""

from abc import ABC, abstractmethod

from app.schemas.audio import AudioResult


class BaseTTSService(ABC):
    """TTS 服务抽象接口。

    后续接入任何真实 TTS 厂商（Edge-TTS / 阿里云 / ElevenLabs / CosyVoice 等），
    只需实现本抽象类并在 tts/__init__.py 的 get_tts_service() 工厂中注册即可，
    上层调用方（配音流程）无需任何改动。
    """

    name: str = "base"

    @abstractmethod
    def generate_audio(self, text: str, voice_id: str, emotion: str) -> AudioResult:
        """将文本合成为音频。

        Args:
            text: 待合成文本（对白/旁白）
            voice_id: 音色 ID（见 VOICES 音色库）
            emotion: 情绪标签，用于语速/语调控制（见 EMOTIONS）

        Returns:
            AudioResult: 含 audio_url、duration、字级别时间戳 timestamp_alignment
        """
        raise NotImplementedError


# 情绪枚举（与分镜脚本 Dialogue.emotion 保持一致）
EMOTIONS = ["平静", "开心", "愤怒", "悲伤", "紧张", "疑惑", "嘲讽", "惊喜"]

# 各情绪对应的语速系数（倍率，>1 快、<1 慢）
EMOTION_SPEED_FACTORS = {
    "平静": 1.0,
    "开心": 1.1,
    "愤怒": 1.2,
    "悲伤": 0.85,
    "紧张": 1.15,
    "疑惑": 1.0,
    "嘲讽": 1.1,
    "惊喜": 1.2,
}
