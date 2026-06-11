# 开发计划

> 设计阶段与开发阶段的衔接文件。所有开发进度以本文件为准。
> 项目：ai-music-companion（音伴） | 生成：阶段 C | 更新：2026-06-07

---

## 一、功能清单总览

| 序号 | 功能编号 | 功能名称 | 一句话描述 | 对应页面 | 优先级 | 状态 |
|------|---------|---------|-----------|---------|--------|------|
| F01 | F-01-01 | 弹唱水平选择 | 三档水平单选 | P01 | MVP | 待开发 |
| F02 | F-01-02 | 风格偏好选择 | 多选音乐风格标签 | P01 | MVP | 待开发 |
| F03 | F-01-03 | 保存偏好 | 写入游客 Session | P01 | MVP | 待开发 |
| F04 | F-02-01 | AI 情绪对话 | 多轮共情聊天 | P02/P02b/G01 | MVP | 待开发 |
| F05 | F-02-02 | 智能荐歌 | LLM 意图+网易云搜索+重排 | P02/P02b/G01 | MVP | 待开发 |
| F06 | F-02-03 | 查看谱面 | 从推荐卡片进入谱面 | P02b/P03 | MVP | 待开发 |
| F07 | F-02-04 | 收藏到歌单 | 选择歌单添加歌曲 | 全局 | MVP | 待开发 |
| F08 | F-02-05 | 历史会话 | 当前 Session 消息持久化 | G01 | MVP | 待开发 |
| F09 | F-02-06 | 新建对话 | 清空对话上下文 | G01 | MVP | 待开发 |
| F10 | F-02-07 | 卡片内嵌播放 | 推荐卡片触发播放 | P02b | MVP | 待开发 |
| F11 | F-03-01 | 歌曲信息展示 | 谱面页基础元数据 | P03 | MVP | 待开发 |
| F12 | F-03-02 | 吉他谱展示 | 和弦+歌词对齐 | P03 | MVP | 待开发 |
| F13 | F-03-03 | 尤克里里谱展示 | 切换乐器 Tab | P03 | MVP | 待开发 |
| F14 | F-03-04 | 水平适配 | 按 skill_level 简化和弦 | P03 | MVP | 待开发 |
| F15 | F-03-06 | 谱面内嵌播放 | 边听边看谱 | P03 | MVP | 待开发 |
| F16 | F-03-07 | 播放失败兜底 | 外链网易云 | P03 | MVP | 待开发 |
| F17 | F-04-01 | 歌单列表 | 展示游客歌单 | P04 | MVP | 待开发 |
| F18 | F-04-02 | 创建歌单 | 新建空歌单 | P04 | MVP | 待开发 |
| F19 | F-04-03 | 删除歌单 | 二次确认删除 | P04 | MVP | 待开发 |
| F20 | F-05-01 | 歌单歌曲列表 | 展示歌单内歌曲 | P05 | MVP | 待开发 |
| F21 | F-05-02 | 移除歌曲 | 从歌单删除 | P05 | MVP | 待开发 |
| F22 | F-05-05 | 歌单内播放 | 点击播放图标 | P05 | MVP | 待开发 |
| F23 | F-06-01 | 偏好查看/修改 | 我的页修改偏好 | P06 | MVP | 待开发 |
| F24 | F-06-03 | 清除数据 | 删除游客全部数据 | P06 | MVP | 待开发 |
| F25 | G01-01 | 全局播放器 | 播放/暂停单例 | 全局 | MVP | 待开发 |
| F26 | G01-03 | 跨页保持播放 | Tab 切换不中断 | 全局 | MVP | 待开发 |
| F27 | G01-04 | 聊天浮窗 | 380×440 浮窗+最小化/FAB | G01 | MVP | 待开发 |

---

## 二、数据契约摘要

完整数据契约见 `docs/PRD.md` 第 6 章「数据契约确认清单」。

核心实体：`guest_session`、`chat_message`、`playlist`、`playlist_song`、`chord_cache`、`score_cache`。

统一响应格式与全部接口定义见 `docs/api-contracts.md`（唯一权威源）。

---

## 二点五、外部服务与测试权限清单

> 本清单为 PRD A5-3 经用户确认后的落定版。真实 Key 仅存 `backend/.env`，不写入本文档。

| 服务 | 用途 | 配置项字段 | MVP 必需 | Tester 完整联调权限 | 缺失时策略 | 状态 |
|------|------|------------|----------|--------------------|------------|------|
| 百炼 DashScope（qwen-plus） | 情绪对话、荐歌重排 | `DASHSCOPE_API_KEY`, `LLM_MODEL_CHAT`, `LLM_BASE_URL` | 是 | 用户提供的测试 Key + 可调用额度 | Mock 固定回复+种子推荐 | **已确认** |
| 百炼 DashScope（qwen-turbo） | 谱面简化、练习提示 | `DASHSCOPE_API_KEY`, `LLM_MODEL_SCORE` | 是 | 同上（共用 Key） | Mock 跳过简化 | **已确认** |
| 网易云 API（pyncm） | 搜索、元数据、播放 URL | 无 Key | 是 | 本地网络可访问 | Mock 种子歌曲列表 | **已确认** |
| SQLite | 业务数据持久化 | `DATABASE_URL` | 是 | 本地文件可读写 | 无法启动 | **已确认** |
| 和弦 Mock 数据源 | 弹唱谱 | `CHORD_PROVIDER=mock` | 是 | 无需 Key | Mock 种子和弦 | **已确认** |
| 游客 Session | Cookie 鉴权 | `GUEST_SESSION_SECRET`, `GUEST_SESSION_MAX_AGE_DAYS` | 是 | 本地 Cookie 可写 | 无法保持状态 | **已确认** |

---

## 三、前端开发清单

### 前端技术选型

| 层级 | 选择 | 说明 |
|------|------|------|
| 框架 | React 18 | 业务 Web App |
| 语言 | TypeScript | 全量类型化 |
| 构建工具 | Vite | 开发代理 `/api` → 8000 |
| 路由 | react-router-dom v6 | 顶栏导航 + 页面路由 |
| 状态管理 | Zustand | 播放器单例、聊天浮窗、游客偏好 |
| 请求库 | Axios | `withCredentials: true` |
| 组件库 | Ant Design 5 | 主色 `#6B4EFF` |
| 工程化 | ESLint + Prettier + tsc + build | 自动验收 |

### 页面开发清单

| 序号 | 页面 | 路由 | 涉及功能 | Mock 数据来源 | 状态 |
|------|------|------|---------|--------------|------|
| P01 | 偏好引导弹层 | `/`（首次） | F01~F03 | POST /api/v1/guest/onboarding | 待开发 |
| P02 | 首页 | `/` | F04（输入） | POST /api/v1/chat/messages | 待开发 |
| P02b | 播放工作台 | `/player` | F05~F10, F25 | chat + songs + play-url | 待开发 |
| P03 | 谱面抽屉 | 组件 | F11~F16 | GET /api/v1/songs/{id}/score | 待开发 |
| P04 | 歌单列表 | `/playlists` | F17~F19 | GET/POST/DELETE playlists | 待开发 |
| P05 | 歌单详情 | `/playlists/:id` | F20~F22 | GET playlist detail | 待开发 |
| P06 | 我的 | `/me` | F23~F24 | GET/PUT/DELETE guest | 待开发 |
| G01 | 聊天浮窗 | 全局组件 | F04~F09, F27 | chat messages | 待开发 |

### 关键前端组件

| 组件 | 页面 | 说明 |
|------|------|------|
| `AppLayout` | 全局 | 顶栏导航 + 游客徽章 + AI 助手按钮 |
| `OnboardingModal` | P01 | 水平+风格向导 |
| `HomeHero` | P02 | 心情输入 + 快捷标签 |
| `PlayerWorkbench` | P02b | 推荐列表 + 黑胶播放器 |
| `ChatFloat` | G01 | 380×440 浮窗、最小化、FAB |
| `ScoreDrawer` | P03 | 吉他/尤克里里 Tab |
| `MiniPlayer` | 全局 | 底部播放条（跨页保持） |
| `PlaylistPicker` | 全局 | 收藏到歌单弹窗 |

### 前端自动验收标准

- [ ] 所有页面 UI 与 `docs/prototypes/index.html` 一致
- [ ] `VITE_USE_MOCK=true` 时所有页面可正常交互
- [ ] Mock 数据格式与 `api-contracts.md` 完全一致
- [ ] 首页默认隐藏聊天浮窗；播放页自动显示浮窗
- [ ] 播放器全局单例，跨 Tab 不中断
- [ ] Agent/Tester 自动验收通过

---

## 四、后端开发清单

| 序号 | 任务 | 依赖 | 对应接口 | 状态 |
|------|------|------|---------|------|
| B00 | 基础设施（PyCore 脚手架、配置、DB、CORS） | 无 | GET /health | 待开发 |
| B01 | 游客 Session（Cookie 中间件） | B00 | guest/session, guest/me | 待开发 |
| B02 | 偏好引导与偏好管理 | B01 | guest/onboarding, guest/preferences | 待开发 |
| B03 | 对话消息 + LLM 编排 | B01, B08, B09 | chat/messages, chat/reset | 待开发 |
| B04 | 网易云搜索与元数据 | B00 | songs/search, songs/{id} | 待开发 |
| B05 | 播放 URL + 流代理 | B04 | songs/{id}/play-url, stream | 待开发 |
| B06 | 谱面服务（Mock 和弦 + 水平简化） | B01, B08, B10 | songs/{id}/score | 待开发 |
| B07 | 歌单 CRUD | B01 | playlists/* | 待开发 |
| B08 | 百炼 DashScope 集成 | B00 | 内部服务 | 待开发 |
| B09 | 荐歌编排（意图→搜索→重排） | B03, B04, B08 | 内部服务 | 待开发 |
| B10 | 和弦 Mock Provider | B00 | 内部服务 | 待开发 |
| B11 | 清除游客数据 | B01 | DELETE guest/data | 待开发 |

### Python 环境

- **Python 版本**：3.11～3.13（pyncm 不支持 3.14）
- **虚拟环境**：`.venv`

### 后端任务验收规则

- 基础设施基于 `pycore/` 脚手架，禁止重写 config/server/logger
- B00 验收：ruff/mypy 通过、单元测试通过、`GET /health` 返回 200
- 业务任务验收：对应前端 `VITE_USE_MOCK=false` 真实联调通过
- 外部服务任务引用「外部服务与测试权限清单」；Key 缺失时仅可 Mock 降级验收

---

## 五、功能详情（开发时逐个展开）

### F05 / B09：智能荐歌

- **Pipeline**：用户消息 → qwen-plus 意图分类 → 抽取情绪/风格/关键词 → pyncm 搜索 10～20 首 → qwen-plus 重排 Top 5 → 结构化 recommendations
- **约束**：禁止 LLM 凭空造歌，必须基于搜索召回
- **极端情绪**：优先关怀话术，不推欢快歌曲

### F12 / B06：谱面生成

- 查 `chord_cache` → 未命中则 `ChordProvider(mock)` 返回种子和弦
- qwen-turbo 按 `skill_level` 简化和弦说明
- 吉他/尤克里里规则转换，写入 `score_cache`

### F25 / B05：内嵌播放

- `GET play-url` → pyncm `GetTrackAudio`
- CORS 失败时前端改请求 `/stream` 代理
- 失败返回 `50004` + `fallback_url`

### F07 / B07：歌单收藏

- 冗余存储 `netease_song_id` + name/artist/cover
- 唯一约束 `(playlist_id, netease_song_id)`

---

## 六、开发顺序建议

### 阶段 1：前端 MVP（Mock，用户先验收 UI/UX）

1. 初始化 `frontend/`（Vite + React + TS + Ant Design）
2. 实现全局布局 + P01 引导弹层
3. 实现 P02 首页 + P02b 播放工作台 + G01 聊天浮窗
4. 实现 P03 谱面抽屉 + P04/P05 歌单 + P06 我的 + 迷你播放器
5. Mock 数据对齐 `api-contracts.md`
6. **用户门禁**：确认 UI/UX 与原型一致

### 阶段 2：后端基础设施（自动连续执行）

1. 初始化 `backend/`（PyCore APIServer + SQLAlchemy + SQLite）
2. 建表（guest、chat、playlist、chord_cache、score_cache）
3. `GET /health` + 游客 Cookie 中间件
4. **Agent 自动验收**：ruff/mypy/测试/health

### 阶段 3：逐功能闭环开发

| 顺序 | 功能闭环 | 前后端切换 |
|------|---------|-----------|
| 1 | 游客 Session + 偏好引导 | guest API + 前端切真实 |
| 2 | 歌单 CRUD | playlists API |
| 3 | 聊天 + 荐歌 | chat API + LLM + pyncm |
| 4 | 播放 URL + 播放器 | play-url/stream + playerStore |
| 5 | 谱面展示 | score API + ChordProvider |
| 6 | 清除数据 | DELETE guest/data |

每个闭环完成后触发用户门禁验收。

### 阶段 4：E2E 回归测试

完整流程：首次访问引导 → 首页输入心情 → 播放工作台荐歌 → 内嵌播放 → 看吉他谱 → 收藏歌单 → 歌单页播放 → 我的页修改偏好

---

## 七、设计产物索引

| 文件 | 路径 | 状态 |
|------|------|------|
| PRD 定稿 | `docs/PRD.md` | 已完成 |
| 接口契约 | `docs/api-contracts.md` | 已完成 |
| 开发计划 | `docs/Plan.md` | 已完成 |
| HTML 原型 | `docs/prototypes/index.html` | 已完成 |
| 任务清单 | `.sdd/tasks.json` | 已完成 |
| 视觉调研 | `.sdd/tmp/visual-research.md` | 已完成（可归档） |
