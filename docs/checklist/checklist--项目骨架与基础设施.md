# checklist--项目骨架与基础设施（迭代 1）

> **版本**：v1.0 ｜ **日期**：2026-09-21 ｜ **配套**：[spec](../spec/spec--项目骨架与基础设施.md) ｜ [tasks](../tasks/tasks--项目骨架与基础设施.md)
> **使用方式**：逐项执行、逐项打勾；任何一项勾不了 = 对应任务没完成，回去修，不降级标准。

---

## A. 仓库与门禁（T1）

- [ ] `git clone` 到干净目录成功，仓库含 `backend/` `frontend/` `docs/` `docker-compose.yml`
- [ ] `pre-commit install` 后，提交一个含 ruff 错误的 Python 文件**被拦截**
- [ ] `.env` 在 `.gitignore` 中，`git status` 看不到它；`.env.example` 已提交

## B. 后端工程（T2–T5）

- [ ] `cd backend && uv sync` 零报错
- [ ] `uv run ruff check .` 零告警
- [ ] `uv run pytest` 全绿（≥ 6 个用例：settings ×3、logging ×1、healthz ×1、占位 ×1）
- [ ] `uv run uvicorn app.main:app` 启动后，`curl http://localhost:8000/healthz` 返回 200 且 body 为 `{"status":"ok"}`
- [ ] 启动控制台输出的日志是**合法 JSON**，含 `time` / `level` / `event` 三字段
- [ ] 把 `.env` 里 `LOG_LEVEL` 改为 `DEBUG`，重启后日志级别变化，**全程未改任何代码**
- [ ] 删掉 `.env` 里某个必填项（如 `DATABASE_URL`），启动立即报 ValidationError（而不是运行到一半才挂）

## C. 基础设施（T6）

- [ ] `docker compose up -d` 一条命令起全部服务
- [ ] `docker compose ps` 显示 PG / Qdrant / Redis / MinIO **四个全部 healthy**
- [ ] `docker compose down && docker compose up -d` 后数据卷还在（PG 里建的测试数据未丢）
- [ ] PG 内执行 `CREATE EXTENSION IF NOT EXISTS vector;` 成功
- [ ] MinIO 控制台 `http://localhost:9001` 可登录，`yunzhi-files` bucket 已存在（无需手动建）

## D. 数据表迁移（T7–T9）

- [ ] `uv run alembic upgrade head` 后，PG 中 `\dt` **恰好 15 张表**（不含 checkpoints 系列）
- [ ] 15 张表与 `docs/schema.sql` 逐表一致：表名、字段、默认值、外键级联规则
- [ ] 关键索引存在：`idx_documents_kb`、`idx_chunks_parent`、`idx_sessions_agent_user`、`idx_audit_user_time`
- [ ] `alembic downgrade base` 后表清空，再 `alembic upgrade head` 重建成功，全程零报错

## E. 前端（T10–T11）

- [ ] `cd frontend && pnpm i && pnpm dev` 后可访问 `http://localhost:5173`
- [ ] `pnpm lint` 零报错；`pnpm build` 成功
- [ ] `/login` 页面与 Pixso 设计稿登录页并排对照：布局、配色、间距一致
- [ ] 登录表单空提交出现必填校验提示；填写后提交走 mock（不请求后端）

## F. 端到端验收（T12–T13，e2e 必做）

- [ ] **e2e-1 新机器复现**：在干净临时目录从零执行 README——clone → `cp .env.example .env` → `docker compose up -d` → `uv sync` → `alembic upgrade head` → 启动后端 → `/healthz` 200 → 启动前端 → 登录页打开。**全程 ≤ 30 分钟，无一步需要README 之外的口头补充**
- [ ] **e2e-2 环境切换**：复制 `.env` 为 `.env.test`，只改端口和库名（如 PG 改 55432、库名 `yunzhi_test`），`docker compose --env-file .env.test up -d` + `uv run alembic upgrade head` 同样跑通，验证"切环境零改码"
