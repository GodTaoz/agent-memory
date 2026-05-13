# Memory MCP Server

> 🧠 Universal Memory Service for AI Agents

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-111%20passed-brightgreen.svg)](https://github.com/GodTaoz/agent-memory/actions)

---

## 简介

Memory MCP Server 是一个通用的AI Agent记忆服务，基于MCP协议和REST API，支持多Agent接入和权限隔离。

**核心特性：**
- 🔌 **双协议支持** - MCP + REST API
- 👥 **多Agent支持** - 任意数量的Agent接入
- 🔒 **权限隔离** - 基于ACL的读写权限控制
- 🔍 **智能搜索** - 多级索引 + 同义词扩展
- 🔄 **记忆演化** - 自动合并相似记忆
- 🐳 **一键部署** - Docker + Compose
- 💰 **零API成本** - 纯本地运行，无需LLM API

---

## 与Mem0对比

| 维度 | Mem0 | Memory MCP Server |
|------|------|-------------------|
| **部署复杂度** | 需要向量DB+LLM | **只需Redis** |
| **运行成本** | LLM API费用 | **零API成本** |
| **协议支持** | Python/Node SDK | **MCP + REST** |
| **语义理解** | ✅ 强（向量搜索） | ⚠️ 关键词+同义词 |
| **适用场景** | 高级语义需求 | **快速接入、本地优先** |

---

## 快速开始

### 方式1：Docker Compose（推荐）

```bash
# 克隆项目
git clone https://github.com/GodTaoz/agent-memory.git
cd agent-memory

# 启动服务
docker-compose up -d

# 验证服务
curl http://localhost:8080/api/v1/health
```

### 方式2：本地安装

```bash
# 克隆项目
git clone https://github.com/GodTaoz/agent-memory.git
cd agent-memory

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -e ".[all]"

# 启动服务
uvicorn src.memory_mcp.protocol.rest:create_app --factory --host 0.0.0.0 --port 8080
```

---

## 使用示例

### REST API

```bash
# 保存记忆
curl -X POST http://localhost:8080/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "content": "用户喜欢简洁的代码风格",
    "tags": ["preference", "code"],
    "agent": "hermes"
  }'

# 搜索记忆
curl "http://localhost:8080/api/v1/memories?q=代码&agent=hermes"

# 获取记忆
curl http://localhost:8080/api/v1/memories/{memory_id}
```

### MCP Client

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["-m", "memory_mcp.protocol.mcp"]
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        
        # 保存记忆
        result = await session.call_tool("memory.save", {
            "content": "用户喜欢简洁的代码风格",
            "tags": ["preference", "code"]
        })
        
        # 搜索记忆
        results = await session.call_tool("memory.search", {
            "query": "代码"
        })
```

---

## API文档

### REST API端点

| 方法 | 路径 | 描述 |
|------|------|------|
| `POST` | `/api/v1/memories` | 创建记忆 |
| `GET` | `/api/v1/memories/{id}` | 获取记忆 |
| `PUT` | `/api/v1/memories/{id}` | 更新记忆 |
| `DELETE` | `/api/v1/memories/{id}` | 删除记忆 |
| `GET` | `/api/v1/memories` | 搜索/列表 |
| `GET` | `/api/v1/health` | 健康检查 |
| `GET` | `/api/v1/stats` | 统计信息 |

### MCP工具

| 工具 | 描述 |
|------|------|
| `memory.save` | 保存记忆 |
| `memory.get` | 获取记忆 |
| `memory.search` | 搜索记忆 |
| `memory.update` | 更新记忆 |
| `memory.delete` | 删除记忆 |
| `memory.list` | 列出记忆 |
| `memory.health` | 健康检查 |
| `memory.stats` | 统计信息 |

---

## 配置

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `REDIS_HOST` | `localhost` | Redis主机 |
| `REDIS_PORT` | `6379` | Redis端口 |
| `REDIS_PASSWORD` | `` | Redis密码 |
| `SERVER_HOST` | `0.0.0.0` | 服务监听地址 |
| `SERVER_PORT` | `8080` | 服务端口 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

### 配置文件

**config/config.yaml:**
```yaml
server:
  host: "0.0.0.0"
  port: 8080

redis:
  host: "localhost"
  port: 6379
  key_prefix: "memory"

memory:
  similarity_threshold: 0.3
  max_tags: 20

search:
  enable_synonyms: true
  enable_fuzzy: true
```

**config/permissions.yaml:**
```yaml
agents:
  hermes:
    permissions:
      namespace: "hermes:*"
      operations: ["read", "write", "delete"]
      admin: true

  codex:
    permissions:
      namespace: "codex:*"
      operations: ["read", "write"]
      shared_read: true
```

---

## Agent接入指南

### Hermes Agent

编辑 `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  memory:
    url: "http://your-server:8080/mcp"
```

### Codex CLI

编辑 `~/.codex/config.toml`:

```toml
[mcp_servers.memory]
url = "http://your-server:8080/mcp"
```

### Claude Code

编辑 `~/.claude/config.json`:

```json
{
  "mcpServers": {
    "memory": {
      "url": "http://your-server:8080/mcp"
    }
  }
}
```

---

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                 Memory MCP Server                           │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  MCP Server  │  │  REST API    │  │  权限管理    │      │
│  │  (协议层)    │  │  (协议层)    │  │  (ACL)       │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         └─────────────────┼─────────────────┘              │
│                           │                                │
│  ┌────────────────────────▼────────────────────────┐       │
│  │              Memory Engine                       │       │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐ │       │
│  │  │ 演化引擎   │  │ 多级索引   │  │ 搜索引擎   │ │       │
│  │  └────────────┘  └────────────┘  └────────────┘ │       │
│  └────────────────────────┬────────────────────────┘       │
│                           │                                │
│                    ┌──────▼───────┐                        │
│                    │    Redis     │                        │
│                    └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 开发

### 运行测试

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=src/memory_mcp --cov-report=html
```

### 代码检查

```bash
# 格式化代码
black src/ tests/

# 检查代码风格
flake8 src/ tests/

# 类型检查
mypy src/
```

---

## 测试覆盖

**总计：111个测试，全部通过！**

| 模块 | 测试数 | 状态 |
|------|--------|------|
| models | 9 | ✅ |
| config | 8 | ✅ |
| redis_backend | 11 | ✅ |
| index | 12 | ✅ |
| memory_engine | 12 | ✅ |
| evolution | 11 | ✅ |
| search | 14 | ✅ |
| mcp | 13 | ✅ |
| rest | 10 | ✅ |
| acl | 11 | ✅ |

---

## 项目结构

```
agent-memory/
├── src/memory_mcp/
│   ├── __init__.py
│   ├── config.py           # 配置管理
│   ├── models.py           # 数据模型
│   ├── engine/
│   │   ├── memory.py       # 记忆引擎
│   │   ├── evolution.py    # 演化引擎
│   │   └── search.py       # 搜索引擎
│   ├── storage/
│   │   ├── redis_backend.py # Redis存储
│   │   └── index.py        # 索引管理
│   ├── protocol/
│   │   ├── mcp.py          # MCP Server
│   │   └── rest.py         # REST API
│   └── auth/
│       └── acl.py          # 权限管理
├── tests/                  # 测试文件
├── config/                 # 配置文件
├── Dockerfile              # Docker构建
├── docker-compose.yml      # Docker Compose
└── pyproject.toml          # 项目配置
```

---

## 贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

---

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 致谢

- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP协议规范
- [FastAPI](https://fastapi.tiangolo.com/) - Web框架
- [Redis](https://redis.io/) - 存储引擎
