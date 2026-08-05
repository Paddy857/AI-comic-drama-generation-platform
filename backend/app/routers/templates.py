from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.template import Template, TemplateVariable, TemplateShot
from app.models.favorite import UserFavorite
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas import TemplateOut

router = APIRouter(prefix="/templates", tags=["模板中心"])

CATEGORIES = ["全部", "热门爆款", "新手推荐", "都市", "古风", "甜宠", "悬疑", "玄幻", "校园", "末世"]


def _enrich_template(template: Template, user_id: int, db: Session) -> dict:
    data = TemplateOut.model_validate(template).model_dump()
    fav = db.query(UserFavorite).filter(
        UserFavorite.user_id == user_id, UserFavorite.template_id == template.id
    ).first()
    data["is_favorited"] = bool(fav)
    return data


@router.get("/categories")
def get_categories():
    return CATEGORIES


@router.get("", response_model=List[dict])
def list_templates(
    category: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("recommend"),  # recommend / newest / play_count / finish_rate / var_count
    beginner_only: Optional[bool] = Query(None),
    skip: int = 0,
    limit: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Template).filter(Template.is_active == True)
    if category and category not in ["全部", "热门爆款"]:
        if category == "新手推荐":
            query = query.filter(Template.is_beginner_friendly == True)
        else:
            query = query.filter(Template.category == category)
    if keyword:
        query = query.filter(Template.name.contains(keyword))
    if beginner_only:
        query = query.filter(Template.is_beginner_friendly == True)
    if sort_by == "newest":
        query = query.order_by(Template.created_at.desc())
    elif sort_by == "var_count":
        query = query.order_by(Template.required_var_count.asc())
    else:
        query = query.order_by(Template.sort_order.desc(), Template.use_count.desc())

    templates = query.offset(skip).limit(limit).all()
    return [_enrich_template(t, current_user.id, db) for t in templates]


@router.get("/favorites", response_model=List[dict])
def get_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    favs = db.query(UserFavorite).filter(UserFavorite.user_id == current_user.id).all()
    result = []
    for fav in favs:
        t = db.query(Template).get(fav.template_id)
        if t:
            result.append(_enrich_template(t, current_user.id, db))
    return result


@router.get("/{template_id}", response_model=dict)
def get_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = db.query(Template).filter(Template.id == template_id, Template.is_active == True).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return _enrich_template(template, current_user.id, db)


@router.post("/{template_id}/favorite")
def toggle_favorite(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # Check limit
    fav_count = db.query(UserFavorite).filter(UserFavorite.user_id == current_user.id).count()
    existing = db.query(UserFavorite).filter(
        UserFavorite.user_id == current_user.id, UserFavorite.template_id == template_id
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return {"is_favorited": False, "message": "已取消收藏"}
    else:
        if fav_count >= 20 and not current_user.is_vip:
            raise HTTPException(status_code=400, detail="免费用户最多收藏20套模板")
        fav = UserFavorite(user_id=current_user.id, template_id=template_id)
        db.add(fav)
        db.commit()
        return {"is_favorited": True, "message": "已收藏"}
