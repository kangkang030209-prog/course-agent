# 课程智能助手（course-agent）

基于 **AI Agent + MCP + RAG** 的课程智能助手，Python 实现。
帮助同学解答《大模型应用开发实战》课程问题：既有知识型问答（RAG 检索讲义/资料），也有事实型查询（MCP 读取课程表/作业/公告）。

## 特性

- 🤖 **AI Agent**：基于 LangGraph 的 ReAct Agent，能自主决定调用哪个工具。
- 📚 **RAG**：本地 Chroma 向量库 + 中文 embedding 模型（`BAAI/bge-small-zh-v1.5`），语义检索课程资料，回答带来源引用。
- 🔌 **MCP**：自建 `course-mcp` 服务（stdio 传输），把课程表/作业/公告封装为标准 MCP 工具；Agent 作为 MCP Client 动态挂载。MCP 不可用时自动降级为纯 RAG。
- ☁️ **LLM**：DeepSeek 官方 API（`deepseek-chat`），密钥放 `.env`。
- 🖥️ **双交互**：命令行 CLI + FastAPI 后端（`/chat`、`/ingest`、`/health`）。

## 目录结构

```
course-agent/
├── app/
│   ├── config.py              # 配置（pydantic-settings 读 .env）
│   ├── rag/
│   │   ├── embeddings.py      # embedding 工厂
│   │   ├── ingest.py          # 文档加载-切分-入库
│   │   └── retriever.py       # 语义检索 + 引用
│   ├── mcp_server/
│   │   ├── course_mcp.py      # MCP 课程工具（课表/作业/公告/概览）
│   │   └── run.py             # stdio 入口
│   ├── agent/
│   │   ├── tools.py           # RAG 工具 + MCP 工具加载
│   │   └── service.py         # LangGraph ReAct Agent 编排
│   └── api/
│       └── main.py            # FastAPI 后端
├── data/                      # 示例课程资料（md + mcp json）
├── cli.py                     # 命令行交互
├── scripts/ingest.py          # 入库脚本
├── tests/                     # 单元测试
├── requirements.txt
├── .env.example
└── README.md
```

## 快速开始

### 1. 环境准备
```bash
# 需 Python 3.10+
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. 配置密钥
```bash
cp .env.example .env
# 编辑 .env，填入真实的 DEEPSEEK_API_KEY
```

### 3. 导入知识库（首次必须）
```bash
python scripts/ingest.py
# 首次会联网下载中文 embedding 模型（约 90MB），之后本地离线
# 加 --force 可重建集合
```

### 4. 命令行使用
```bash
python cli.py --verbose
# 依次尝试：
#   > 什么是 RAG？
#   > RAG 的实现要点是什么？
#   > 下周三有什么课？
#   > 作业截止时间？
#   > 退出
```

单次提问（非交互，方便脚本）：
```bash
python cli.py --once "什么是 Agent？"
```

### 5. 启动 FastAPI 后端
```bash
python -m app.api.main
# 或
uvicorn app.api.main:app --reload
```

打开 http://127.0.0.1:8000/docs 查看 Swagger 文档，可用接口：
- `POST /chat` — 对话，返回 `{answer, mcp_used}`
- `POST /ingest` —（重新）导入知识库
- `GET /health` — 健康检查，含 MCP 是否可用

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"作业截止时间是什么？"}'
```

## 运行测试

```bash
pytest -v
```

## 工作原理

```
用户提问
  │
  ▼
FastAPI /chat 或 CLI
  │
  ▼
LangGraph ReAct Agent（DeepSeek）
  ├── 需要知识 → 调用 RAG 工具 knowledge_base_search
  │                  → Chroma 向量相似度检索 → 带来源返回
  ├── 需要事实 → 调用 MCP 工具 get_course_schedule/get_homework/...
  │                  → course-mcp server（stdio）→ 结构化数据返回
  └── MCP 不可用 → 自动降级为仅 RAG
  │
  ▼
带引用的回答回到用户
```

## 配置项

见 [.env.example](.env.example)：

| 变量 | 说明 |
|---|---|
| `DEEPSEEK_API_KEY` | DeepSeek 密钥 |
| `DEEPSEEK_MODEL` | 模型名（默认 `deepseek-chat`） |
| `EMBEDDING_MODEL` | embedding 模型（默认 `BAAI/bge-small-zh-v1.5`） |
| `CHROMA_DB_DIR` | 向量库目录（默认 `./chroma_db`） |
| `RETRIEVAL_TOP_K` | 检索返回条数 |
| `MCP_SERVER_CMD` | MCP server 启动命令 |

## 扩展

- **加课程资料**：往 `data/` 放 `.md`/`.txt`，再跑 `python scripts/ingest.py`。
- **加 MCP 工具**：编辑 `app/mcp_server/course_mcp.py`（`course_mcp_data.json` 是结构化课程数据），Agent 启动时自动挂载。
- **换 LLM**：改 `config.py` 里的 DeepSeek 参数即可。