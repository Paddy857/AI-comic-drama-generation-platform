from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.shot import Shot
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas import ShotCreate, ShotOut, ShotUpdate

router = APIRouter(prefix="/shots", tags=["分镜管理"])


@router.get("/project/{project_id}", response_model=List[ShotOut])
def list_shots(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    shots = (
        db.query(Shot)
        .filter(Shot.project_id == project_id)
        .order_by(Shot.order)
        .all()
    )
    return shots


@router.post("/", response_model=ShotOut)
def create_shot(
    data: ShotCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    shot = Shot(**data.model_dump())
    db.add(shot)
    db.commit()
    db.refresh(shot)
    return shot


@router.put("/{shot_id}", response_model=ShotOut)
def update_shot(
    shot_id: int,
    data: ShotUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if not shot:
        raise HTTPException(status_code=404, detail="分镜不存在")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(shot, field, value)
    shot.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(shot)
    return shot


@router.delete("/{shot_id}")
def delete_shot(
    shot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if not shot:
        raise HTTPException(status_code=404, detail="分镜不存在")
    db.delete(shot)
    db.commit()
    return {"message": "分镜已删除"}
