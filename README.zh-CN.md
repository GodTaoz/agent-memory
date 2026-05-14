# agent-memory

**Language / 语言：** [![English](https://img.shields.io/badge/English-README-blue)](README.md) [![简体中文](https://img.shields.io/badge/简体中文-README-green)](README.zh-CN.md)

> 一个轻量级、local-first 的 AI Agent 记忆服务，支持 **MCP + REST API**，内置 **管理面板**，并且 **零外部 API 成本**。

[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Branch](https://img.shields.io/badge/default%20branch-master-blueviolet.svg)](https://github.com/GodTaoz/agent-memory)

`agent-memory` 让多个 AI Agent 通过标准协议共享可持久化的记忆，而不是把状态反复塞回每一轮对话上下文中。
它的设计目标是：

- **轻量**：仅依赖 Redis，v1 不需要向量数据库
- **协议友好**：MCP 适合 Agent 原生集成，REST 适合通用接入
- **Local-first**：可部署在自己的机器、服务器或 NAS 上
- **默认具备基础安全性**：REST API Key 鉴权，管理面板独立登录
- **易运维**：内置 Web 管理面板，可查看记忆、管理 API Key、监控运行状态

---

## 功能特性

### 核心记忆服务
- 支持 MCP + REST 双协议
- 基于 Redis 持久化存储
- 提供 Memory CRUD 与 list/search API
- 多层索引：agent / tag / keyword / time
- 为未来的记忆合并与语义升级预留 evolution hooks
- 提供面向 ACL 的多 Agent 隔离基础能力

### 管理面板
- 单端口部署，默认运行在 **`5678`**
- 前端基于 Vue 3 + Element Plus
- 支持浅色 / 深色 / 跟随系统主题切换
- Dashboard 实时展示 Redis / memory / API key / request 统计
- API Key 管理：列表 / 创建 / 删除 / 使用追踪
- 记忆浏览 / 搜索 / 编辑 / 删除 / 导出
- Agent 活动总览（当前为占位 UI，后端可扩展）
- 使用 SQLite 保存管理后台与 REST 访问统计
- 支持管理员密码登录、面板内修改密码、失败登录锁定、默认密码告警

### 安全性
- REST API Key 鉴权
- 受管 API Key 权限模型：
  - `read` → 只读 REST 访问
  - `read_write` → 完整 memory CRUD 权限
  - `admin` → 预留 / 兼容 bootstrap 的完全访问权限
- 支持的鉴权方式：
  - `Authorization: Bearer <api_key>`
  - `X-API-Key: <api_key>`
  - `?api_key=<api_key>`
- 管理面板使用独立登录流程
- 生产环境建议继续加固：HTTPS、防火墙 / IP 白名单、密钥轮换

---

## 架构

```text
Browser
  └─ http://host:5678/
       ├─ /admin/api/*        管理后台 API (FastAPI)
       ├─ /assets/*           构建后的 Vue 前端静态资源
       ├─ /api/v1/*           Memory REST API
       └─ /                   管理面板入口

AI Agents
  ├─ MCP client  ─────────────┐
  └─ REST client ─────────────┤
                              ▼
                    agent-memory service
                      ├─ protocol layer
                      ├─ auth layer
                      ├─ memory engine
                      ├─ index manager
                      ├─ admin module
                      └─ Redis / SQLite
```

---

## 快速开始

### 方案 1：Docker Compose

```bash
git clone https://github.com/GodTaoz/agent-memory.git
cd agent-memory

cp config/config.example.yaml config/config.yaml
cp config/permissions.example.yaml config/permissions.yaml

# 可选：导出运行时密钥
export REDIS_PASSWORD='your-redis-password'
export API_KEYS='agent-key-1,agent-key-2'
export ADMIN_PASSWORD_HASH=''
export ADMIN_PASSWORD_SALT=''

docker-compose up -d
```

然后打开：

- 管理面板：`http://localhost:5678/`
- 健康检查：`http://localhost:5678/api/v1/health`

### 方案 2：本地开发

```bash
git clone https://github.com/GodTaoz/agent-memory.git
cd agent-memory

python3 -m venv venv
source venv/bin/activate
pip install -e ".[all]"

# 启动后端
uvicorn memory_mcp.main:create_app --factory --host 0.0.0.0 --port 5678
```

如果安装后想通过 console script 运行：

```bash
memory-mcp
```

---

## 管理面板

管理面板与 API 通过同一端口提供服务。

- 地址：`http://<host>:5678/`
- 默认密码：`admin123`
- **重要**：首次登录后请立即修改密码

### 当前面板范围

- Dashboard / 服务统计（实时 Redis + request metrics）
- API Key 管理（创建 / 列表 / 吊销）
- 记忆查看与编辑
- Agent 总览壳层（后端可继续扩展）
- 操作日志 API 与 REST 访问统计
- 导出入口
- 主题切换：浅色 / 深色 / 跟随系统

管理日志默认存储在 SQLite 中：

- 默认文件：`data/admin_logs.db`
- 可通过 `ADMIN_LOG_DB_PATH` 配置

管理员认证 / API Key 持久化默认路径：

- 管理员密码状态：`data/admin_auth.json`
- 受管 API Keys：`data/api_keys.json`

---

## REST API 用法

### 保存记忆

```bash
curl -X POST http://localhost:5678/api/v1/memories \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "content": "User prefers concise and elegant code.",
    "tags": ["preference", "coding"],
    "agent": "hermes"
  }'
```

### 搜索记忆

```bash
curl 'http://localhost:5678/api/v1/memories?q=concise&agent=hermes&api_key=your-api-key'
```

### 健康检查

```bash
curl http://localhost:5678/api/v1/health
```

### 主要接口

- `POST /api/v1/memories`
- `GET /api/v1/memories/{id}`
- `PUT /api/v1/memories/{id}`
- `DELETE /api/v1/memories/{id}`
- `GET /api/v1/memories`
- `GET /api/v1/health`
- `GET /api/v1/stats`

---

## MCP 集成

stdio client 使用示例：

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["-m", "memory_mcp.protocol.mcp"],
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        await session.call_tool("memory.save", {
            "content": "User prefers concise and elegant code.",
            "tags": ["preference", "coding"],
        })
```

---

## 配置

### 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `SERVER_HOST` | `0.0.0.0` | 监听地址 |
| `SERVER_PORT` | `5678` | 服务端口 |
| `REDIS_HOST` | `localhost` | Redis 主机 |
| `REDIS_PORT` | `6379` | Redis 端口 |
| `REDIS_PASSWORD` | 空 | Redis 密码 |
| `REDIS_DB` | `0` | Redis 数据库索引 |
| `API_KEYS` | 空 | 启动时注入的 REST API Keys（可选兼容路径） |
| `ADMIN_PASSWORD_HASH` | 空 | 可选的管理员密码哈希 |
| `ADMIN_PASSWORD_SALT` | 空 | 管理员密码哈希使用的盐 |
| `ADMIN_AUTH_CONFIG_PATH` | `data/admin_auth.json` | 管理员密码状态持久化文件 |
| `ADMIN_API_KEYS_PATH` | `data/api_keys.json` | 受管 API Key 持久化文件 |
| `ADMIN_LOG_DB_PATH` | `data/admin_logs.db` | 保存管理日志和 REST 访问统计的 SQLite 路径 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

### 配置文件

- `config/config.yaml` - server / Redis / search / logging 配置
- `config/permissions.yaml` - agent 权限 / ACL 相关配置

可以从下面两个示例开始：

- `config/config.example.yaml`
- `config/permissions.example.yaml`

---

## 前端开发

管理后台前端位于 `admin-frontend/`。

```bash
cd admin-frontend
npm install
npm run build
```

构建产物会发布到：

- `src/memory_mcp/admin/static/`

仓库中保留了已构建静态资源，因此在部署环境中后端可以直接提供管理面板页面。

---

## 开发

### 运行测试

```bash
pytest
```

### 建议检查项

```bash
black src tests
flake8 src tests
mypy src
```

### 分支策略

本仓库默认工作分支是 **`master`**。

---

## 项目结构

```text
agent-memory/
├── admin-frontend/              # Vue 3 管理后台源码
├── config/                      # 示例与运行时配置
├── src/memory_mcp/
│   ├── admin/                   # 管理后台后端 + 构建后的静态资源
│   ├── auth/                    # 认证与 ACL 模块
│   ├── engine/                  # Memory 生命周期逻辑
│   ├── protocol/                # MCP / REST 接口
│   ├── storage/                 # Redis 后端与索引
│   ├── config.py                # 配置加载器
│   ├── models.py                # 数据模型
│   └── main.py                  # 运行入口
├── tests/                       # 测试套件
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

---

## 安全说明

当前基础安全能力包括 REST API Key 鉴权与管理员登录，另外管理流程还包括：

- 默认密码检测（登录时返回 `requires_password_change`）
- 管理员密码状态持久化
- 受管 API Key 持久化与吊销
- 强制 API Key 权限控制（`read` vs `read_write`）
- SQLite 中的登录 / 管理操作 / REST 访问审计日志
- 多次失败后登录锁定
- 管理员密码状态文件权限收紧为仅 owner 可读写（`0600`）
- API Key 存储文件权限收紧为仅 owner 可读写（`0600`）

在生产环境中仍建议继续增加：

- HTTPS / TLS
- 如果公网暴露，建议加反向代理（Nginx / Caddy）
- 防火墙或来源 IP 限制
- 强随机 API Keys
- 密码轮换与审计检查

---

## 参与贡献

详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## License

本项目采用 [MIT License](LICENSE) 开源。
