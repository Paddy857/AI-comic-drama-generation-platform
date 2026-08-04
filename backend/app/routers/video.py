"""视频合成接口：图片 + 音频 + 字幕 → 带 Ken Burns 效果的视频片段"""

import os
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import settings
from app.services.video_composer import VideoComposer

router = APIRouter(prefix="/video", tags=["视频合成"])

composer = VideoComposer()

_TMP_DIR = os.path.join(settings.upload_dir, "video_tmp")
_OUT_DIR = os.path.join(settings.upload_dir, "video_out")


@router.post("/compose", summary="图片+音频+字幕合成视频片段")
async def compose_video(
    image: UploadFile = File(..., description="静态图片"),
    audio: UploadFile = File(..., description="配音音频"),
    subtitle_text: str = Form("", description="台词字幕文本"),
    width: int = Form(1080),
    height: int = Form(1920),
    direction: str = Form("in", description="Ken Burns 方向: in推近/out拉远"),
) -> dict:
    os.makedirs(_TMP_DIR, exist_ok=True)
    os.makedirs(_OUT_DIR, exist_ok=True)
    uid = uuid.uuid4().hex[:10]

    image_path = os.path.join(_TMP_DIR, f"{uid}_img{os.path.splitext(image.filename or '')[-1] or '.jpg'}")
    audio_path = os.path.join(_TMP_DIR, f"{uid}_audio{os.path.splitext(audio.filename or '')[-1] or '.mp3'}")
    output_path = os.path.join(_OUT_DIR, f"{uid}.mp4")

    try:
        for upload, dest in ((image, image_path), (audio, audio_path)):
            with open(dest, "wb") as f:
                f.write(await upload.read())

        video_url = composer.compose(
            image_path=image_path,
            audio_path=audio_path,
            subtitle_text=subtitle_text,
            output_path=output_path,
            width=width,
            height=height,
            direction=direction,
        )
        return {
            "video_url": f"/{video_url}",
            "duration": composer._probe_duration(video_url),
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        for p in (image_path, audio_path):
            if os.path.exists(p):
                os.remove(p)
