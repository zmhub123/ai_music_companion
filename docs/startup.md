# 音伴启动与使用说明

## 环境要求

- Python 3.12
- Node.js 22+
- 项目根目录已创建 `.venv`
- 前端依赖已安装
- `backend/.env` 已配置 `DASHSCOPE_API_KEY`、`GUEST_SESSION_SECRET` 等必要变量
- `frontend/.env` 保持 `VITE_USE_MOCK=false`

## 本地启动

在两个终端中分别执行：

```bash
cd /path/to/ai-music-companion
./scripts/dev-backend.sh
```

```bash
cd /path/to/ai-music-companion
./scripts/dev-frontend.sh
```

访问地址：

- 应用：http://127.0.0.1:5199
- 后端健康检查：http://127.0.0.1:8099/health

## 功能使用流程

1. 首次进入完成弹唱水平和风格偏好。
2. 在首页输入心情或指定歌手，例如“想听霉霉的歌”。
3. 进入播放页，等待 AI 返回真实荐歌。
4. 展示歌曲播放、上一首/下一首及顺序/单曲循环/随机模式。
5. 生成吉他或尤克里里谱面，展示歌词、和弦和指法图。
6. 将歌曲收藏到歌单，并从歌单继续播放。
7. 展示网易云扫码登录和 VIP 试听提示。
8. 在“我的”页面清除数据，验证聊天、推荐与偏好重置。

## 运行检查

```bash
curl http://127.0.0.1:8099/health
cd frontend && npm run lint && npm run type-check && npm run build
```

后端完整测试：

```bash
cd /path/to/ai-music-companion
source .venv/bin/activate
python -m pytest backend/tests -q
```

## 已知非阻塞项

- 谱库列表页仍使用 Mock 列表。
- “查看更多推荐”按钮尚未接入分页接口。
- 部分网易云 VIP 或版权歌曲即使登录也可能无法获取完整音源，此时应用提供提示或外链兜底。
