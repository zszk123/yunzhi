# yunzhi —— 知识库 + LangGraph Agent 系统

> 求职简历项目：跑通"文档上传 → 解析分块 → 混合检索 → Agent 对话/工作流"全链路。
> 文档链：[技术选型](docs/技术选型文档.md) → [schema.sql](docs/schema.sql) → [开发计划](docs/开发计划.md) → 迭代级三件套（docs/spec|tasks|checklist/）

## 快速开始（30 分钟复现）

前置：Docker Desktop、uv（`pip install uv` 或见 [uv 文档](https://docs.astral.sh/uv/)）、Node.js ≥ 20（含 corepack）。

```bash
# 1. 克隆并准备配置（.env 给 docker-compose 用，backend/.env 给 FastAPI 用）
git clone <repo-url> yunzhi && cd yunzhi
cp .env.example .env
cp .env.example backend/.env

# 2. 起基础设施四件套（PG17+pgvector / Qdrant / Redis / MinIO）
docker compose up -d
docker compose ps        # 四个服务全部 healthy 才算好

# 3. 后端：装依赖 → 建 18 张表 → 启动
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
# 验证：浏览器/curl 访问 http://127.0.0.1:8000/healthz → {"status":"ok"}

# 4. 前端：另开一个终端
cd frontend
corepack pnpm install    # 或已装 pnpm 则直接 pnpm install
pnpm dev
# 验证：访问 http://localhost:5173/login 看到登录页
```

## 常用命令

```bash
# 后端（backend/ 目录下）
uv run pytest                 # 跑全部测试（含迁移的临时库 e2e）
uv run ruff check .           # lint
uv run alembic upgrade head   # 应用最新迁移
uv run alembic downgrade base # 回滚到空库（验证可重复性）

# 前端（frontend/ 目录下）
pnpm dev / pnpm build / pnpm lint

# 提交门禁（仓库根目录）
uv --directory backend run pre-commit install
```

## 仓库结构

```
yunzhi/
├── docker-compose.yml   # 四件套基础设施：PG17(pgvector) / Qdrant / Redis / MinIO
├── backend/             # FastAPI · Python 3.12 · uv · SQLAlchemy + Alembic
│   ├── app/             # core(配置/日志) · api(路由) · models(18 表模型)
│   ├── alembic/         # 迁移脚本（env.py 从 settings 读连接串）
│   └── tests/           # pytest（settings/logging/healthz/migration）
├── frontend/            # Vite + React + TypeScript + Ant Design
└── docs/                # 规格文档（spec / tasks / checklist）
```

## Windows 中文环境注意事项（踩过的坑）

- **连接串用 `127.0.0.1` 不用 `localhost`**：psycopg 走 localhost 可能 IPv6 回退挂死；
- **`backend/alembic.ini` 必须纯 ASCII**：alembic 按 locale（GBK）读 ini，中文注释会 UnicodeDecodeError；
- **MinIO 镜像走 `quay.io/minio/...`**：docker.io 的 minio 被国内镜像站 403；
- pnpm 拉不动时设 `COREPACK_NPM_REGISTRY=https://registry.npmmirror.com`，或 frontend/.npmrc 已内置 npmmirror。
