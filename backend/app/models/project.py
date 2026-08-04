from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    cover_url = Column(String(500), nullable=True)
    status = Column(String(20), default="draft")  # draft / in_progress / review / completed
    category = Column(String(50), nullable=True)   # 都市 / 古风 / 甜宠 / 悬疑 / 玄幻 / 校园
    style = Column(String(50), nullable=True)       # 赛博 / 古风 / 日漫 / 水彩
    total_pages = Column(Integer, default=0)
    current_page = Column(Integer, default=0)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="projects")
    template = relationship("Template", back_populates="projects")
    shots = relationship("Shot", back_populates="project", cascade="all, delete-orphan", order_by="Shot.order")
    generation_tasks = relationship("GenerationTask", back_populates="project", cascade="all, delete-orphan")
