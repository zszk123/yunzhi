# tasks--项目骨架与基础设施（迭代 1）

> **版本**：v1.0 ｜ **日期**：2026-09-21 ｜ **配套**：[spec--项目骨架与基础设施.md](../spec/spec--项目骨架与基础设施.md) ｜ [checklist--项目骨架与基础设施.md](../checklist/checklist--项目骨架与基础设施.md)
> **执行纪律**：遵循 CLAUDE.md 的 TDD 铁律——每个标 [TDD] 的任务先写失败测试再写实现；任何任务导致已有测试变红，立即修复，不进入下一个任务。

---

## 任务列表

### T1. Git 仓库初始化 + 提交门禁
- **产出物**：根目录 git 仓库、`.gitignore`（Python / Node / .env / IDE）、`.pre-commit-config.yaml`、README 骨架
- **内容**：`git init`；pre-commit 钩子含 ruff（backend）+ 通用检查（trailing-whitespace / end-of-file-fixer / check-added-large-files / check-merge-conflict）
- **验证**：随便改个文件提交，钩子触发并能拦住一个故意的 ruff 错误

### T2. [TDD] backend uv 工程初始化
- **产出物**：`backend/pyproject.toml`、uv lock、pytest 配置（`--basetemp=.pytest_tmp`，避免沙箱删 TEMP 目录被拦）
- **内容**：依赖基线 fastapi / uvicorn / pydantic-settings / structlog / sqlalchemy / alembic / psycopg；dev 依赖 pytest / httpx / ruff
- **验证**：`uv sync` 成功；`uv run pytest` 跑通一个占位测试

### T3. [TDD] 配置管理 settings.py
- **产出物**：`backend/app/core/settings.py` + `.env.example`
- **内容**：pydantic-settings BaseSettings，字段覆盖 spec 第 5 节全部端口/连接串/密钥/日志级别；缺必填项启动即报错
- **测试**：① 从临时 env 文件加载得到正确值 ② 缺必填字段时 ValidationError ③ 默认值生效（如 LOG_LEVEL=INFO）
- **验证**：测试全绿；改 `.env` 值后重新加载生效，代码零改动

### T4. [TDD] 结构化日志
- **产出物**：`backend/app/core/logging.py`
- **内容**：structlog 配置，JSON 输出，字段含 time / level / event；level 从 settings 读
- **测试**：捕获日志输出，断言是合法 JSON 且含三个必需字段、level 随配置变化
- **验证**：测试全绿

### T5. [TDD] FastAPI 服务 + /healthz
- **产出物**：`backend/app/main.py`、`backend/app/api/healthz.py`
- **内容**：先写 httpx 测试（断言 200 + `{"status":"ok"}`），再写最小实现
- **验证**：`uv run uvicorn app.main:app` 启动，`curl localhost:8000/healthz` 返回 200；启动日志为 JSON

### T6. docker-compose 四件套
- **产出物**：根目录 `docker-compose.yml`
- **内容**：PG（pgvector/pgvector:pg17）/ Qdrant / Redis 7 / MinIO，全部配 healthcheck；MinIO 附初始化容器自动建 `yunzhi-files` bucket；数据卷命名持久化
- **验证**：`docker compose up -d` 后 `docker compose ps` 四个服务全部 healthy；MinIO 控制台（:9001）可登录且 bucket 已存在；PG 内 `CREATE EXTENSION vector;` 可用

### T7. SQLAlchemy 模型（15 表）
- **产出物**：`backend/app/models/`，按 schema.sql 五个模块分文件（user / kb / agent / session / audit）
- **内容**：SQLAlchemy 2.0 Mapped 风格，逐表对齐 schema.sql 的字段、默认值、索引、外键级联；JSONB / TEXT[] / UUID 类型用对
- **验证**：模型可 import 无错；与 schema.sql 逐表人工 diff 一致

### T8. [TDD] Alembic 初始化 + 首个迁移
- **产出物**：`backend/alembic/`、env.py 从 settings 读连接串、首个迁移脚本
- **内容**：迁移脚本由 models 自动生成后人工校对（对齐 15 表 + 全部索引）
- **测试**：对临时库执行 upgrade head，断言 `\dt` 恰好 15 张表、关键索引存在
- **验证**：测试全绿

### T9. 迁移可重复性验证
- **产出物**：验证记录（写入 checklist）
- **内容**：`upgrade head` → `downgrade base` → 再 `upgrade head`
- **验证**：三段命令全程零报错；最终 15 表齐全

### T10. frontend 骨架（Vite + React + TS + AntD）
- **产出物**：`frontend/` 工程，含 eslint + prettier、`pnpm lint` 脚本、路由骨架
- **内容**：`pnpm create vite`（react-ts 模板）；接入 antd、react-router；目录按 pages 划分
- **验证**：`pnpm dev` 打开默认页；`pnpm build` 通过

### T11. 登录页静态版
- **产出物**：`frontend/src/pages/login/`
- **内容**：对照 Pixso 设计稿登录页还原视觉（布局 / 配色 / 间距）；AntD Form 做必填校验；提交仅 mock（console 输出 + 跳转占位），不接后端
- **验证**：页面与设计稿并排对照一致；空表单提交出现校验提示

### T12. 接入主流程
- **产出物**：README 完整版（30 分钟复现指南）+ 根目录便捷脚本（可选 make / just / npm script）
- **内容**：把 T1–T11 串成一条命令链：clone → `cp .env.example .env` → `docker compose up -d` → `cd backend && uv sync && uv run alembic upgrade head && uv run uvicorn` → `cd frontend && pnpm i && pnpm dev`
- **验证**：README 步骤无断点，缺一步都走不通的那种"想当然"被消灭

### T13. 端到端验证
- **产出物**：checklist 全部勾完
- **内容**：按 checklist--项目骨架与基础设施.md 逐项执行，重点是 e2e 项——**在一个干净的临时目录模拟新机器**，从零 clone 到登录页打开全程计时
- **验证**：checklist 全勾；e2e ≤ 30 分钟；任何一步卡住就回到对应任务修

---

## 依赖顺序

```
T1 → T2 → T3 → T4 → T5（后端线，T3/T4 可并行）
T6（基础设施线，与 T2-T5 可并行，但 T8 依赖它）
T5 + T6 → T7 → T8 → T9（数据层线）
T10 → T11（前端线，完全独立，可最早并行）
全部 → T12 → T13
```

**建议节奏**（每周 10–12h，2 周）：第 1 周 T1–T6 + T10 启动；第 2 周 T7–T9、T11、T12–T13。
