"""T8/T9 Alembic 迁移测试：临时库上验证 upgrade / downgrade 全链路。

做法（≈ Java 里用 Testcontainers 起临时库测 Flyway）：
- 连 docker 里的 PG，建一次性测试库 yunzhi_migration_test；
- 用 alembic 的 Python API 执行 upgrade head / downgrade base；
- 通过 information_schema（≈ MySQL SHOW TABLES 的机器可读版）断言表与索引。
"""

from collections.abc import Iterator

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from app.core.settings import get_settings

# schema.sql 定义的 18 张业务表（alembic_version 是迁移工具自己的账本，不算）
EXPECTED_TABLES = {
    "users",
    "roles",
    "user_roles",
    "knowledge_bases",
    "documents",
    "document_chunks",
    "data_sources",
    "parse_tasks",
    "retrieval_logs",
    "skills",
    "agents",
    "agent_skills",
    "agent_kbs",
    "agent_sessions",
    "agent_messages",
    "workflows",
    "workflow_runs",
    "audit_logs",
}

KEY_INDEXES = {
    "idx_documents_kb",
    "idx_documents_status",
    "idx_chunks_doc",
    "idx_chunks_parent",
    "idx_parse_tasks_status",
    "idx_sessions_agent_user",
    "idx_messages_session",
    "idx_runs_workflow",
    "idx_audit_user_time",
}

TEST_DB = "yunzhi_migration_test"


def _alembic_cfg(db_url: str) -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def _table_names(db_url: str) -> set[str]:
    engine = sa.create_engine(db_url)
    try:
        insp = sa.inspect(engine)
        return set(insp.get_table_names()) - {"alembic_version"}
    finally:
        engine.dispose()  # 不关连接会导致 teardown 删库报 ObjectInUse


@pytest.fixture
def temp_db_url() -> Iterator[str]:
    settings = get_settings()
    base_url = settings.database_url.rsplit("/", 1)[0]
    admin_engine = sa.create_engine(f"{base_url}/postgres", isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        conn.execute(sa.text(f"DROP DATABASE IF EXISTS {TEST_DB} WITH (FORCE)"))
        conn.execute(sa.text(f"CREATE DATABASE {TEST_DB}"))
    yield f"{base_url}/{TEST_DB}"
    with admin_engine.connect() as conn:
        # WITH (FORCE)：强制踢掉残留连接（PG13+），防止删库被占用的会话卡住
        conn.execute(sa.text(f"DROP DATABASE IF EXISTS {TEST_DB} WITH (FORCE)"))
    admin_engine.dispose()


def test_upgrade_head_creates_18_tables_and_key_indexes(temp_db_url: str):
    command.upgrade(_alembic_cfg(temp_db_url), "head")

    assert _table_names(temp_db_url) == EXPECTED_TABLES

    insp = sa.inspect(sa.create_engine(temp_db_url))
    index_names = {idx["name"] for table in EXPECTED_TABLES for idx in insp.get_indexes(table)}
    assert index_names >= KEY_INDEXES


def test_downgrade_then_upgrade_is_reproducible(temp_db_url: str):
    cfg = _alembic_cfg(temp_db_url)

    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")
    assert _table_names(temp_db_url) == set(), "downgrade base 后应一张业务表都不剩"

    command.upgrade(cfg, "head")
    assert _table_names(temp_db_url) == EXPECTED_TABLES
