from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.scene import Scene
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas import SceneCreate, SceneOut, SceneUpdate

router = APIRouter(prefix="/scenes", tags=["场景库"])


@router.get("", response_model=List[SceneOut])
def list_scenes(
    project_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Scene).filter(Scene.user_id == current_user.id)
    if project_id:
        query = query.filter(Scene.project_id == project_id)
    if keyword:
        query = query.filter(Scene.name.contains(keyword))
    return query.order_by(Scene.created_at.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=SceneOut)
def create_scene(
    data: SceneCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scene = Scene(user_id=current_user.id, **data.model_dump())
    db.add(scene)
    db.commit()
    db.refresh(scene)
    return scene


@router.get("/{scene_id}", response_model=SceneOut)
def get_scene(
    scene_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    s = db.query(Scene).filter(Scene.id == scene_id, Scene.user_id == current_user.id).first()
    if not s:
        raise HTTPException(status_code=404, detail="场景不存在")
    return s


@router.put("/{scene_id}", response_model=SceneOut)
def update_scene(
    scene_id: int,
    data: SceneUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    s = db.query(Scene).filter(Scene.id == scene_id, Scene.user_id == current_user.id).first()
    if not s:
        raise HTTPException(status_code=404, detail="场景不存在")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(s, field, value)
    s.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(s)
    return s


@router.delete("/{scene_id}")
def delete_scene(
    scene_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    s = db.query(Scene).filter(Scene.id == scene_id, Scene.user_id == current_user.id).first()
    if not s:
        raise HTTPException(status_code=404, detail="场景不存在")
    db.delete(s)
    db.commit()
    return {"message": "场景已删除"}
