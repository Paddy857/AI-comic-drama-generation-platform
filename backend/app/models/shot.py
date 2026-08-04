from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Shot(Base):
    __tablename__ = "shots"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    order = Column(Integer, default=0)
    shot_no = Column(Integer, nullable=True)
    shot_type = Column(String(50), nullable=True)    # 大全景 / 全景 / 中景 / 近景 / 特写
    camera_move = Column(String(50), nullable=True)  # 固定 / 推 / 拉 / 摇 / 跟
    duration_sec = Column(Integer, default=5)
    script_content = Column(Text, nullable=True)     # 镜头脚本/对白
    image_url = Column(String(500), nullable=True)   # 已生成的分镜图
    status = Column(String(20), default="pending")   # pending / generating / done / failed
    mood = Column(String(50), nullable=True)         # 压抑铺垫 / 冲突升级 / 反转爆发
    mood_intensity = Column(Integer, default=5)      # 1-10
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="shots")
