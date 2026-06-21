"""应用配置（基于 pydantic-settings）。

支持从环境变量 / .env 文件加载。生产环境通过环境变量注入敏感配置。
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # 应用
    APP_NAME: str = "企业级脚手架模板"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # 数据库：默认 PG，本地无 PG 时可改 sqlite+aiosqlite
    DATABASE_URL: str = "postgresql+asyncpg://app:app@localhost:5432/scaffold"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 1800
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 604800

    # 初始管理员
    INITIAL_ADMIN_USERNAME: str = "admin"
    INITIAL_ADMIN_PASSWORD: str = "Admin123456"
    INITIAL_ADMIN_EMAIL: str = "admin@example.com"

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
