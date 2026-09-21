"""SQLAlchemy 声明式基类与公共列。

全库约定（对齐 schema.sql 设计原则）：
- 业务表主键：BIGINT GENERATED ALWAYS AS IDENTITY（≈ MySQL AUTO_INCREMENT）；
- 会话/运行类主键：UUID + gen_random_uuid()（可直接作 LangGraph thread_id）；
- 时间戳：TIMESTAMPTZ，server_default=now()（由数据库填，不依赖应用时钟）。
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Identity, func
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedColumn, mapped_column


class Base(DeclarativeBase):
    """所有模型的声明式基类（≈ JPA 的 @MappedSuperclass 载体）。"""


class BigIdBase(Base):
    """BIGINT IDENTITY 主键的抽象基类。"""

    __abstract__ = True

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)


# 复用的列定义（写函数而不是列对象：列对象不能跨表复用）
def created_at_col() -> MappedColumn[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def updated_at_col() -> MappedColumn[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
