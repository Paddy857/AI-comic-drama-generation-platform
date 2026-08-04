import os
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.models.asset import Asset
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas import AssetOut

router = APIRouter(prefix="/assets", tags=["素材管理"])


@router.get("/", response_model=List[AssetOut])
def list_assets(
    project_id: Optional[int] = Query(None),
    file_type: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Asset).filter(Asset.user_id == current_user.id)
    if project_id:
        query = query.filter(Asset.project_id == project_id)
    if file_type:
        query = query.filter(Asset.file_type == file_type)
    return query.order_by(Asset.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/upload", response_model=AssetOut)
async def upload_asset(
    file: UploadFile = File(...),
    project_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Determine file type
    content_type = file.content_type or ""
    if "image" in content_type:
        file_type = "image"
    elif "video" in content_type:
        file_type = "video"
    elif "audio" in content_type:
        file_type = "audio"
    else:
        file_type = "other"

    # Save file
    ext = os.path.splitext(file.filename or "")[1]
    unique_name = f"{uuid.uuid4().hex}{ext}"
    upload_dir = os.path.join(settings.upload_dir, str(current_user.id))
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, unique_name)

    content = await file.read()
    if len(content) > settings.max_upload_size:
        raise HTTPException(status_code=413, detail="文件过大，最大支持50MB")

    with open(file_path, "wb") as f:
        f.write(content)

    asset = Asset(
        user_id=current_user.id,
        project_id=project_id,
        file_name=file.filename or unique_name,
        file_path=f"/uploads/{current_user.id}/{unique_name}",
        file_type=file_type,
        file_size=len(content),
        mime_type=content_type,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.delete("/{asset_id}")
def delete_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.user_id == current_user.id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="素材不存在")
    # Try to remove file
    try:
        real_path = asset.file_path.lstrip("/")
        if os.path.exists(real_path):
            os.remove(real_path)
    except Exception:
        pass
    db.delete(asset)
    db.commit()
    return {"message": "素材已删除"}
