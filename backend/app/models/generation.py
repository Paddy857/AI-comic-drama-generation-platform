from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class GenerationTask(Base):
    __tablename__ = "generation_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=True)
    task_name = Column(String(200), nullable=True)
    task_type = Column(String(30), default="from_template")  # from_template / free_style / regenerate_shot
    status = Column(String(20), default="pending")  # pending / running / done / failed / cancelled
    progress = Column(Integer, default=0)           # 0-100
    current_step = Column(String(100), nullable=True)
    variables_snapshot = Column(JSON, nullable=True)  # 用户填的变量JSON快照
    style = Column(String(50), nullable=True)        # 画风
    voice_combo = Column(String(100), nullable=True) # 声线组合
    result_shots = Column(JSON, nullable=True)       # 已生成的分镜列表
    video_url = Column(String(500), nullable=True)   # 全流程渲染完成的完整漫剧视频
    error_msg = Column(Text, nullable=True)
    total_shots = Column(Integer, default=0)
    completed_shots = Column(Integer, default=0)
    estimated_seconds = Column(Integer, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="generation_tasks")
    project = relationship("Project", back_populates="generation_tasks")
    generated_shots = relationship("GeneratedShot", back_populates="task", cascade="all, delete-orphan")


class GeneratedShot(Base):
    __tablename__ = "generated_shots"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("generation_tasks.id"), nullable=False)
    shot_no = Column(Integer, nullable=False)
    script_content = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("GenerationTask", back_populates="generated_shots")
