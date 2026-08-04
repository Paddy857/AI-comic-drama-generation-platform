import asyncio
import os
import re
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.generation import GenerationTask, GeneratedShot
from app.models.template import Template
from app.models.project import Project
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas import GenerationTaskCreate, GenerationTaskOut, GeneratedShotOut
from app.schemas.image import ImageTask
from app.services.image_gen import BatchImageService, get_image_generator

router = APIRouter(prefix="/generate", tags=["AI生成"])

_batch_service = BatchImageService(generator=get_image_generator())

STEPS = [
    "变量注入模板",
    "剧本自动合成",
    "角色图生成",
    "分镜批量绘图",
    "配音合成+渲染",
]


def _render_template_script(script_template: str, variables: dict) -> str:
    """Replace ${variable} with actual values"""
    def replacer(match):
        key = match.group(1)
        return str(variables.get(key, f"[{key}]"))
    return re.sub(r"\$\{(\w+)\}", replacer, script_template or "")


# 前端画风值 -> 生图风格描述
_STYLE_PROMPT = {
    "ancient": "古风唯美插画，工笔国风，淡雅水墨",
    "cyber": "赛博朋克，霓虹光影，未来都市",
    "japanese": "日系动漫，精致赛璐璐上色",
    "watercolor": "清新水彩手绘，柔和晕染",
}


def _build_image_prompt(script: str, style: str) -> str:
    """由分镜剧本构造竖屏生图提示词"""
    style_desc = _STYLE_PROMPT.get(style or "", "国漫厚涂")
    return f"电影感竖屏漫画分镜：{script}。风格：{style_desc}。人物表情生动，画面精美，纯背景无字幕"


def _render_task_video(db: Session, task: GenerationTask) -> None:
    """第5步：逐镜 TTS 配音 + Ken Burns 视频合成 + 拼接完整漫剧，写回 task.video_url"""
    from app.core.config import settings
    from app.services.tts import get_tts_service
    from app.services.video_composer import VideoComposer

    shots = (
        db.query(GeneratedShot)
        .filter(GeneratedShot.task_id == task.id)
        .order_by(GeneratedShot.shot_no)
        .all()
    )
    if not shots:
        return

    clip_dir = os.path.join(settings.upload_dir, "video_tmp", f"task_{task.id}")
    os.makedirs(clip_dir, exist_ok=True)
    composer = VideoComposer()
    tts = get_tts_service()
    clip_paths = []

    for idx, shot in enumerate(shots):
        if not shot.image_url or not shot.script_content:
            continue
        img_path = os.path.join(settings.upload_dir, shot.image_url.replace("/uploads/", "", 1))
        if not os.path.isfile(img_path):
            continue
        try:
            audio = tts.generate_audio(
                text=shot.script_content,
                voice_id="female_gentle" if idx % 2 == 0 else "male_steady",
                emotion="平静",
            )
            audio_path = os.path.join(
                settings.upload_dir, audio.audio_url.replace("/uploads/", "", 1)
            )
            clip_path = os.path.join(clip_dir, f"S{shot.shot_no:03d}.mp4")
            composer.compose(
                image_path=img_path,
                audio_path=audio_path,
                subtitle_text=shot.script_content,
                output_path=clip_path,
                width=720,
                height=1280,
                direction="in" if idx % 2 == 0 else "out",
            )
            clip_paths.append(clip_path)
        except Exception as e:
            task.error_msg = f"第{shot.shot_no}镜渲染失败: {e}"
        task.progress = min(99, 95 + int((idx + 1) / len(shots) * 4))
        db.commit()

    if clip_paths:
        video_out = os.path.join(settings.upload_dir, "video_out", f"task_{task.id}.mp4")
        os.makedirs(os.path.dirname(video_out), exist_ok=True)
        VideoComposer.concat_clips(clip_paths, video_out)
        rel = os.path.relpath(video_out, settings.upload_dir).replace(os.sep, "/")
        task.video_url = f"/uploads/{rel}"
        db.commit()


def _run_generation(task_id: int, db_url: str):
    """Simulate async generation in background"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        task = db.query(GenerationTask).filter(GenerationTask.id == task_id).first()
        if not task:
            return

        task.status = "running"
        task.started_at = datetime.utcnow()
        db.commit()

        template = db.query(Template).filter(Template.id == task.template_id).first()
        total_shots = template.total_shots if template else 4
        task.total_shots = total_shots
        db.commit()

        variables = task.variables_snapshot or {}

        for step_idx, step_name in enumerate(STEPS):
            task.current_step = step_name
            task.progress = max(task.progress, int((step_idx / len(STEPS)) * 80))
            db.commit()

            import time
            if step_idx == 0:
                time.sleep(1)
            elif step_idx == 1:
                time.sleep(2)
            elif step_idx == 2:
                time.sleep(3)
            elif step_idx == 3:
                # 分镜批量绘图：真实调用文生图服务（Pollinations），图片落盘后写回
                tasks = []
                if template and template.fixed_shots:
                    for shot in template.fixed_shots:
                        script = _render_template_script(shot.script_template, variables)
                        gen_shot = GeneratedShot(
                            task_id=task.id,
                            shot_no=shot.shot_no,
                            script_content=script,
                            image_url=None,
                            status="generating",
                        )
                        db.add(gen_shot)
                        task.completed_shots += 1
                        db.commit()
                        tasks.append(
                            ImageTask(
                                scene_id=f"S{shot.shot_no:03d}",
                                prompt=_build_image_prompt(script, task.style),
                                style=task.style or "ancient",
                                aspect_ratio="9:16",
                            )
                        )
                else:
                    for i in range(1, total_shots + 1):
                        gen_shot = GeneratedShot(
                            task_id=task.id,
                            shot_no=i,
                            script_content=f"第{i}镜内容",
                            status="generating",
                        )
                        db.add(gen_shot)
                        task.completed_shots += 1
                        db.commit()
                        tasks.append(
                            ImageTask(
                                scene_id=f"S{i:03d}",
                                prompt=_build_image_prompt(f"第{i}镜：{task.task_name}", task.style),
                                style=task.style or "ancient",
                                aspect_ratio="9:16",
                            )
                        )

                if tasks:
                    from app.core.config import settings
                    batch_id = _batch_service.submit_prompts(
                        tasks, concurrency=settings.image_concurrency
                    )
                    # 轮询批量任务直到全部完成（期间同步进度，供前端实时展示）
                    while True:
                        batch = _batch_service.get_batch_status(batch_id)
                        task.progress = max(task.progress, 48 + int(batch["progress"] * 0.47))
                        task.completed_shots = batch["completed"] + batch["failed"]
                        db.commit()
                        if batch["status"] == "done":
                            break
                        time.sleep(1.5)
                    # 将生成的图片 URL 写回分镜记录
                    for item in batch["tasks"]:
                        shot_no = int(item["scene_id"].lstrip("S"))
                        shot = db.query(GeneratedShot).filter(
                            GeneratedShot.task_id == task.id,
                            GeneratedShot.shot_no == shot_no,
                        ).first()
                        if shot:
                            shot.image_url = item.get("image_url")
                            shot.status = "done" if item["status"] == "completed" else "failed"
                    task.completed_shots = batch["completed"]
                    db.commit()
            elif step_idx == 4:
                # 配音合成+渲染：逐镜 TTS 配音 → Ken Burns 视频片段 → 拼接完整漫剧
                _render_task_video(db, task)

        task.status = "done"
        task.progress = 100
        task.current_step = "生成完成"
        task.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        task = db.query(GenerationTask).filter(GenerationTask.id == task_id).first()
        if task:
            task.status = "failed"
            task.error_msg = str(e)
            db.commit()
    finally:
        db.close()


@router.post("/", response_model=GenerationTaskOut)
def create_generation_task(
    data: GenerationTaskCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Check daily quota
    today_count = (
        db.query(GenerationTask)
        .filter(
            GenerationTask.user_id == current_user.id,
            GenerationTask.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0),
        )
        .count()
    )
    if today_count >= 10 and not current_user.is_vip:
        raise HTTPException(status_code=429, detail="今日生成次数已达上限（10次），明天再来～")

    task = GenerationTask(
        user_id=current_user.id,
        project_id=data.project_id,
        template_id=data.template_id,
        task_name=data.task_name or "新建生成任务",
        task_type=data.task_type or "from_template",
        variables_snapshot=data.variables_snapshot,
        style=data.style,
        voice_combo=data.voice_combo,
        status="pending",
        progress=0,
        total_shots=0,
        completed_shots=0,
        estimated_seconds=210,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    from app.core.config import settings
    background_tasks.add_task(_run_generation, task.id, settings.database_url)
    return task


@router.post("/ai-fill-variables")
def ai_fill_variables(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mock AI variable filling - returns generated optional variables based on required ones"""
    required = payload.get("required_vars", {})
    hero_name = required.get("hero_name", "萧战")
    heroine_name = required.get("heroine_name", "苏沐雪")
    punchline = required.get("punchline", "")

    return {
        "generated_vars": {
            "hero_appearance": f"{hero_name}，剑眉星目，气宇轩昂，眼神深邃如渊",
            "villain_name": "王少爷",
            "scene1_location": "豪华酒店宴会厅，灯火辉煌",
            "bgm_style": "都市爽感",
            "hero_background": f"{hero_name}曾是被家族抛弃的废婿，三年沉默，如今龙神归位",
            "heroine_trait": f"{heroine_name}外冷内热，内心深处一直在等待那个人回来",
        },
        "punchline_suggestions": [
            punchline or "三年之期已满，龙神归位！",
            f"你们嘲笑的{hero_name}，如今站在你们仰望不到的高处",
            "笑够了吗？现在轮到我了。",
        ]
    }


@router.get("/tasks", response_model=List[GenerationTaskOut])
def list_tasks(
    status: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(GenerationTask).filter(GenerationTask.user_id == current_user.id)
    if status:
        query = query.filter(GenerationTask.status == status)
    return query.order_by(GenerationTask.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/history", response_model=List[GenerationTaskOut])
def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(GenerationTask)
        .filter(GenerationTask.user_id == current_user.id, GenerationTask.status == "done")
        .order_by(GenerationTask.completed_at.desc())
        .limit(20)
        .all()
    )


@router.get("/tasks/{task_id}", response_model=GenerationTaskOut)
def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(GenerationTask).filter(
        GenerationTask.id == task_id, GenerationTask.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    data = GenerationTaskOut.model_validate(task).model_dump()
    data["shots"] = [
        GeneratedShotOut.model_validate(s).model_dump()
        for s in db.query(GeneratedShot)
        .filter(GeneratedShot.task_id == task_id)
        .order_by(GeneratedShot.shot_no)
        .all()
    ]
    return data


@router.post("/tasks/{task_id}/cancel")
def cancel_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(GenerationTask).filter(
        GenerationTask.id == task_id, GenerationTask.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status not in ["pending", "running"]:
        raise HTTPException(status_code=400, detail="任务已完成或已取消")
    task.status = "cancelled"
    db.commit()
    return {"message": "任务已取消"}
