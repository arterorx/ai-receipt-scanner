from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    database_path: str = "receipts.db"
    max_file_size_mb: int = 10
    log_level: str = "INFO"

    model_config = {"env_file": ".env"}


settings = Settings()
