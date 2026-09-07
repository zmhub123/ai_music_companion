# 音伴 AI 音乐陪伴助手

AI 驱动的音乐陪伴 Web 应用：情绪倾诉、智能荐歌、内嵌播放、吉他/尤克里里谱面、歌单管理。

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | React 19 + TypeScript + Vite 8 + Ant Design 6 + Zustand |
| 后端 | Python 3.12 + FastAPI + PyCore + SQLAlchemy |
| 数据 | SQLite |
| AI | 百炼 DashScope（qwen-plus / qwen-turbo） |
| 音乐 | 网易云 API（pyncm） |

## 功能亮点

- 根据用户心情、场景或指定歌手进行 AI 荐歌
- 调用网易云搜索与播放地址，支持扫码登录及 VIP 试听提示
- 全局播放器支持上一首、下一首、顺序播放、单曲循环和随机播放
- 基于音频分析生成吉他/尤克里里谱面、歌词和和弦指法
- 支持游客偏好、聊天历史和歌单管理

## 快速开始（本地）

### 后端

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp backend/.env.example backend/.env
# 编辑 backend/.env，至少填写 DASHSCOPE_API_KEY 和 GUEST_SESSION_SECRET
./scripts/dev-backend.sh
```

如果 PyPI 无法安装 `pyncm`，可改用项目验证过的镜像源：

```bash
pip install "git+https://gitcode.com/gh_mirrors/py/pyncm.git"
```

### 前端

另开一个终端：

```bash
cd frontend
cp .env.example .env
npm install
cd ..
./scripts/dev-frontend.sh
```

访问地址：

- 应用：http://127.0.0.1:5199
- 后端健康检查：http://127.0.0.1:8099/health

前端通过 `/api` 代理访问后端 8099，默认 `VITE_USE_MOCK=false`。

## 使用示例

完整启动要求和功能使用流程见 [`docs/startup.md`](docs/startup.md)。

典型使用流程：

1. 完成弹唱水平和风格偏好。
2. 输入心情或“想听霉霉的歌”，展示 AI 真实荐歌。
3. 展示歌曲播放和三种播放模式。
4. 生成吉他或尤克里里谱面，展示歌词、和弦和指法图。
5. 收藏到歌单并从歌单播放。
6. 清除数据，展示聊天、推荐和偏好同步重置。

## 目录结构

```
├── backend/          # FastAPI 后端
├── frontend/         # React 前端
├── pycore/           # 内部框架（随项目分发）
├── docs/             # PRD、API 契约、原型
├── scripts/          # 本地开发启动脚本
└── pyproject.toml    # Python 依赖与质量工具配置
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

## 验证

```bash
source .venv/bin/activate
python -m pytest backend/tests -q
cd frontend
npm run lint
npm run type-check
npm run build
```

最新验收结果：后端 64 项测试通过，前端 lint、type-check、build 通过。

## 仓库

[GitHub - ai_music_companion](https://github.com/zmhub123/ai_music_companion)
