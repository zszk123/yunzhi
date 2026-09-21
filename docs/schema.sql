-- =============================================================
-- 知识库 + LangGraph Agent 系统 · PostgreSQL 17 建库脚本
-- 配套文档：技术选型文档.md（第 7 章数据库选型 / 第 9-10 章解析与向量模型）
--
-- 设计原则：
--   1. 动态配置用 JSONB（配 GIN 索引可按内部字段查询）；
--      需要按字段过滤/关联的业务字段用普通列。
--   2. 向量存 Qdrant，正文存 PG：chunks 表用 qdrant_point_id 关联，
--      Qdrant payload 只放引用，避免两边数据双写不一致。
--   3. 会话主键用 UUID，直接作为 LangGraph PostgresSaver 的 thread_id。
--   4. 阶段① 全部表在同一个库；阶段② 拆双服务时，
--      可按 PostgreSQL schema 划分（admin / ai）做权限隔离，表结构不变。
-- =============================================================

-- ------------------------------------------------------------
-- 模块一：用户与权限（对应设计稿：登录页）
-- ------------------------------------------------------------

CREATE TABLE users (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username      VARCHAR(64)  NOT NULL UNIQUE,
    email         VARCHAR(128) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,              -- argon2/bcrypt，绝不存明文
    avatar_url    VARCHAR(512),
    status        SMALLINT     NOT NULL DEFAULT 1,    -- 1=启用 0=禁用
    last_login_at TIMESTAMPTZ,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

COMMENT ON TABLE users IS '用户表（SSO 登录后本地落一份影子账号）';

CREATE TABLE roles (
    id   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(32) NOT NULL UNIQUE,                 -- admin / editor / viewer
    name VARCHAR(64) NOT NULL
);

CREATE TABLE user_roles (
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- ------------------------------------------------------------
-- 模块二：知识库域（对应设计稿：知识库概览 / 文档列表 / 数据源接入 / 检索调试）
-- ------------------------------------------------------------

CREATE TABLE knowledge_bases (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            VARCHAR(128) NOT NULL,
    description     TEXT,
    owner_id        BIGINT NOT NULL REFERENCES users(id),
    -- 记录本库使用的嵌入模型：换模型 = 全量重嵌入，必须显式落库
    embedding_model VARCHAR(64)  NOT NULL DEFAULT 'bge-m3',
    -- 分块策略：{"parent_tokens":1024,"child_tokens":256,"overlap":64,"separators":["\n\n","。"]}
    chunk_strategy  JSONB        NOT NULL DEFAULT '{}',
    status          SMALLINT     NOT NULL DEFAULT 1,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

COMMENT ON TABLE knowledge_bases IS '知识库（1 个 KB 对应 1 个 Qdrant collection，命名 kb_{id}）';

CREATE TABLE documents (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    kb_id        BIGINT       NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    title        VARCHAR(256) NOT NULL,
    file_name    VARCHAR(256),
    file_type    VARCHAR(16),                         -- pdf / docx / md / xlsx / html
    file_size    BIGINT,
    mime_type    VARCHAR(128),
    storage_key  VARCHAR(512) NOT NULL,               -- MinIO 对象 key，如 kb1/2026/09/xxx.pdf
    parse_status SMALLINT     NOT NULL DEFAULT 0,     -- 0=待解析 1=解析中 2=已入库 3=失败
    parse_error  TEXT,
    chunk_count  INTEGER      NOT NULL DEFAULT 0,
    version      INTEGER      NOT NULL DEFAULT 1,     -- 同名重复上传时递增
    uploaded_by  BIGINT       REFERENCES users(id),
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX idx_documents_kb     ON documents (kb_id);
CREATE INDEX idx_documents_status ON documents (parse_status);

COMMENT ON TABLE documents IS '文档元数据（原始文件在 MinIO，这里只存 key 和状态）';

CREATE TABLE document_chunks (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id     BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    parent_chunk_id BIGINT REFERENCES document_chunks(id),  -- child 指向 parent；parent 该列为 NULL
    chunk_type      SMALLINT   NOT NULL,                     -- 1=parent（父块，不进向量库） 2=child（子块，进向量库）
    chunk_index     INTEGER    NOT NULL,                     -- 在文档内的顺序
    content         TEXT       NOT NULL,                     -- 块正文（检索命中后取 parent 全文靠它）
    token_count     INTEGER,
    metadata        JSONB      DEFAULT '{}',                 -- 页码/标题层级/表格标注等
    -- child 块在 Qdrant 里的 point id；parent 为 NULL
    qdrant_point_id UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_chunks_doc    ON document_chunks (document_id);
CREATE INDEX idx_chunks_parent ON document_chunks (parent_chunk_id);

COMMENT ON TABLE document_chunks IS 'Parent-Child 分块：child 向量进 Qdrant 召回，命中后回 PG 取 parent 全文喂给 LLM';

CREATE TABLE data_sources (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name               VARCHAR(128) NOT NULL,
    type               VARCHAR(32)  NOT NULL,            -- s3 / webdav / sharepoint / webhook
    config             JSONB        NOT NULL,            -- 连接配置；密钥字段应用应用层加密后存入
    sync_interval_sec  INTEGER      NOT NULL DEFAULT 3600,
    last_sync_at       TIMESTAMPTZ,
    sync_status        SMALLINT     NOT NULL DEFAULT 0,  -- 0=正常 1=同步中 2=异常（对应设计稿红色异常卡）
    error_message      TEXT,
    target_kb_id       BIGINT       REFERENCES knowledge_bases(id),
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE parse_tasks (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    task_type   SMALLINT NOT NULL DEFAULT 1,              -- 1=首次解析 2=重新解析
    status      SMALLINT NOT NULL DEFAULT 0,              -- 0=排队 1=执行中 2=成功 3=失败
    worker_id   VARCHAR(64),                              -- 消费任务的 Python worker 标识
    started_at  TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    error       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_parse_tasks_status ON parse_tasks (status);

COMMENT ON TABLE parse_tasks IS '解析任务持久化：Redis 做队列，这里做状态账本（可追溯、可重试）';

CREATE TABLE retrieval_logs (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    kb_id          BIGINT      NOT NULL REFERENCES knowledge_bases(id),
    user_id        BIGINT      REFERENCES users(id),
    query          TEXT        NOT NULL,
    strategy       VARCHAR(16) NOT NULL,                 -- dense / sparse / hybrid（检索调试页的策略 chips）
    top_k          INTEGER     NOT NULL DEFAULT 5,
    rerank_enabled SMALLINT    NOT NULL DEFAULT 1,
    -- 命中明细：[{"doc_id":1,"chunk_id":99,"score_dense":0.82,"score_sparse":0.76,"score_final":0.88}]
    results        JSONB       NOT NULL,
    latency_ms     INTEGER,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE retrieval_logs IS '检索调试历史（对应设计稿检索调试页右侧历史记录）';

-- ------------------------------------------------------------
-- 模块三：Skill 与 Agent（对应设计稿：Agent 创建页）
-- ------------------------------------------------------------

CREATE TABLE skills (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            VARCHAR(128) NOT NULL,
    version         VARCHAR(32)  NOT NULL DEFAULT '1.0.0',
    description     TEXT,
    prompt_template TEXT         NOT NULL,               -- system prompt 模板，支持 {{变量}} 占位
    tool_names      TEXT[]       NOT NULL DEFAULT '{}',  -- 预挂载工具，如 {kb.search, web.search}
    output_schema   JSONB,                               -- 输出格式约束（JSON Schema）
    enabled         SMALLINT     NOT NULL DEFAULT 1,     -- Java 域启停开关
    created_by      BIGINT       REFERENCES users(id),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (name, version)
);

COMMENT ON TABLE skills IS 'Skill = 提示词模板 + 工具组合包（Java 域注册管理，Python 运行时加载）';

CREATE TABLE agents (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name         VARCHAR(128) NOT NULL,
    type         SMALLINT     NOT NULL,                  -- 1=对话型 2=会话流（工作流）型，对应创建页弹层两个选项
    description  TEXT,
    owner_id     BIGINT       NOT NULL REFERENCES users(id),
    -- {"provider":"openai_compatible","base_url":"...","model":"qwen-max","temperature":0.7,"max_tokens":4096}
    model_config JSONB        NOT NULL DEFAULT '{}',
    system_prompt TEXT,
    status       SMALLINT     NOT NULL DEFAULT 1,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE agent_skills (
    agent_id BIGINT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    skill_id BIGINT NOT NULL REFERENCES skills(id)    ON DELETE CASCADE,
    PRIMARY KEY (agent_id, skill_id)
);

CREATE TABLE agent_kbs (
    agent_id BIGINT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    kb_id    BIGINT NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    PRIMARY KEY (agent_id, kb_id)
);

COMMENT ON TABLE agent_kbs IS 'Agent 挂载哪些知识库（运行时把 kb.search 工具限定到这些库）';

-- ------------------------------------------------------------
-- 模块四：会话与运行（对应设计稿：Agent 对话页 / Agent 工作流页）
-- ------------------------------------------------------------

CREATE TABLE agent_sessions (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    -- 这个 UUID 直接作为 LangGraph PostgresSaver 的 thread_id：
    -- checkpoint 由 PostgresSaver 自动建表管理（表名 checkpoints 等），不在本脚本内
    agent_id        BIGINT      NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    user_id         BIGINT      NOT NULL REFERENCES users(id),
    title           VARCHAR(256) NOT NULL DEFAULT '新会话',  -- 首条消息后由 LLM 生成标题
    context         JSONB       DEFAULT '{}',                -- 会话级变量（如当前案件号）
    message_count   INTEGER     NOT NULL DEFAULT 0,
    last_message_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_sessions_agent_user ON agent_sessions (agent_id, user_id, last_message_at DESC);

COMMENT ON TABLE agent_sessions IS '对话会话（对话页左侧会话列表）';

CREATE TABLE agent_messages (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    session_id  UUID   NOT NULL REFERENCES agent_sessions(id) ON DELETE CASCADE,
    role        SMALLINT NOT NULL,                        -- 1=user 2=assistant 3=tool/system
    content     TEXT     NOT NULL,
    reasoning   TEXT,                                     -- 思考过程（可选展示）
    -- 工具调用链：[{"name":"kb.search","args":{...},"latency_ms":420}]（对话页工具调用卡）
    tool_calls  JSONB,
    -- 引用来源：[{"doc_id":1,"chunk_id":99,"quote":"...","score":0.88}]（AI 回答下方的引用 chips）
    citations   JSONB,
    token_in    INTEGER NOT NULL DEFAULT 0,
    token_out   INTEGER NOT NULL DEFAULT 0,
    latency_ms  INTEGER,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_messages_session ON agent_messages (session_id, created_at);

COMMENT ON TABLE agent_messages IS '消息明细（trace 汇总存 workflow_runs，这里存对话本身）';

CREATE TABLE workflows (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    agent_id   BIGINT       NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    name       VARCHAR(128) NOT NULL,
    -- 画布整体存 JSONB（节点+边+坐标），不拆 nodes/edges 关系表：
    -- 图结构是"整体读写"，且节点类型会持续演进，拆表反而锁死扩展性
    -- {"nodes":[{"id":"n1","type":"llm","pos":{"x":120,"y":80},"params":{...}}],"edges":[{"from":"n1","to":"n2","condition":null}]}
    graph      JSONB        NOT NULL,
    version    INTEGER      NOT NULL DEFAULT 1,
    published  SMALLINT     NOT NULL DEFAULT 0,          -- 0=草稿 1=已发布
    created_by BIGINT       REFERENCES users(id),
    created_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT now()
);

COMMENT ON TABLE workflows IS '工作流定义（工作流页 FlowCanvas 画布的持久化形态）';

CREATE TABLE workflow_runs (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id  BIGINT      NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    session_id   UUID        REFERENCES agent_sessions(id),
    status       SMALLINT    NOT NULL DEFAULT 0,          -- 0=运行中 1=成功 2=失败 3=超时
    current_node VARCHAR(64),
    -- 节点级轨迹：[{"node":"retrieve","status":"ok","latency_ms":820,"tokens":1200}]（TracePanel 六步）
    node_traces  JSONB,
    total_tokens INTEGER     NOT NULL DEFAULT 0,
    error        TEXT,
    started_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at  TIMESTAMPTZ
);

CREATE INDEX idx_runs_workflow ON workflow_runs (workflow_id, started_at DESC);

-- ------------------------------------------------------------
-- 模块五：审计（Java 管理域）
-- ------------------------------------------------------------

CREATE TABLE audit_logs (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id       BIGINT,
    action        VARCHAR(64) NOT NULL,                   -- login / upload / delete / agent.run
    resource_type VARCHAR(32),
    resource_id   VARCHAR(64),
    detail        JSONB,
    ip            VARCHAR(45),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_user_time ON audit_logs (user_id, created_at DESC);

-- =============================================================
-- 附录：阶段② 拆分说明
--   Java 管理域 → schema "admin"：users, roles, user_roles,
--                 knowledge_bases, documents, document_chunks,
--                 data_sources, parse_tasks, skills, audit_logs
--   Python AI 域 → schema "ai"：agents, agent_skills, agent_kbs,
--                 agent_sessions, agent_messages, workflows,
--                 workflow_runs, retrieval_logs
--   阶段① 同库同 schema 直接跑；拆分时 ALTER TABLE ... SET SCHEMA 迁移，
--   服务间跨 schema 访问改为走 REST（契约在 ai-api-client 模块）。
-- =============================================================
