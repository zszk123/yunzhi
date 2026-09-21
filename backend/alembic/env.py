"""Alembic 运行环境：连接串来自 app.core.settings（测试可用 config 覆盖）。

设计（对应 tasks T8"env.py 从 settings 读连接串"）：
- 命令行/测试若显式设了 sqlalchemy.url（如临时测试库），优先使用；
- 否则回退到 Settings().database_url（即 .env 里的配置），不写死任何环境。
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.settings import Settings
from app.models import Base  # 导入即注册全部 18 张表到 metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 测试通过 cfg.set_main_option("sqlalchemy.url", ...) 注入临时库；
# 日常命令行不设置，走 .env
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", Settings().database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """offline 模式：只生成 SQL 脚本，不连库。"""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """online 模式：连库执行迁移。"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        # psycopg 在 Windows 上走 localhost（IPv6 优先回退）可能挂死，
        # 统一加连接超时兜底
        connect_args={"connect_timeout": 10},
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
