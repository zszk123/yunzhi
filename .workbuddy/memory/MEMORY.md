# 项目长期记忆 —— yunzhi（知识库 + LangGraph Agent 系统）

## 项目定位
求职简历项目：跑通"文档上传→解析分块→混合检索→Agent 对话/工作流"全链路，8 页设计稿，18 周在职业余开发（每周 10-12h）。三阶段：① Python 单体 MVP ② 抽 Java 管理域 ③ MCP/Skill + 评测交付。里程碑 M1/M2/M3，砍范围不砍里程碑。

## 技术栈（已定，勿反复讨论）
- Monorepo：`backend/`（FastAPI, Python 3.12, uv, ruff, pytest）+ `frontend/`（Vite+React+TS+AntD, pnpm）+ `docs/`；迭代 4 加 `admin/`（Spring Boot 多模块）
- 基础设施：docker-compose 四件套 PG17(pgvector/pgvector:pg17) / Qdrant≥1.10 / Redis 7 / MinIO；应用本地跑（uvicorn / pnpm dev），容器化留迭代 5
- 数据：Alembic 管 schema.sql 15 表；checkpoints 表由 LangGraph PostgresSaver 自建；MinIO bucket `yunzhi-files`；DB 名/用户 yunzhi/yunzhi
- 端口：PG 5432 / Qdrant 6333 / Redis 6379 / MinIO 9000+9001 / 后端 8000 / 前端 5173
- 配置：pydantic-settings 读 .env（提交 .env.example）；日志 structlog JSON（time/level/event）
- AI 主线：LangGraph + OpenAI 兼容协议 + Anthropic Provider；BGE-M3 + bge-reranker-v2-m3；Qdrant sparse+dense+RRF

## 协作规则（CLAUDE.md + 用户约定）
- SDD+TDD：每迭代先产出 `docs/spec|tasks|checklist/` 下的 `xx--模块名.md` 三件套，用户评审批准后才写代码；测试先行，禁止补测
- spec 写背景/目标/能力清单/非功能要求/设计骨架/Out of Scope，不写实现细节
- tasks 5~15 个，末尾必有"接入主流程"+"端到端验证"
- checklist 每项可勾选可观测，至少一条 e2e；本迭代 e2e 基准：干净目录 30 分钟复现
- 新需求先 brainstorming；pytest 加 `--basetemp=.pytest_tmp`（沙箱拦 TEMP 删除）

## 关键资产
- 文档链：`docs/技术选型文档.md` → `docs/schema.sql`（15 表）→ `docs/开发计划.md`（7 迭代）→ 迭代级三件套
- Pixso 设计稿 8 页：fileKey BE6geK8QYPj3TqbLx2x5ew（登录 10:1127 / Agent 创建 10:2407 / 概览 7:342 / 文档列表 2:465 / 检索调试 10:1 / 数据源 10:464 / Agent 对话 10:1217 / 工作流 10:1691）
- Pixso MCP：http://127.0.0.1:3667/mcp（需 Pixso Desktop 运行且文件打开）

## 当前进度
- 迭代 1 三件套已产出（2026-09-21），**待用户评审 spec**，批准后按 tasks T1-T13 执行 TDD 实现
