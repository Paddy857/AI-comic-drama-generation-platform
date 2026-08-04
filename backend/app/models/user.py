from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    nickname = Column(String(50), default="创作者")
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    is_vip = Column(Boolean, default=False)
    daily_generate_count = Column(Integer, default=0)
    daily_generate_reset_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="user", cascade="all, delete-orphan")
    scenes = relationship("Scene", back_populates="user", cascade="all, delete-orphan")
    generation_tasks = relationship("GenerationTask", back_populates="user", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("UserFavorite", back_populates="user", cascade="all, delete-orphan")
