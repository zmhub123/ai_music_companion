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

## 仓库

https://github.com/zmhub123/ai_music_companion
