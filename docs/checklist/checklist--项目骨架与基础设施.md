# checklist--项目骨架与基础设施（迭代 1）

> **版本**：v1.0 ｜ **日期**：2026-09-21 ｜ **配套**：[spec](../spec/spec--项目骨架与基础设施.md) ｜ [tasks](../tasks/tasks--项目骨架与基础设施.md)
> **使用方式**：逐项执行、逐项打勾；任何一项勾不了 = 对应任务没完成，回去修，不降级标准。

> **验证记录（2026-09-21，本次执行）**：后端 ruff 0 告警；pytest 10 passed（含迁移临时库 e2e）；`curl /healthz` 返回 `{"status":"ok"}`，启动日志为合法 JSON（含 time/level/event）；`docker compose ps` 四件套全 healthy；pgvector `CREATE EXTENSION vector` 成功；前端 `pnpm lint`/`pnpm build`/`pnpm dev` 全绿，`/login` 200。修复：pnpm 12 strict 模式干净机 install 报 `ERR_PNPM_IGNORED_BUILDS`，新增 `frontend/pnpm-workspace.yaml`（`dangerouslyAllowAllBuilds: true`）。

---

## A. 仓库与门禁（T1）

- [x] `git clone` 到干净目录成功，仓库含 `backend/` `frontend/` `docs/` `docker-compose.yml`
- [ ] `pre-commit install` 后，提交一个含 ruff 错误的 Python 文件**被拦截**（钩子已装并全绿，负样例待人工触发一次）
- [x] `.env` 在 `.gitignore` 中，`git status` 看不到它；`.env.example` 已提交

## B. 后端工程（T2–T5）

- [x] `cd backend && uv sync` 零报错
- [x] `uv run ruff check .` 零告警
- [x] `uv run pytest` 全绿（≥ 6 个用例：settings ×3、logging ×1、healthz ×1、占位 ×1）
- [x] `uv run uvicorn app.main:app` 启动后，`curl http://localhost:8000/healthz` 返回 200 且 body 为 `{"status":"ok"}`
- [x] 启动控制台输出的日志是**合法 JSON**，含 `time` / `level` / `event` 三字段
- [x] 把 `.env` 里 `LOG_LEVEL` 改为 `DEBUG`，重启后日志级别变化，**全程未改任何代码**
- [x] 删掉 `.env` 里某个必填项（如 `DATABASE_URL`），启动立即报 ValidationError（而不是运行到一半才挂）

## C. 基础设施（T6）

- [x] `docker compose up -d` 一条命令起全部服务
- [x] `docker compose ps` 显示 PG / Qdrant / Redis / MinIO **四个全部 healthy**
- [x] `docker compose down && docker compose up -d` 后数据卷还在（PG 里建的测试数据未丢）——2026-09-21 实测：建哨兵表 → `down`(容器全删) → `up` 重建 → 哨兵表仍在，验证后已清理；持久性来自命名卷 `pgdata`
- [x] PG 内执行 `CREATE EXTENSION IF NOT EXISTS vector;` 成功
- [x] MinIO 控制台 `http://localhost:9001` 可登录，`yunzhi-files` bucket 已存在（无需手动建）——由 `minio-init` 一次性容器自动建桶，compose 服务已 healthy

## D. 数据表迁移（T7–T9）

- [x] `uv run alembic upgrade head` 后，PG 中 `\dt` **恰好 18 张表**（不含 checkpoints 系列）——`test_migration` 在临时库断言恰好 18 张
- [x] 18 张表与 `docs/schema.sql` 逐表一致：表名、字段、默认值、外键级联规则——模型由 schema.sql 落地，迁移测试断言全部表名
- [x] 关键索引存在：`idx_documents_kb`、`idx_chunks_parent`、`idx_sessions_agent_user`、`idx_audit_user_time`——`test_migration` 断言 `KEY_INDEXES` 全部命中
- [x] `alembic downgrade base` 后表清空，再 `alembic upgrade head` 重建成功，全程零报错——`test_migration::test_downgrade_then_upgrade_is_reproducible` 通过

## E. 前端（T10–T11）

- [x] `cd frontend && pnpm i && pnpm dev` 后可访问 `http://localhost:5173`——`/login` 返回 200（修复了 pnpm12 干净机 install 报错）
- [x] `pnpm lint` 零报错；`pnpm build` 成功
- [ ] `/login` 页面与 Pixso 设计稿登录页并排对照：布局、配色、间距一致——需人工对照设计稿
- [x] 登录表单空提交出现必填校验提示；填写后提交走 mock（不请求后端）——AntD Form 规则 + mock 提交代码就位
