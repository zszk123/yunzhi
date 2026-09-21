# yunzhi —— 知识库 + LangGraph Agent 系统

> 求职简历项目：跑通"文档上传 → 解析分块 → 混合检索 → Agent 对话/工作流"全链路。
> 文档链：[技术选型](docs/技术选型文档.md) → [schema.sql](docs/schema.sql) → [开发计划](docs/开发计划.md) → 迭代级三件套（docs/spec|tasks|checklist/）

## 快速开始（30 分钟复现）

> 本节在 T12 补全为无断点命令链。当前迭代 1 进行中。

## 仓库结构

```
yunzhi/
├── docker-compose.yml   # 四件套基础设施：PG17(pgvector) / Qdrant / Redis / MinIO
├── backend/             # FastAPI · Python 3.12 · uv · SQLAlchemy + Alembic
├── frontend/            # Vite + React + TypeScript + Ant Design
└── docs/                # 规格文档（spec / tasks / checklist）
```
