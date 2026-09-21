# spec--项目骨架与基础设施（迭代 1）

> **版本**：v1.0 ｜ **日期**：2026-09-21 ｜ **状态**：待评审
> **上游文档**：[开发计划.md](../开发计划.md)（迭代 1）｜ [技术选型文档.md](../技术选型文档.md) ｜ [schema.sql](../schema.sql) ｜ CLAUDE.md
> **本迭代定位**：七个迭代的第 1 个，为后续所有迭代提供工程地基。

---

## 1. 背景

项目采用"Python 单体 MVP → 抽离 Java 管理域 → MCP/Skill 完整化"三阶段路线。迭代 1 是阶段①的第一步：不写任何业务功能，先把工程骨架、基础设施、数据表版本管理、前端骨架全部就位，让迭代 2（文档 Ingestion）开工时"有库存东西、有配置可用、有日志可查、有门禁兜底"。

## 2. 目标

从空目录到可运行骨架：

1. `git clone` 后按 README 操作，**30 分钟内**在新机器上复现"四件套运行 + 15 表建好 + 后端 `/healthz` 200 + 前端登录页可打开"；
2. 数据库结构由 Alembic 版本化管理，可重复 upgrade / downgrade；
3. 配置全部走 `.env`，切换环境零改码；
4. 所有代码经过 pre-commit + ruff 门禁，测试先行（TDD）。

## 3. 已确认决策（2026-09-21 brainstorming 结论）

| 决策点 | 结论 | 理由 |
|---|---|---|
| 仓库布局 | **Monorepo 单仓**：`backend/`（FastAPI）+ `frontend/`（React）+ `docs/` | 一人开发，迭代 4 加 Java 服务时再放 `admin/` |
| Python | **3.12** + uv（包管理）+ ruff（lint/format）+ pytest | AI 生态（torch / sentence-transformers）对 3.12 支持最成熟 |
| 前端 | **Vite + React + TypeScript + Ant Design** | 8 页管理台大量表格表单，AntD 开箱即用；TS 对齐后端 15 表结构 |
| 应用运行方式 | docker-compose **只管四件套基础设施**；后端 `uv run uvicorn`、前端 `pnpm dev` 本地跑 | 迭代 1 不做应用容器化，调试热重载最快 |
| PG 镜像 | `pgvector/pgvector:pg17` | 提前内置 pgvector 扩展（选型文档第 7 章的"轻量向量兜底"），无需额外配置 |
| 结构化日志 | **structlog**，JSON 输出 | 为迭代 6 TracePanel 的 trace 排查铺路 |

## 4. 能力清单（In Scope）

| # | 能力 | 说明 |
|---|---|---|
| C1 | Git 仓库 + 提交门禁 | 根目录初始化 git；pre-commit 钩子：ruff（backend）+ 通用检查（行尾/大文件/合并冲突标记） |
| C2 | FastAPI 空服务 | `GET /healthz` 返回 200 `{"status":"ok"}`；pytest + httpx 测试先行 |
| C3 | docker-compose 四件套 | PG17（pgvector 镜像）/ Qdrant ≥1.10 / Redis 7 / MinIO，均配 healthcheck，`docker compose up -d` 一键起 |
| C4 | 数据表版本管理 | SQLAlchemy 2.0 风格模型 + Alembic，迁移结果对齐 schema.sql 的 15 张表 |
| C5 | 配置与日志 | pydantic-settings 读 `.env`；structlog JSON 日志，level 由环境变量控制 |
| C6 | 前端骨架 + 登录页静态版 | Vite + React + TS + AntD；`/login` 路由静态页，视觉对齐 Pixso 设计稿（提交不做真实认证，仅表单校验 + mock） |

## 5. 非功能要求

- **环境切换零改码**：所有环境相关值（连接串、密钥、日志级别、端口）只出现在 `.env`；`.env` 不进 git，提交 `.env.example` 模板；
- **迁移可重复**：`alembic upgrade head` → `downgrade base` → 再 `upgrade head` 全程无报错；
- **TDD 铁律**：任何功能代码前先写失败测试（Red），禁止补测（遵循 CLAUDE.md）；
- **日志可机读**：JSON 格式，至少含 `time` / `level` / `event` 字段；
- **端口约定**（写死进 `.env.example`，避免后续猜）：PG `5432`、Qdrant `6333`、Redis `6379`、MinIO API `9000` / 控制台 `9001`、后端 `8000`、前端 `5173`。

## 6. 设计骨架

```
yunzhi/                        ← git 仓库根（Monorepo）
├── docker-compose.yml         ← 四件套基础设施
├── .env.example               ← 配置模板（.env 不入库）
├── .pre-commit-config.yaml
├── README.md                  ← 30 分钟复现指南
├── docs/                      ← 已有，规格文档持续放这里
├── backend/                   ← Python 3.12 + uv
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py            ← FastAPI 入口，挂 /healthz
│   │   ├── core/              ← settings.py、logging.py
│   │   ├── models/            ← SQLAlchemy 模型（15 表，按 schema.sql 五个模块分文件）
│   │   └── api/               ← 路由（本迭代只有 healthz）
│   ├── alembic/               ← 迁移脚本
│   └── tests/
└── frontend/                  ← Vite + React + TS + AntD
    └── src/pages/login/       ← 登录页静态版
```

**关键约定**：

- MinIO bucket 名：`yunzhi-files`（compose 用初始化容器自动建桶，不手动点控制台）；
- 数据库名 / 用户：`yunzhi` / `yunzhi`；
- Alembic 只管理 schema.sql 的 15 张表；LangGraph checkpoint 表（`checkpoints` 等）由 PostgresSaver 在迭代 3 自建，**不在本迭代迁移内**；
- 前端 lint 走 `pnpm lint`（eslint + prettier），不进 pre-commit（迭代 1 保持门禁轻量，后端 ruff 为主）。

## 7. Out of Scope（本迭代明确不做）

- 任何业务接口（上传 / 检索 / 对话 / 用户 CRUD）；
- 真实登录认证（登录页只静态，JWT 在迭代 4）；
- 后端 / 前端的 Docker 化（应用容器化在迭代 5 随 Nginx 一起做）；
- Nginx、Java 服务、MinerU；
- 远端 CI 流水线（GitHub Actions 等，本地 pre-commit 已够用）。
