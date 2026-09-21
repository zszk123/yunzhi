"""模块一：用户与权限（对应设计稿登录页）。schema.sql: users / roles / user_roles。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BigIdBase, created_at_col, updated_at_col


class User(BigIdBase):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(64), unique=True)
    email: Mapped[str] = mapped_column(String(128), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))  # argon2/bcrypt，绝不存明文
    avatar_url: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[int] = mapped_column(SmallInteger, server_default="1")  # 1=启用 0=禁用
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()


class Role(BigIdBase):
    __tablename__ = "roles"

    code: Mapped[str] = mapped_column(String(32), unique=True)  # admin / editor / viewer
    name: Mapped[str] = mapped_column(String(64))


class UserRole(Base):  # 桥接表：联合主键，无自增 id
    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )
