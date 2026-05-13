# Memory MCP Server

> 🧠 Universal Memory Service for AI Agents

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

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
           │                 │                 │
           ▼                 ▼                 ▼
      ┌─────────┐      ┌─────────┐      ┌─────────┐
      │ Hermes  │      │ Codex   │      │ Claude  │
      └─────────┘      └─────────┘      └─────────┘
```

---

## 快速开始

### 方式1：Docker Compose（推荐）

```bash
# 克隆项目
git clone https://github.com/GodTaoz/memory-mcp.git
cd memory-mcp

# 启动服务
docker-compose up -d

# 验证服务
curl http://localhost:8080/api/v1/health
```

### 方式2：本地安装

```bash
# 克隆项目
git clone https://github.com/GodTaoz/memory-mcp.git
cd memory-mcp

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -e .

# 启动服务
memory-mcp serve
```

---

## 使用示例

### REST API

```bash
# 保存记忆
curl -X POST http://localhost:8080/api/v1/memories \
  -H "Content-Type: application/json" \
  -H "X-Agent: hermes" \
  -d '{
    "content": "用户喜欢简洁的代码风格",
    "tags": ["preference", "code"]
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

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # 初始化
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

## 配置

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `REDIS_HOST` | `localhost` | Redis主机 |
| `REDIS_PORT` | `6379` | Redis端口 |
| `REDIS_PASSWORD` | `` | Redis密码 |
| `SERVER_HOST` | `0.0.0.0` | 服务监听地址 |
| `SERVER_PORT` | `8080` | 服务端口 |

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

## API文档

启动服务后，访问以下地址查看API文档：

- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

---

## 开发

### 运行测试

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
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

## 目录结构

```
memory-mcp/
├── README.md                    # 本文档
├── LICENSE                      # MIT License
├── pyproject.toml               # 项目配置
├── Dockerfile                   # Docker构建
├── docker-compose.yml           # Docker Compose
├── config/                      # 配置文件
│   ├── config.yaml
│   └── permissions.yaml
├── src/                         # 源代码
│   └── memory_mcp/
│       ├── main.py
│       ├── config.py
│       ├── models.py
│       ├── engine/
│       ├── storage/
│       ├── protocol/
│       └── auth/
├── tests/                       # 测试
└── docs/                        # 文档
    ├── architecture.md
    ├── api-reference.md
    └── deployment.md
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
