"""TTS 服务工厂：根据配置 TTS_ENGINE 返回对应实现。

新增真实 TTS 厂商接入方式：
1. 在 tts/ 目录下新建实现文件（参考 edge_tts.py 骨架），继承 BaseTTSService 并实现 generate_audio()
2. 在下方 get_tts_service() 工厂中按引擎名注册
3. 修改 backend/.env 的 TTS_ENGINE 即可切换，上层配音流程无需改动
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
    """按配置返回 TTS 实现。
    - auto（默认）：macOS 用系统离线合成（say），其他平台用静音音频兜底，保证全流程可出片
    - say：强制 macOS say；silence：静音兜底；mock：纯模拟（不落盘）
    - 厂商引擎（aliyun/cosyvoice/volcengine/edge）：接入后在此注册，需在 README 配置对应 API
    """
    engine = settings.tts_engine.lower()
    if engine == "say":
        from app.services.tts.say import SayTTSService
        return SayTTSService()
    if engine == "silence":
        from app.services.tts.silence import SilenceTTSService
        return SilenceTTSService()
    if engine == "auto":
        import sys
        if sys.platform == "darwin":
            from app.services.tts.say import SayTTSService
            return SayTTSService()
        from app.services.tts.silence import SilenceTTSService
        return SilenceTTSService()
    if engine == "edge":
        from app.services.tts.edge_tts import EdgeTTSService
        return EdgeTTSService()
    if engine in ("aliyun", "cosyvoice", "elevenlabs", "volcengine"):
        raise NotImplementedError(
            f"TTS 引擎 {engine} 尚未接入，请先实现子类并注册到 get_tts_service()"
        )
    return MockTTSService()
