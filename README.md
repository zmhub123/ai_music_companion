# 音伴 AI 音乐陪伴助手

AI 驱动的音乐陪伴 Web 应用：情绪倾诉、智能荐歌、内嵌播放、吉他/尤克里里谱面、歌单管理。

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | React 18 + TypeScript + Vite + Ant Design + Zustand |
| 后端 | Python 3.12 + FastAPI + PyCore + SQLAlchemy |
| 数据 | SQLite |
| AI | 百炼 DashScope（qwen-plus / qwen-turbo） |
| 音乐 | 网易云 API（pyncm） |

## 快速开始（Docker）

1. 复制环境变量并填写密钥：

```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env，至少设置 DASHSCOPE_API_KEY 和 GUEST_SESSION_SECRET
```

2. 构建并启动：

```bash
docker compose up --build -d
```

> **国内网络**：`docker-compose.yml` 已默认使用 DaoCloud 镜像加速拉取基础镜像，并用清华 PyPI / npmmirror 安装依赖。若仍失败，见下方「Docker 构建失败排查」。

3. 访问：

- 前端：http://localhost:5199
- 后端健康检查：http://localhost:8099/health

## 本地开发

### 后端

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp backend/.env.example backend/.env
./scripts/dev-backend.sh
```

### 前端

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

前端默认 http://127.0.0.1:5199，API 代理到后端 8099。

## 目录结构

```
├── backend/          # FastAPI 后端
├── frontend/         # React 前端
├── pycore/           # 内部框架（随项目分发）
├── docs/             # PRD、API 契约、原型
├── deploy/           # Nginx 等部署配置
├── docker-compose.yml
├── Dockerfile.backend
└── Dockerfile.frontend
```

## 环境变量

详见 `backend/.env.example`。关键项：

| 变量 | 说明 |
|------|------|
| `DASHSCOPE_API_KEY` | 百炼 API Key |
| `DATABASE_URL` | SQLite 路径 |
| `GUEST_SESSION_SECRET` | 游客 Session 签名密钥 |
| `CHORD_PROVIDER` | 和弦数据源（`mock`） |
| `CORS_ORIGINS` | 允许的前端 Origin |

## Docker 构建失败排查

### 1. `Cannot connect to the Docker daemon`

Docker Desktop 未启动。打开 Docker Desktop，等菜单栏鲸鱼图标显示 **Running** 后，再执行 `docker info` 确认 Server 段有输出。

### 2. `failed to fetch oauth token` / `connection reset by peer`

无法访问 Docker Hub（`auth.docker.io`），常见于国内网络或 IPv6 不稳定。本项目 compose 已默认：

- 基础镜像：`docker.m.daocloud.io/library/...`
- pip：`pypi.tuna.tsinghua.edu.cn`
- npm：`registry.npmmirror.com`

也可在 Docker Desktop → **Settings → Docker Engine** 中合并 `deploy/docker-daemon-mirror.example.json` 里的 `registry-mirrors`，并设置 `"ipv6": false` 后 Apply & Restart。

海外环境可改回官方源：

```bash
REGISTRY= PIP_INDEX_URL=https://pypi.org/simple NPM_REGISTRY=https://registry.npmjs.org docker compose up --build -d
```

### 3. 手动预拉镜像（可选）

```bash
docker pull docker.m.daocloud.io/library/python:3.12-slim-bookworm
docker pull docker.m.daocloud.io/library/node:22-alpine
docker pull docker.m.daocloud.io/library/nginx:1.27-alpine
```

## 仓库

https://github.com/zmhub123/ai_music_companion
