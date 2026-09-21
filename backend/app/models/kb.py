"""模块二：知识库域（概览 / 文档列表 / 数据源 / 检索调试）。

schema.sql: knowledge_bases / documents / document_chunks / data_sources /
parse_tasks / retrieval_logs。

关键设计（schema.sql 注释的代码化）：
- 1 个 KB = 1 个 Qdrant collection（kb_{id}），embedding_model 显式落库——换模型=全量重嵌入；
- Parent-Child 分块：child 向量进 Qdrant 召回，命中后回 PG 取 parent 全文；
- 向量存 Qdrant、正文存 PG，靠 qdrant_point_id 单向关联，避免双写不一致。
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    UUID,
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BigIdBase, created_at_col, updated_at_col


class KnowledgeBase(BigIdBase):
    __tablename__ = "knowledge_bases"

    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    embedding_model: Mapped[str] = mapped_column(String(64), server_default="bge-m3")
    # {"parent_tokens":1024,"child_tokens":256,"overlap":64,"separators":["\n\n","。"]}
    chunk_strategy: Mapped[dict] = mapped_column(JSONB, server_default="'{}'::jsonb")
    status: Mapped[int] = mapped_column(SmallInteger, server_default="1")
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()


class Document(BigIdBase):
    __tablename__ = "documents"
    __table_args__ = (
        Index("idx_documents_kb", "kb_id"),
        Index("idx_documents_status", "parse_status"),
    )

    kb_id: Mapped[int] = mapped_column(ForeignKey("knowledge_bases.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(256))
    file_name: Mapped[str | None] = mapped_column(String(256))
    file_type: Mapped[str | None] = mapped_column(String(16))  # pdf / docx / md / xlsx / html
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    mime_type: Mapped[str | None] = mapped_column(String(128))
    storage_key: Mapped[str] = mapped_column(String(512))  # MinIO 对象 key
    parse_status: Mapped[int] = mapped_column(
        SmallInteger, server_default="0"
    )  # 0=待解析 1=解析中 2=已入库 3=失败
    parse_error: Mapped[str | None] = mapped_column(Text)
    chunk_count: Mapped[int] = mapped_column(Integer, server_default="0")
    version: Mapped[int] = mapped_column(Integer, server_default="1")  # 同名重复上传递增
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()


class DocumentChunk(BigIdBase):
    __tablename__ = "document_chunks"
    __table_args__ = (
        Index("idx_chunks_doc", "document_id"),
        Index("idx_chunks_parent", "parent_chunk_id"),
    )

    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    # child 指向 parent；parent 该列为 NULL
    parent_chunk_id: Mapped[int | None] = mapped_column(ForeignKey("document_chunks.id"))
    chunk_type: Mapped[int] = mapped_column(SmallInteger)  # 1=parent（不进向量库） 2=child
    chunk_index: Mapped[int] = mapped_column(Integer)  # 文档内顺序
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int | None] = mapped_column(Integer)
    # 页码/标题层级/表格标注等；列名 metadata 与 Declarative 保留字冲突，属性名用 extra
    extra: Mapped[dict | None] = mapped_column("metadata", JSONB, server_default="'{}'::jsonb")
    # child 块在 Qdrant 里的 point id；parent 为 NULL
    qdrant_point_id: Mapped[uuid.UUID | None] = mapped_column(UUID)
    created_at: Mapped[datetime] = created_at_col()


class DataSource(BigIdBase):
    __tablename__ = "data_sources"

    name: Mapped[str] = mapped_column(String(128))
    type: Mapped[str] = mapped_column(String(32))  # s3 / webdav / sharepoint / webhook
    config: Mapped[dict] = mapped_column(JSONB)  # 密钥字段应用层加密后存入
    sync_interval_sec: Mapped[int] = mapped_column(Integer, server_default="3600")
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sync_status: Mapped[int] = mapped_column(
        SmallInteger, server_default="0"
    )  # 0=正常 1=同步中 2=异常（设计稿红色异常卡）
    error_message: Mapped[str | None] = mapped_column(Text)
    target_kb_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_bases.id"))
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()


class ParseTask(BigIdBase):
    """解析任务状态账本：Redis 做队列，这里做可追溯、可重试的账本。"""

    __tablename__ = "parse_tasks"
    __table_args__ = (Index("idx_parse_tasks_status", "status"),)

    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    task_type: Mapped[int] = mapped_column(SmallInteger, server_default="1")  # 1=首次 2=重新
    status: Mapped[int] = mapped_column(
        SmallInteger, server_default="0"
    )  # 0=排队 1=执行中 2=成功 3=失败
    worker_id: Mapped[str | None] = mapped_column(String(64))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created_at_col()


class RetrievalLog(BigIdBase):
    """检索调试历史（设计稿检索调试页右侧历史记录）。"""

    __tablename__ = "retrieval_logs"

    kb_id: Mapped[int] = mapped_column(ForeignKey("knowledge_bases.id"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    query: Mapped[str] = mapped_column(Text)
    strategy: Mapped[str] = mapped_column(String(16))  # dense / sparse / hybrid
    top_k: Mapped[int] = mapped_column(Integer, server_default="5")
    rerank_enabled: Mapped[int] = mapped_column(SmallInteger, server_default="1")
    # [{"doc_id":1,"chunk_id":99,"score_dense":0.82,"score_sparse":0.76,"score_final":0.88}]
    results: Mapped[dict] = mapped_column(JSONB)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = created_at_col()
