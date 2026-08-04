from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    name = Column(String(100), nullable=False)
    role_type = Column(String(20), default="main")  # main / female_main / villain / supporting
    role_label = Column(String(50), nullable=True)   # 主角 / 女主角 / 反派 / 配角
    appearance = Column(Text, nullable=True)
    personality = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    project_name = Column(String(200), nullable=True)  # 冗余，方便展示
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="characters")
