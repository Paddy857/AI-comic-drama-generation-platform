from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.character import Character
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas import CharacterCreate, CharacterOut, CharacterUpdate

router = APIRouter(prefix="/characters", tags=["角色库"])


@router.get("/", response_model=List[CharacterOut])
def list_characters(
    project_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Character).filter(Character.user_id == current_user.id)
    if project_id:
        query = query.filter(Character.project_id == project_id)
    if keyword:
        query = query.filter(Character.name.contains(keyword))
    return query.order_by(Character.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/", response_model=CharacterOut)
def create_character(
    data: CharacterCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    character = Character(user_id=current_user.id, **data.model_dump())
    db.add(character)
    db.commit()
    db.refresh(character)
    return character


@router.get("/{character_id}", response_model=CharacterOut)
def get_character(
    character_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = db.query(Character).filter(Character.id == character_id, Character.user_id == current_user.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="角色不存在")
    return c


@router.put("/{character_id}", response_model=CharacterOut)
def update_character(
    character_id: int,
    data: CharacterUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = db.query(Character).filter(Character.id == character_id, Character.user_id == current_user.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="角色不存在")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(c, field, value)
    c.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(c)
    return c


@router.delete("/{character_id}")
def delete_character(
    character_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = db.query(Character).filter(Character.id == character_id, Character.user_id == current_user.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="角色不存在")
    db.delete(c)
    db.commit()
    return {"message": "角色已删除"}
