from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_type: str = "sqlite"
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "aigc_db"
    sqlite_path: str = "aigc.db"

    secret_key: str = "aigc-super-secret-key-2026"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080

    upload_dir: str = "uploads"
    max_upload_size: int = 52428800

    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_api_key: str = ""
    llm_model: str = "deepseek-chat"

    tts_engine: str = "auto"
    tts_upload_dir: str = "uploads/tts"

    image_gen_engine: str = "mock"
    image_gen_upload_dir: str = "uploads/image_gen"
    pollinations_base_url: str = "https://image.pollinations.ai"
    pollinations_timeout: int = 180
    image_concurrency: int = 1

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def database_url(self) -> str:
        if self.db_type.lower() == "sqlite":
            return f"sqlite:///./{self.sqlite_path}"
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )


settings = Settings()
