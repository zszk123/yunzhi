"""T3 配置管理：pydantic-settings 行为测试。"""

import pytest
from pydantic import ValidationError

from app.core.settings import Settings

REQUIRED = {
    "database_url": "postgresql+psycopg://yunzhi:yunzhi@localhost:5432/yunzhi",
    "minio_access_key": "minioadmin",
    "minio_secret_key": "minioadmin",
}


def _write_env(tmp_path, data: dict[str, str]):
    env_file = tmp_path / ".env"
    env_file.write_text("\n".join(f"{k.upper()}={v}" for k, v in data.items()))
    return env_file


def test_loads_values_from_env_file(tmp_path):
    env_file = _write_env(tmp_path, {**REQUIRED, "log_level": "DEBUG", "backend_port": "9000"})
    settings = Settings(_env_file=env_file)
    assert settings.database_url == REQUIRED["database_url"]
    assert settings.log_level == "DEBUG"
    assert settings.backend_port == 9000


def test_missing_required_field_raises_validation_error(tmp_path):
    env_file = _write_env(
        tmp_path,
        {"minio_access_key": "x", "minio_secret_key": "y"},  # 缺 database_url
    )
    with pytest.raises(ValidationError):
        Settings(_env_file=env_file)


def test_defaults_applied_when_not_set(tmp_path):
    env_file = _write_env(tmp_path, REQUIRED)
    settings = Settings(_env_file=env_file)
    assert settings.app_env == "dev"
    assert settings.log_level == "INFO"
    assert settings.minio_bucket == "yunzhi-files"
    assert settings.backend_port == 8000
    assert settings.redis_url == "redis://localhost:6379/0"
    assert settings.qdrant_url == "http://localhost:6333"
