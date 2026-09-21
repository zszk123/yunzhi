"""配置管理：pydantic-settings 读 .env，改配置零改码。

Java 类比：application.yml + @ConfigurationProperties，且带启动期校验——
缺必填项时服务直接起不来（ValidationError），而不是运行到一半才失败。
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 环境
    app_env: str = "dev"
    log_level: str = "INFO"

    # 后端服务
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000

    # PostgreSQL（必填，无默认值：连不上库的服务没有意义）
    database_url: str

    # Qdrant / Redis
    qdrant_url: str = "http://localhost:6333"
    redis_url: str = "redis://localhost:6379/0"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str = "yunzhi-files"


@lru_cache
def get_settings() -> Settings:
    """进程级单例：整个服务共享一份配置。"""
    return Settings()
