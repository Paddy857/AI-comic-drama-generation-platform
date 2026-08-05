"""TTS 服务工厂：根据配置 TTS_ENGINE 返回对应实现（环境变量一键切换，无需改代码）。

免费引擎（跑通全流程，开箱即用）：
- pollinations（默认）：Pollinations.ai 免费在线 TTS，免 Key 需外网；失败自动降级静音
- edge：微软 Edge-TTS，免费高质量中文，需 pip install edge-tts
- silence：静音音频（跨平台兜底，无配音但能出片）

本机演示：
- say：macOS 系统离线语音（仅本机）

真实厂商引擎（申请到 API 后接入，见 README「模型 API 配置」）：
- aliyun / cosyvoice / volcengine / elevenlabs：按下方说明实现子类并注册即可，
  上层配音流程（generate 状态机）无需任何改动
"""

from app.core.config import settings
from app.schemas.audio import VoiceInfo
from app.services.tts.base import BaseTTSService, EMOTIONS
from app.services.tts.mock import MockTTSService

# 平台音色库（跨引擎统一 ID；各引擎实现内部映射到自身音色 ID）
VOICES = [
    VoiceInfo(id="male_young", name="少年音", gender="男", age="少年", style="现代",
              description="清爽年轻男声，适合男主/热血角色",
              emotions=EMOTIONS),
    VoiceInfo(id="male_steady", name="沉稳男声", gender="男", age="中年", style="成熟",
              description="低沉沉稳男声，适合反派/权威/旁白",
              emotions=EMOTIONS),
    VoiceInfo(id="female_gentle", name="温柔女声", gender="女", age="青年", style="甜美",
              description="温柔细腻女声，适合女主/甜宠角色",
              emotions=EMOTIONS),
    VoiceInfo(id="female_lively", name="活泼少女", gender="女", age="少女", style="可爱",
              description="活泼俏皮少女音，适合配角/萌系角色",
              emotions=EMOTIONS),
]


def get_tts_service() -> BaseTTSService:
    """按 backend/.env 中 TTS_ENGINE 配置返回 TTS 实现。"""
    engine = settings.tts_engine.lower()
    if engine == "pollinations":
        from app.services.tts.pollinations_tts import PollinationsTTSService
        return PollinationsTTSService()
    if engine == "edge":
        from app.services.tts.edge_tts import EdgeTTSService
        return EdgeTTSService()
    if engine == "say":
        from app.services.tts.say import SayTTSService
        return SayTTSService()
    if engine == "silence":
        from app.services.tts.silence import SilenceTTSService
        return SilenceTTSService()
    if engine == "mock":
        return MockTTSService()
    if engine in ("aliyun", "cosyvoice", "volcengine", "elevenlabs"):
        raise NotImplementedError(
            f"TTS 引擎 {engine} 尚未内置实现：请在 backend/app/services/tts/ 下新增实现类并注册，"
            f"或参照 README「模型 API 配置」使用免费引擎 pollinations / edge"
        )
    # 默认（含 auto / 未知值）：免费在线 TTS
    from app.services.tts.pollinations_tts import PollinationsTTSService
    return PollinationsTTSService()
