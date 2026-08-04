from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.generation import GenerationTask
from app.models.asset import Asset
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas import ProjectCreate, ProjectOut, ProjectUpdate, StatsOut

router = APIRouter(prefix="/projects", tags=["项目管理"])


@router.get("/stats", response_model=StatsOut)
def get_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    total_projects = db.query(Project).filter(Project.user_id == current_user.id).count()
    now = datetime.utcnow()
    monthly_creations = (
        db.query(Project)
        .filter(
            Project.user_id == current_user.id,
            Project.created_at >= datetime(now.year, now.month, 1),
        )
        .count()
    )
    total_ai_generates = (
        db.query(GenerationTask)
        .filter(GenerationTask.user_id == current_user.id, GenerationTask.status == "done")
        .count()
    )
    total_assets = db.query(Asset).filter(Asset.user_id == current_user.id).count()
    return StatsOut(
        total_projects=total_projects,
        monthly_creations=monthly_creations,
        total_ai_generates=total_ai_generates,
        total_assets=total_assets,
    )


@router.get("/", response_model=List[ProjectOut])
def list_projects(
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Project).filter(Project.user_id == current_user.id)
    if status:
        query = query.filter(Project.status == status)
    if keyword:
        query = query.filter(Project.title.contains(keyword))
    projects = query.order_by(Project.updated_at.desc()).offset(skip).limit(limit).all()
    return projects


@router.post("/", response_model=ProjectOut)
def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = Project(user_id=current_user.id, **data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(project, field, value)
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    db.delete(project)
    db.commit()
    return {"message": "项目已删除"}
