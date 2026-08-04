"""TTS 语音合成与配音接口"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.schemas.audio import AudioResult
from app.services.tts import VOICES, get_tts_service

router = APIRouter(prefix="/tts", tags=["TTS配音"])


class TTSGenerateRequest(BaseModel):
    text: str = Field(..., description="待合成文本")
    voice_id: Optional[str] = Field("female_gentle", description="音色ID，缺省温柔女声")
    emotion: Optional[str] = Field("平静", description="情绪标签")


@router.get("/voices", summary="获取可用音色库")
def list_voices() -> dict:
    return {"voices": [v.model_dump() for v in VOICES], "default_voice": "female_gentle"}


@router.post("/generate", summary="文本转语音合成")
def generate_audio(req: TTSGenerateRequest) -> AudioResult:
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="待合成文本不能为空")
    voice_ids = {v.id for v in VOICES}
    if req.voice_id not in voice_ids:
        raise HTTPException(status_code=400, detail=f"未知音色ID: {req.voice_id}，可选: {sorted(voice_ids)}")
    try:
        service = get_tts_service()
        return service.generate_audio(
            text=req.text.strip(),
            voice_id=req.voice_id,
            emotion=req.emotion or "平静",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS 合成失败: {e}")
