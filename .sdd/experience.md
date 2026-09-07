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

### Bugfix: 前端 Vite 代理 ECONNREFUSED（非路由配错）
- **触发**：只运行 `npm run dev`、未先启动后端时，Vite 报 `http proxy error ... ECONNREFUSED`
- **根因**：代理目标 `8099` 无进程监听；不是 `/api` 路径或 axios `baseURL` 配置错误
- **已有经验回查**：T-001 要求配 `/api` 代理，但未覆盖「后端未启动」的识别方式
- **为什么仍然犯错**：错误信息像网络/路由故障，缺少启动期健康检查提示
- **修复**：`VITE_BACKEND_PROXY_TARGET` 默认改为 `http://127.0.0.1:8099`；`vite.config.ts` 启动时探测 `/health`；`dev-frontend.sh` 启动前检查后端
- **避坑规则**：本地开发必须双终端——先 `./scripts/dev-backend.sh`，再 `./scripts/dev-frontend.sh`；看到 ECONNREFUSED 先 `curl http://127.0.0.1:8099/health`

### Bugfix: 顶栏搜索点击无播放
- **触发**：搜索有结果，点击后仅跳转或无任何变化，播放器仍显示默认种子歌
- **根因**：`GlobalSearch` 只 `navigate('/player')`，未 `setRecommendations` / `playSong`
- **已有经验回查**：chatStore 已有荐歌→播放器联动模式，GlobalSearch 未复用
- **修复**：点击/回车时把搜索结果写入 `playerStore`，跳转后播放选中歌曲
- **避坑规则**：任何「选歌」入口（搜索、聊天卡片、歌单）必须同时更新 `recommendations` + `currentSong`（`playSong`）

### Bugfix: VIP 歌曲返回试听 URL 被误判为完整可播
- **触发**：VIP 歌曲（如《下一站天后》id=382844）聊天点歌后只播放约 30 秒即停止，无提示
- **根因**：网易云 `GetTrackAudio` 在游客 Session 下对 VIP 曲返回带 `freeTrialInfo.end=30` 的试听 MP3；后端仅以 `url` 非空判定 `playable=true`，忽略试听标记
- **已有经验回查**：T-009 覆盖无 URL 的 VIP 失败路径，未覆盖试听片段
- **为什么仍然犯错**：可播性检测与 play-url 未解析 `freeTrialInfo`/`fee` 组合态
- **修复**：`_inspect_track_audio_item` 识别试听；`play-url` 返回 `vip_trial`/`trial_duration_sec`；前端 `showVipTrialNotice` 弹窗
- **避坑规则**：`GetTrackAudio` 有 URL 不等于完整可播；必须检查 `freeTrialInfo` 或试听 CDN；荐歌 `vip_only` 在试听场景应为 true 且 `playable` 可为 true

### Bugfix: 网易云登录后仍播放 VIP 试听或无法播放
- **触发**：扫码登录 VIP 账号后，VIP 歌曲仍只播 30 秒或点击无反应
- **根因**：① 前端 `playUrlCache` 缓存了登录前的试听 URL，登录后未失效；② `vip_only && playable===false` 时前端直接拦截，不请求带 Cookie 的 `play-url`
- **修复**：登录/登出时 `clearPlaybackCache()`；已登录用户跳过 VIP 拦截并重新拉取 play-url；后端登录时 `invalidate_track_audio_cache()`
- **避坑规则**：网易云 Cookie 路径已能返回完整音源时，前端不得复用匿名试听缓存；部分曲目（如部分周杰伦版权）即使登录仍可能 50004，需提示「呜呜音源要钱」而非登录

### Bugfix: AI 生成曲谱和弦指法图为空
- **触发**：《Good Time》等 AI 扒谱曲目，右侧 Gm7/D#maj7 等指法格无按弦点
- **根因**：`chordShapes.ts` 仅含种子谱常用和弦；`resolveChordShape` 无法解析 m7、升号 maj7
- **修复**：补充 Gm7/Cm7/Ebmaj7/Abmaj7 等指法；增强和弦名归一化与回落查找；未命中显示「暂无指法」
- **避坑规则**：音频分析产出和弦名不受限，指法库与解析器须覆盖 m7/maj7/#b 根音；禁止静默渲染空指法图

### Bugfix: 歌手昵称荐歌被情绪词覆盖
- **触发**：用户说「想听霉霉的歌」，系统推荐「欢快 流行」类无关歌曲
- **根因**：① `_extract_mood_style_query` 因「高兴」优先返回情绪搜索词；② 「X的歌」一律被判为情绪/风格描述；③ 无歌手昵称别名表
- **已有经验回查**：有 T-010 歌名提取经验，但未覆盖歌手昵称与情绪优先级冲突
- **为什么仍然犯错**：情绪荐歌规则后于歌手实体识别设计，别名未纳入契约
- **修复**：`ARTIST_ALIASES` + `extract_artist_search_keywords`；关键词优先级歌手>歌名>情绪；歌手请求按 `artist_name` 排序
- **避坑规则**：「想听霉霉/周杰伦的歌」类请求必须先解析歌手别名；情绪词（开心/欢快）不得覆盖已识别歌手；`_looks_like_mood_style_target` 须区分「欢快的歌」与「霉霉的歌」

### Bugfix: 清除游客数据后前端 Store 未同步
- **触发**：点击「清除全部数据」后，AI 助手聊天框仍显示旧对话
- **根因**：后端 `DELETE /guest/data` 已删库，但 `chatStore.messages` 留在内存；`ChatFloat` 全局挂载不触发重新拉取
- **已有经验回查**：无直接条目
- **修复**：`resetAfterGuestClear` 清空 chat/player store；`MePage` 清除后调用 `resetClientSessionAfterGuestClear`；补后端测试断言消息为空
- **避坑规则**：任何「清除游客数据」入口必须同时重置前端 Zustand（聊天、播放器、鉴权），不能仅依赖后端删库或组件 remount

### Bugfix: 播放页初始不应展示种子推荐
- **触发**：首页心情进入播放页时，左侧先显示种子 5 首歌，AI 荐歌返回后才替换
- **根因**：`playerStore` 初始态直接挂载 `SEED_RECOMMENDATIONS`，无「等待荐歌」状态
- **修复**：`recommendationsReady` + 空列表初始态；`RecommendList` 等待态 UI；荐歌/搜索/历史消息写入后才 `ready`
- **避坑规则**：种子歌仅作后端降级与 Mock 对齐，不得作为播放页首屏默认展示；`setRecommendations` 是唯一「推荐就绪」入口
