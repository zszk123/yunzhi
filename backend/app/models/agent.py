"""模块三：Skill 与 Agent（对应设计稿 Agent 创建页）。

schema.sql: skills / agents / agent_skills / agent_kbs。

Skill = 提示词模板 + 工具组合包（Java 域注册管理，Python 运行时加载）；
Agent 通过桥接表挂载 Skill 与知识库（运行时把 kb.search 限定到挂载的库）。
"""

from datetime import datetime

from sqlalchemy import ForeignKey, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BigIdBase, created_at_col, updated_at_col


class Skill(BigIdBase):
    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("name", "version"),)

    name: Mapped[str] = mapped_column(String(128))
    version: Mapped[str] = mapped_column(String(32), server_default="1.0.0")
    description: Mapped[str | None] = mapped_column(Text)
    prompt_template: Mapped[str] = mapped_column(Text)  # system prompt，支持 {{变量}}
    tool_names: Mapped[list[str]] = mapped_column(
        ARRAY(Text), server_default="'{}'::text[]"
    )  # 如 {kb.search, web.search}
    output_schema: Mapped[dict | None] = mapped_column(JSONB)  # 输出格式约束（JSON Schema）
    enabled: Mapped[int] = mapped_column(SmallInteger, server_default="1")  # Java 域启停开关
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()


class Agent(BigIdBase):
    __tablename__ = "agents"

    name: Mapped[str] = mapped_column(String(128))
    type: Mapped[int] = mapped_column(SmallInteger)  # 1=对话型 2=会话流（工作流）型
    description: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    # {"provider":"openai_compatible","base_url":"...","model":"qwen-max",...}
    model_config: Mapped[dict] = mapped_column(JSONB, server_default="'{}'::jsonb")
    system_prompt: Mapped[str | None] = mapped_column(Text)
    status: Mapped[int] = mapped_column(SmallInteger, server_default="1")
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()


class AgentSkill(Base):  # 桥接表：联合主键
    __tablename__ = "agent_skills"

    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )


class AgentKb(Base):  # 桥接表：联合主键
    __tablename__ = "agent_kbs"

    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True
    )
    kb_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"), primary_key=True
    )
