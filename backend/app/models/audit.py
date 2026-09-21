"""模块五：审计（Java 管理域）。schema.sql: audit_logs。"""

from datetime import datetime

from sqlalchemy import BigInteger, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BigIdBase, created_at_col


class AuditLog(BigIdBase):
    """关键操作留痕：login / upload / delete / agent.run。

    user_id 有意不加外键：审计日志要"用户删了记录还在"。
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index(
            "idx_audit_user_time",
            "user_id",
            "created_at",
            postgresql_ops={"created_at": "DESC"},
        ),
    )

    user_id: Mapped[int | None] = mapped_column(BigInteger)
    action: Mapped[str] = mapped_column(String(64))
    resource_type: Mapped[str | None] = mapped_column(String(32))
    resource_id: Mapped[str | None] = mapped_column(String(64))
    detail: Mapped[dict | None] = mapped_column(JSONB)
    ip: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = created_at_col()
