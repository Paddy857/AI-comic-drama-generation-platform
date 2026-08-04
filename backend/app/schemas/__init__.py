from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    nickname: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    is_vip: bool
    daily_generate_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    style: Optional[str] = None
    total_pages: Optional[int] = 0
    template_id: Optional[int] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    style: Optional[str] = None
    total_pages: Optional[int] = None
    current_page: Optional[int] = None
    cover_url: Optional[str] = None


class ProjectOut(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    status: str
    category: Optional[str] = None
    style: Optional[str] = None
    total_pages: int
    current_page: int
    template_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CharacterCreate(BaseModel):
    name: str
    role_type: Optional[str] = "main"
    role_label: Optional[str] = None
    appearance: Optional[str] = None
    personality: Optional[str] = None
    project_id: Optional[int] = None
    project_name: Optional[str] = None


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    role_type: Optional[str] = None
    role_label: Optional[str] = None
    appearance: Optional[str] = None
    personality: Optional[str] = None
    avatar_url: Optional[str] = None


class CharacterOut(BaseModel):
    id: int
    user_id: int
    project_id: Optional[int] = None
    name: str
    role_type: str
    role_label: Optional[str] = None
    appearance: Optional[str] = None
    personality: Optional[str] = None
    avatar_url: Optional[str] = None
    project_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SceneCreate(BaseModel):
    name: str
    description: Optional[str] = None
    scene_type: Optional[str] = None
    time_of_day: Optional[str] = None
    weather: Optional[str] = None
    project_id: Optional[int] = None


class SceneUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    scene_type: Optional[str] = None
    time_of_day: Optional[str] = None
    weather: Optional[str] = None
    preview_url: Optional[str] = None


class SceneOut(BaseModel):
    id: int
    user_id: int
    project_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    scene_type: Optional[str] = None
    time_of_day: Optional[str] = None
    weather: Optional[str] = None
    preview_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ShotCreate(BaseModel):
    project_id: int
    order: Optional[int] = 0
    shot_type: Optional[str] = None
    camera_move: Optional[str] = None
    duration_sec: Optional[int] = 5
    script_content: Optional[str] = None
    mood: Optional[str] = None
    mood_intensity: Optional[int] = 5


class ShotUpdate(BaseModel):
    order: Optional[int] = None
    shot_type: Optional[str] = None
    camera_move: Optional[str] = None
    duration_sec: Optional[int] = None
    script_content: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[str] = None
    mood: Optional[str] = None
    mood_intensity: Optional[int] = None


class ShotOut(BaseModel):
    id: int
    project_id: int
    order: int
    shot_no: Optional[int] = None
    shot_type: Optional[str] = None
    camera_move: Optional[str] = None
    duration_sec: int
    script_content: Optional[str] = None
    image_url: Optional[str] = None
    status: str
    mood: Optional[str] = None
    mood_intensity: int
    created_at: datetime

    class Config:
        from_attributes = True


class TemplateVariableOut(BaseModel):
    id: int
    key: str
    label: str
    var_type: str
    is_required: bool
    default_value: Optional[str] = None
    hint: Optional[str] = None
    examples: Optional[list] = None
    options: Optional[list] = None
    ai_generated: bool
    sort_order: int

    class Config:
        from_attributes = True


class TemplateShotOut(BaseModel):
    id: int
    shot_no: int
    shot_type: Optional[str] = None
    camera_move: Optional[str] = None
    duration_sec: int
    script_template: Optional[str] = None
    mood: Optional[str] = None
    mood_intensity: int

    class Config:
        from_attributes = True


class TemplateOut(BaseModel):
    id: int
    template_code: str
    name: str
    category: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    preview_gif_url: Optional[str] = None
    total_shots: int
    total_duration_sec: int
    required_var_count: int
    avg_play: Optional[str] = None
    avg_finish_rate: Optional[str] = None
    emotion_curve: Optional[list] = None
    tags: Optional[list] = None
    is_beginner_friendly: bool
    use_count: int
    is_favorited: Optional[bool] = False
    variables: Optional[list[TemplateVariableOut]] = None
    fixed_shots: Optional[list[TemplateShotOut]] = None

    class Config:
        from_attributes = True


class GenerationTaskCreate(BaseModel):
    project_id: Optional[int] = None
    template_id: Optional[int] = None
    task_name: Optional[str] = None
    task_type: Optional[str] = "from_template"
    variables_snapshot: Optional[dict] = None
    style: Optional[str] = None
    voice_combo: Optional[str] = None
    description: Optional[str] = None  # for free_style


class GeneratedShotOut(BaseModel):
    id: int
    shot_no: int
    script_content: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GenerationTaskOut(BaseModel):
    id: int
    user_id: int
    project_id: Optional[int] = None
    template_id: Optional[int] = None
    task_name: Optional[str] = None
    task_type: str
    status: str
    progress: int
    current_step: Optional[str] = None
    total_shots: int
    completed_shots: int
    estimated_seconds: Optional[int] = None
    error_msg: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    video_url: Optional[str] = None
    shots: List[GeneratedShotOut] = []

    class Config:
        from_attributes = True


class AssetOut(BaseModel):
    id: int
    user_id: int
    project_id: Optional[int] = None
    file_name: str
    file_path: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    tags: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class StatsOut(BaseModel):
    total_projects: int
    monthly_creations: int
    total_ai_generates: int
    total_assets: int
