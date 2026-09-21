"""模块四：会话与运行（Agent 对话页 / 工作流页）。

schema.sql: agent_sessions / agent_messages / workflows / workflow_runs。

关键设计：
- agent_sessions.id 用 UUID，直接作为 LangGraph PostgresSaver 的 thread_id
  （checkpoint 表由 PostgresSaver 自动建表管理，不在 Alembic 迁移内）；
- workflows.graph 整体存 JSONB（节点+边+坐标）——图结构是"整体读写"，
  且节点类型会持续演进，拆 nodes/edges 关系表反而锁死扩展性。
"""

import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, ForeignKey, Index, Integer, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BigIdBase, created_at_col, updated_at_col


class AgentSession(Base):
    __tablename__ = "agent_sessions"
    __table_args__ = (
        Index(
            "idx_sessions_agent_user",
            "agent_id",
            "user_id",
            "last_message_at",
            postgresql_ops={"last_message_at": "DESC"},
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, server_default=func.gen_random_uuid()
    )
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(256), server_default="新会话")  # 首条消息后 LLM 生成
    context: Mapped[dict | None] = mapped_column(
        JSONB, server_default="'{}'::jsonb"
    )  # 会话级变量（如当前案件号）
    message_count: Mapped[int] = mapped_column(Integer, server_default="0")
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created_at_col()


class AgentMessage(BigIdBase):
    """消息明细（trace 汇总存 workflow_runs，这里存对话本身）。"""

    __tablename__ = "agent_messages"
    __table_args__ = (Index("idx_messages_session", "session_id", "created_at"),)

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("agent_sessions.id", ondelete="CASCADE")
    )
    role: Mapped[int] = mapped_column(SmallInteger)  # 1=user 2=assistant 3=tool/system
    content: Mapped[str] = mapped_column(Text)
    reasoning: Mapped[str | None] = mapped_column(Text)  # 思考过程（可选展示）
    # [{"name":"kb.search","args":{...},"latency_ms":420}]（对话页工具调用卡）
    tool_calls: Mapped[dict | None] = mapped_column(JSONB)
    # [{"doc_id":1,"chunk_id":99,"quote":"...","score":0.88}]（回答下方引用 chips）
    citations: Mapped[dict | None] = mapped_column(JSONB)
    token_in: Mapped[int] = mapped_column(Integer, server_default="0")
    token_out: Mapped[int] = mapped_column(Integer, server_default="0")
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = created_at_col()


class Workflow(BigIdBase):
    """工作流定义（工作流页 FlowCanvas 画布的持久化形态）。

    graph JSONB 形如：
    {"nodes":[{"id":"n1","type":"llm","pos":{"x":120,"y":80},"params":{...}}],
     "edges":[{"from":"n1","to":"n2","condition":null}]}
    """

    __tablename__ = "workflows"

    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(128))
    graph: Mapped[dict] = mapped_column(JSONB)
    version: Mapped[int] = mapped_column(Integer, server_default="1")
    published: Mapped[int] = mapped_column(SmallInteger, server_default="0")  # 0=草稿 1=已发布
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    __table_args__ = (
        Index(
            "idx_runs_workflow",
            "workflow_id",
            "started_at",
            postgresql_ops={"started_at": "DESC"},
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, server_default=func.gen_random_uuid()
    )
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflows.id", ondelete="CASCADE"))
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID, ForeignKey("agent_sessions.id"))
    status: Mapped[int] = mapped_column(
        SmallInteger, server_default="0"
    )  # 0=运行中 1=成功 2=失败 3=超时
    current_node: Mapped[str | None] = mapped_column(String(64))
    # [{"node":"retrieve","status":"ok","latency_ms":820,"tokens":1200}]（TracePanel）
    node_traces: Mapped[dict | None] = mapped_column(JSONB)
    total_tokens: Mapped[int] = mapped_column(Integer, server_default="0")
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = created_at_col()
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
