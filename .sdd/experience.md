# 项目经验

> 当前项目长期有效的经验。  
> Developer / Tester / Bugfix 在任务完成后维护本文件。

---

## Harness 系统经验摘要

新项目开始时，Developer / Tester / Bugfix 需要同时参考：

- 当前项目经验：`.sdd/experience.md`
- 系统级经验：`<Harness 根目录>/memory/harness-experience.md`

---

### [T-001]: 前端初始化与全局布局 Mock
- **陷阱**：`npm install` 在沙箱环境可能因 EPERM 警告耗时较长，但最终可成功；Mock 搜歌字段若用 `name`/`artist` 会与 api-contracts 不一致。
- **经验**：参考 smart-cs 脚手架快速落地 Vite+React+TS+Ant Design；顶栏样式直接复用原型 `style.css` 的 token（`#6B4EFF`、64px header、胶囊搜歌框）；`VITE_USE_MOCK=true` 时 GlobalSearch 只走 `mocks/songs.ts`，不触发 axios。
- **避坑**：`vite.config.ts` 必须同时配置 `/api` 与 `/ws` 代理；axios 实例须 `withCredentials: true` 以支持游客 Cookie；Mock 数据字段对齐 `SongSummary`（`song_name`/`artist_name`/`netease_song_id`）。

### [T-009]: 音乐播放从 MCP 改为 pyncm API 直连
- **陷阱**：`cloud-music-mcp` 通过 URL Scheme 唤起桌面客户端，无法在 Web 内嵌播放；MCP 不适合作为 Web 后端集成方式。
- **陷阱**：种子歌曲 ID 会过期或张冠李戴（如 `3339230677` 歌名虽叫晴天但专辑是《不散》，并非叶惠美版）；`186016` 是叶惠美正版元数据 ID，但 `GetTrackAudio` 常返回 404，**禁止**用 `PLAYBACK_ID_ALIASES` 静默换歌，否则 UI 显示周杰伦而实际播放翻唱。
- **经验**：搜索须过滤翻唱（歌名含「原唱/女声版/钢琴版」、歌手名带 `.`/`-` 后缀等）；种子库曲目视为唯一原版原唱；VIP 不可播时返回 `vip_required=true` 并前端弹窗确认跳转网易云。
- **经验**：荐歌返回的 ID 与播放 ID 必须一致，禁止静默换歌。
- **陷阱**：pyncm 未写入 `pyproject.toml` 时搜索/播放会静默降级到 Mock 种子。
- **陷阱**：大量 VIP 曲目游客模式无 Cookie 时 `GetTrackAudio` 返回空 URL，须配置 `NETEASE_COOKIE_PATH` 指向扫码登录后的 `cookies.json`。
- **经验**：后端 `music_provider.py` 直接用 pyncm 调用网易云 API；前端走 `GET /api/v1/songs/{id}/play-url` + HTML5 audio；无法播放时返回 50004 + `fallback_url` 外链兜底，不要用 demo 音频冒充真歌。
- **避坑**：`NETEASE_COOKIE_PATH` 配置在 `backend/.env`；Cookie 来源可用 `cloud-music-mcp` 扫码登录后导出的 `storage/cookies.json`。
- **陷阱**：网易云搜索可能返回旧版歌曲 ID（如晴天 `186016`），`GetTrackAudio` 返回空 URL 时接口会 50004；须在 `LEGACY_SONG_ID_ALIASES` 做 ID 映射，并在荐歌搜索后 `prioritize_playable_candidates` 过滤不可播放曲目。

### [T-010]: 荐歌/播放/谱面一致性
- **陷阱**：口语「我想听晴天」若整句拿去 pyncm 搜索，会召回无关歌曲；`prioritize_playable_candidates` 若不看相关性，会把可播放但无关的歌顶到前面。
- **陷阱**：播放器预加载第一首推荐音频时，`currentSong` 仍可能是旧 Mock ID（如 `100001`），导致 UI 歌名与实际音频不一致。
- **陷阱**：谱面 Mock 只认固定 `netease_song_id`；搜索返回同歌名不同 ID 时会 40403。
- **经验**：`extract_song_search_keywords` 剥离「我想听/播放」等前缀；搜索后按歌名相关性排序，再在强匹配集内优先可播放曲目；前端禁止静默预加载 audio，仅在 `playSong` 时绑定音源；`get_chord_source` 支持按歌名回落到种子谱面。
- **避坑**：前端默认推荐/当前歌曲使用与后端 `SEED_SONGS` 一致的真实网易云 ID，勿再用 `10000x` Mock ID 混入真实 API 流程。

### [T-012]: 音频扒谱 + 网易云扫码登录
- **陷阱**：`pyncm` 是进程级全局 Session，多用户并发会互相覆盖 Cookie；须用 `netease_session.run_with_netease_cookies` + 线程锁隔离。
- **陷阱**：从 `backend/` 直接 `uvicorn` 会 `ModuleNotFoundError: pycore`；须 `PYTHONPATH=.:..` 或 `scripts/dev-backend.sh`。
- **经验**：谱面生成走 `POST /score/jobs` 异步任务 + 进度轮询；歌词仍用网易云 LRC，和弦用 `librosa` chroma 模板匹配；校对谱 `verified` 仍优先命中缓存。
- **经验**：无播放权限时 `error_code=NEED_NETEASE_LOGIN` 弹扫码；已登录仍 VIP 不可播 →「抱歉，呜呜音源要钱」。

### [T-009+]: 播放加载与暂停恢复优化
- **陷阱**：`togglePlay` 暂停后再播放若重新调用 `playSong`，会重复请求 `play-url` 并重载 audio，导致每次恢复等待数秒。
- **经验**：前端缓存 play-url（Map + TTL）；暂停恢复时若同一首歌已加载则直接 `audio.play()`；推荐列表/聊天卡片预取前 3 首 URL，首条同时 `warmAudioBuffer` 预热。
- **经验**：后端 `resolve_direct_play_url` 内存缓存 1100s，避免每次播放都调 pyncm。
