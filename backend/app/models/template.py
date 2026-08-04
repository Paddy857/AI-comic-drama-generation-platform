from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    template_code = Column(String(100), unique=True, nullable=False)  # TPL_URBAN_XUZHU_003
    name = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False)   # 都市 / 古风 / 甜宠 / 悬疑 / 玄幻 / 校园 / 新手推荐
    description = Column(Text, nullable=True)
    cover_url = Column(String(500), nullable=True)
    preview_gif_url = Column(String(500), nullable=True)
    total_shots = Column(Integer, default=10)
    total_duration_sec = Column(Integer, default=180)
    required_var_count = Column(Integer, default=3)
    avg_play = Column(String(50), nullable=True)      # "1200万"
    avg_finish_rate = Column(String(20), nullable=True) # "42%"
    emotion_curve = Column(JSON, nullable=True)        # [{shot, mood, intensity}]
    tags = Column(JSON, nullable=True)                 # ["新手友好", "爽感"]
    is_beginner_friendly = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    use_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    variables = relationship("TemplateVariable", back_populates="template", cascade="all, delete-orphan")
    fixed_shots = relationship("TemplateShot", back_populates="template", cascade="all, delete-orphan", order_by="TemplateShot.shot_no")
    projects = relationship("Project", back_populates="template")
    favorites = relationship("UserFavorite", back_populates="template", cascade="all, delete-orphan")


class TemplateVariable(Base):
    __tablename__ = "template_variables"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    key = Column(String(100), nullable=False)
    label = Column(String(100), nullable=False)
    var_type = Column(String(20), default="text")  # text / textarea / select
    is_required = Column(Boolean, default=False)
    default_value = Column(String(500), nullable=True)
    hint = Column(String(200), nullable=True)
    examples = Column(JSON, nullable=True)          # ["叶凡", "林辰"]
    options = Column(JSON, nullable=True)           # for select type
    ai_generated = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)

    template = relationship("Template", back_populates="variables")


class TemplateShot(Base):
    __tablename__ = "template_shots"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    shot_no = Column(Integer, nullable=False)
    shot_type = Column(String(50), nullable=True)
    camera_move = Column(String(50), nullable=True)
    duration_sec = Column(Integer, default=5)
    script_template = Column(Text, nullable=True)  # 含${变量}的模板脚本
    mood = Column(String(50), nullable=True)
    mood_intensity = Column(Integer, default=5)

    template = relationship("Template", back_populates="fixed_shots")
