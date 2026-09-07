# 测试报告：T-011 E2E 回归：倾诉→荐歌→播放→看谱→收藏

**测试时间**：2026-09-08 03:30 (UTC+8)
**Tester Agent ID**：tester-subagent
**验收基准**：当前磁盘代码（不信任既有 PASS 声明）

## 结果：PASS

> 自动化验收通过；任务含 `user_gate: true`，浏览器高保真交互仍建议 Orchestrator 组织用户门禁（端口 5175/8003）后关闭 MVP。

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | 完整主流程无阻塞性 Bug | PASS | 后端 64/64 pytest；真实 API 主链路（游客→引导→聊天荐歌→搜索→播放 URL→谱面→歌单收藏→清数据）全部 200/预期错误码；前端 lint/type-check/build 通过；本轮 Bugfix 功能点经代码审查 + API/静态证据覆盖 |
| 2 | 播放失败时有外链兜底提示 | PASS | `GET /api/v1/songs/{id}/play-url` 对不可播曲目返回 `code=50004` 且含 `fallback_url`（如 `https://music.163.com/song?id=186016`）；成功路径对 Taylor Swift 曲目返回可播 URL；前端 `RecommendList.tsx` / `playerStore.ts` 在外链场景弹窗或 `window.open` |
| 3 | 清除数据后回到偏好引导 | PASS | `DELETE /api/v1/guest/data` 返回 `cleared=true`、`onboarding_completed=false`；聊天 `total=0`、歌单清空；前端 `MePage.tsx` 调用 `resetClientSessionAfterGuestClear()` 并 `navigate('/')`；`guestStore.fetchProfile` 在 `onboarding_completed=false` 时设 `showOnboarding=true` |

## technicalChecks

| 检查项 | 结果 | 证据 |
|--------|------|------|
| 前端 build | PASS | `npm run build` 成功（dist 无 `[Mock]` 文案） |
| 后端测试 | PASS | `PYTHONPATH=.:.. $PY -m pytest backend/tests -q` → **64 passed** |
| 主流程自动化 | PASS | 见下文「真实 API 主链路脚本」16/16 PASS |

## 环境与配置

| 检查项 | 结果 | 说明 |
|--------|------|------|
| Python 运行时 | PASS | `.venv/bin/python` → Python 3.12.13 |
| backend/.env | PASS | 必需键均已配置（DASHSCOPE、DATABASE、CORS 等）；未输出秘密值 |
| frontend/.env | PASS | `VITE_USE_MOCK=false`；`VITE_API_BASE_URL=/api`；各 `VITE_MOCK_*=false` |
| Vite 代理 | PASS | `vite.config.ts` 含 `/api`、`/ws`（ws:true）；默认目标 `127.0.0.1:8099` |
| CORS | PASS | `config.py` DEFAULT_CORS_ORIGINS 含 5199/5175 四套 origin |
| 服务 health | PASS | `curl http://127.0.0.1:8099/health` → 200；前端 5199 → 200；代理 `/api/v1/guest/me` 可达 |
| 密钥泄露扫描 | PASS | 除 `.env` 外未发现硬编码 API Key/Token |

## 测试数据库隔离

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 测试库配置 | PASS | `backend/tests/fixtures/test.env` → `DATABASE_URL=sqlite+aiosqlite:///:memory:` |
| drop_all 静态检查 | PASS | `backend/tests/*` 无对运行时库 `drop_all` |
| pytest 后运行时库 | PASS | `backend/data/ai-music-companion.db` 仍含 9 张核心表（guest_sessions、chat_messages、playlists 等）；未被 pytest 清空 |

## 真实 API 主链路脚本（8099，2026-09-08）

```
PASS guest_session / onboarding_initial / onboarding_complete
PASS chat_meimei_recs (count=3, intent=play_song)
PASS chat_meimei_taylor (['TaylorSwift', 'TaylorSwift', 'Taylor Swift'])
PASS search_qingtian (count=5, q=晴天)
PASS play_url（Taylor Swift 曲目返回可播 URL）
PASS score（lines 等字段齐全）
PASS playlist_create / playlist_add / playlist_has_song
PASS clear_data / clear_onboarding_reset / clear_messages / clear_playlists
PASS vite_proxy（5199 → 8099）
```

## 本轮 Bugfix / 增强复核

| 功能 | 结果 | 证据 |
|------|------|------|
| 荐歌超时 60s | PASS | `frontend/src/services/api.ts` `LLM_REQUEST_TIMEOUT_MS = 60_000`；`chatService.ts` 使用该 timeout |
| 霉霉别名优先 | PASS | API：`想听霉霉的歌` → 3 条 Taylor Swift 推荐；单测 `test_music_keywords.py` / `test_chat.py` 通过 |
| 清除数据同步 Store | PASS | `sessionReset.ts` 重置 chat/player；`MePage.tsx` 清除后调用；后端 `test_guest.py` 断言消息为空 |
| 播放页等待 AI 荐歌 | PASS | `playerStore` 初始 `recommendationsReady=false`；`RecommendList.tsx` 等待态 UI |
| 上一首/下一首/三种模式 | PASS | `playerStore.ts` + `VinylPlayer.tsx` 实现 sequential/loop/shuffle |
| 歌单播放同步列表 | PASS | `PlaylistDetailPage.tsx` 播放前 `setRecommendations(playerSongs)` |
| 和弦指法扩展 | PASS | `chordShapes.ts` 含 Gm7/Cm7/Ebmaj7 等；`resolveChordShape` 支持 m7/maj7 归一化 |

## 浏览器自动化边界

- 项目 **无** Playwright/Cypress/E2E 目录；`package.json` 无浏览器测试脚本。
- 本次 **未** 执行真实浏览器页面交互；UI 行为通过静态代码审查 + 构建产物 + API 联调间接验证。
- 建议用户门禁（5175/8003）重点手测：VIP 试听弹窗、谱面抽屉指法图、播放器切歌/模式切换、清除后引导弹窗。

## 超出范围发现（不影响当前任务判定）

| # | 问题 | 所属模块 | 建议处理方式 |
|---|------|---------|------------|
| 1 | `ScoresPage` 仍走 Mock 列表 | 谱面列表页 | 后续任务或技术债；不在 T-011 主流程 |
| 2 | 「查看更多推荐」按钮未接接口 | 播放页 | 后续任务 |
| 3 | 网易云元数据偶现 `TaylorSwift` 无空格歌手名 | 音乐 Provider | 展示优化，非阻塞 |
| 4 | pytest 在无外网沙箱下 3 例失败（pyncm 代理 403），有网 64/64 | 测试环境 | CI/本地需允许网易云出站或 mock pyncm |

## 用户门禁清单（Orchestrator → 用户）

1. 偏好引导 → 首页心情 → 播放页等待荐歌 → 列表出现
2. 播放 / VIP 试听提示
3. 谱面抽屉 + 指法图
4. 收藏歌单 → 歌单内播放（左侧显示歌单曲目）
5. 播放器：上一首/下一首、三种播放模式
6. 我的 → 清除数据 → 聊天与推荐均清空 → 回到引导
