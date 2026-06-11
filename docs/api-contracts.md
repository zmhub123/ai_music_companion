# 接口契约

> 前端 Mock 和后端实现的唯一对齐依据。任何变更必须同步更新本文件。

## 通用约定

### 基础路径

- 开发环境：`http://localhost:8000`
- 所有业务接口前缀：`/api/v1`
- 认证方式：游客 **HttpOnly Cookie** `guest_id`（UUID）；浏览器请求须 `credentials: 'include'`

### 统一响应格式

**成功：**

```json
{"code": 200, "message": "success", "data": {}}
```

**错误：**

```json
{"code": 40001, "message": "错误描述", "data": null}
```

**分页：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

### HTTP 状态码

| 状态码 | 含义 |
|--------|------|
| 200 | 成功 |
| 400 | 参数错误 |
| 401 | 游客 Session 无效或过期 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 业务错误码

| code | 含义 |
|------|------|
| 40001 | 参数校验失败 |
| 40101 | 游客 Session 无效 |
| 40401 | 歌单不存在 |
| 40402 | 歌曲不存在 |
| 40403 | 谱面暂无数据 |
| 50001 | LLM 调用失败 |
| 50002 | 网易云 API 调用失败 |
| 50003 | 和弦数据源失败 |
| 50004 | 播放地址获取失败 |

### 公共类型

```typescript
type SkillLevel = "beginner" | "intermediate" | "advanced";
type Instrument = "guitar" | "ukulele";

interface GuestProfile {
  guest_id: string;
  skill_level: SkillLevel | null;
  style_preferences: string[];
  onboarding_completed: boolean;
  created_at: string; // ISO8601
  last_active_at: string;
}

interface SongSummary {
  netease_song_id: number;
  song_name: string;
  artist_name: string;
  cover_url: string;
  album_name?: string;
  duration_ms?: number;
}

interface SongRecommendation {
  netease_song_id: number;
  song_name: string;
  artist_name: string;
  cover_url: string;
  reason: string;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  metadata: {
    intent?: "chat_only" | "recommend_music";
    recommendations?: SongRecommendation[];
  } | null;
  created_at: string;
}

interface Playlist {
  id: string;
  name: string;
  description: string | null;
  cover_url: string | null;
  song_count: number;
  created_at: string;
  updated_at: string;
}

interface PlaylistSong {
  id: string;
  netease_song_id: number;
  song_name: string;
  artist_name: string;
  cover_url: string | null;
  added_at: string;
}

interface ChordLine {
  position: number;
  chord: string;
  lyric_line: string;
}

interface ScoreDetail {
  netease_song_id: number;
  song_name: string;
  artist_name: string;
  cover_url: string;
  instrument: Instrument;
  skill_level: SkillLevel;
  key: string;
  capo: number;
  lines: ChordLine[];
  practice_tips: string | null;
}

interface PlayUrl {
  url: string;
  expires_in: number;
  quality: string;
  fallback_url: string | null;
}
```

---

## 接口清单

### GET /health

**说明：** 健康检查，无需 Cookie。

**响应（成功 200）：**

```json
{"code": 200, "message": "success", "data": {"status": "ok"}}
```

---

### POST /api/v1/guest/session

**说明：** 创建或续期游客 Session；响应 `Set-Cookie: guest_id=...; HttpOnly; Max-Age=2592000`。

**请求体：** 无

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "guest_id": "550e8400-e29b-41d4-a716-446655440000",
    "onboarding_completed": false,
    "skill_level": null,
    "style_preferences": []
  }
}
```

---

### GET /api/v1/guest/me

**说明：** 获取当前游客资料与偏好。

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "guest_id": "550e8400-e29b-41d4-a716-446655440000",
    "skill_level": "beginner",
    "style_preferences": ["民谣", "流行"],
    "onboarding_completed": true,
    "created_at": "2026-06-07T10:00:00Z",
    "last_active_at": "2026-06-07T12:00:00Z"
  }
}
```

**响应（失败 401）：**

```json
{"code": 40101, "message": "游客 Session 无效", "data": null}
```

---

### POST /api/v1/guest/onboarding

**说明：** 完成 P01 偏好引导，写入游客偏好。

**请求体：**

```json
{
  "skill_level": "beginner",
  "style_preferences": ["民谣", "流行", "摇滚"]
}
```

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "guest_id": "550e8400-e29b-41d4-a716-446655440000",
    "skill_level": "beginner",
    "style_preferences": ["民谣", "流行", "摇滚"],
    "onboarding_completed": true
  }
}
```

**响应（失败 400）：**

```json
{"code": 40001, "message": "style_preferences 至少选择 1 项", "data": null}
```

---

### PUT /api/v1/guest/preferences

**说明：** P06 修改弹唱水平与风格偏好。

**请求体：**

```json
{
  "skill_level": "intermediate",
  "style_preferences": ["爵士", "蓝调"]
}
```

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "skill_level": "intermediate",
    "style_preferences": ["爵士", "蓝调"]
  }
}
```

---

### DELETE /api/v1/guest/data

**说明：** 清除当前游客全部数据（对话、歌单、偏好），保留新 Session。

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "cleared": true,
    "onboarding_completed": false
  }
}
```

---

### GET /api/v1/chat/messages

**说明：** 获取当前游客会话内历史消息（按时间升序）。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 默认 1 |
| page_size | int | 否 | 默认 50，最大 100 |

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "msg-001",
        "role": "user",
        "content": "今天有点累，想听点安静的歌",
        "metadata": null,
        "created_at": "2026-06-07T10:01:00Z"
      },
      {
        "id": "msg-002",
        "role": "assistant",
        "content": "听起来你需要一些温柔的声音陪伴。我为你挑了几首适合放松的歌：",
        "metadata": {
          "intent": "recommend_music",
          "recommendations": [
            {
              "netease_song_id": 186016,
              "song_name": "晴天",
              "artist_name": "周杰伦",
              "cover_url": "https://p1.music.126.net/example.jpg",
              "reason": "旋律舒缓，适合放空思绪"
            }
          ]
        },
        "created_at": "2026-06-07T10:01:05Z"
      }
    ],
    "total": 2,
    "page": 1,
    "page_size": 50
  }
}
```

---

### POST /api/v1/chat/messages

**说明：** 发送用户消息，后端调用 LLM 生成回复；若识别荐歌意图则附带推荐卡片。

**请求体：**

```json
{
  "content": "推荐几首适合弹唱的民谣"
}
```

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user_message": {
      "id": "msg-003",
      "role": "user",
      "content": "推荐几首适合弹唱的民谣",
      "metadata": null,
      "created_at": "2026-06-07T10:02:00Z"
    },
    "assistant_message": {
      "id": "msg-004",
      "role": "assistant",
      "content": "民谣很适合用吉他慢慢弹。这几首和弦简单、氛围温暖：",
      "metadata": {
        "intent": "recommend_music",
        "recommendations": [
          {
            "netease_song_id": 25706282,
            "song_name": "南山南",
            "artist_name": "马頔",
            "cover_url": "https://p1.music.126.net/example2.jpg",
            "reason": "C 调基础和弦，零基础友好"
          },
          {
            "netease_song_id": 31654343,
            "song_name": "成都",
            "artist_name": "赵雷",
            "cover_url": "https://p1.music.126.net/example3.jpg",
            "reason": "节奏舒缓，适合边弹边唱"
          }
        ]
      },
      "created_at": "2026-06-07T10:02:08Z"
    }
  }
}
```

**响应（失败 500）：**

```json
{"code": 50001, "message": "AI 服务暂时不可用，请稍后再试", "data": null}
```

---

### POST /api/v1/chat/reset

**说明：** 清空当前游客对话上下文（F-02-06 新建对话）。

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "reset": true,
    "cleared_message_count": 12
  }
}
```

---

### GET /api/v1/songs/search

**说明：** 网易云歌曲搜索（内部荐歌链路也会使用）。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| q | string | 是 | 搜索关键词 |
| limit | int | 否 | 默认 10，最大 30 |

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "netease_song_id": 186016,
        "song_name": "晴天",
        "artist_name": "周杰伦",
        "cover_url": "https://p1.music.126.net/example.jpg",
        "album_name": "叶惠美",
        "duration_ms": 269000
      }
    ],
    "total": 1
  }
}
```

**响应（失败 500）：**

```json
{"code": 50002, "message": "曲库搜索失败", "data": null}
```

---

### GET /api/v1/songs/{netease_song_id}

**说明：** 获取单首歌曲元数据。

**路径参数：** `netease_song_id`（int）

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "netease_song_id": 186016,
    "song_name": "晴天",
    "artist_name": "周杰伦",
    "cover_url": "https://p1.music.126.net/example.jpg",
    "album_name": "叶惠美",
    "duration_ms": 269000,
    "netease_url": "https://music.163.com/song?id=186016"
  }
}
```

**响应（失败 404）：**

```json
{"code": 40402, "message": "歌曲不存在", "data": null}
```

---

### GET /api/v1/songs/{netease_song_id}/play-url

**说明：** 获取可播放音频地址（有时效）。

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "url": "https://m801.music.126.net/example.mp3",
    "expires_in": 1200,
    "quality": "standard",
    "fallback_url": "https://music.163.com/song?id=186016"
  }
}
```

**响应（失败 500）：**

```json
{
  "code": 50004,
  "message": "暂无法获取播放地址，请尝试外链播放",
  "data": {
    "fallback_url": "https://music.163.com/song?id=186016"
  }
}
```

---

### GET /api/v1/songs/{netease_song_id}/stream

**说明：** 音频流代理（CORS 兜底）；响应 `Content-Type: audio/mpeg`，直接返回二进制流。无需 JSON 包装。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| token | string | 否 | 短期签名，防滥用（实现可选） |

**响应（成功 200）：** `audio/mpeg` 二进制流

**响应（失败 404）：** JSON 错误体

```json
{"code": 40402, "message": "歌曲不存在", "data": null}
```

---

### GET /api/v1/songs/{netease_song_id}/score

**说明：** 获取弹唱谱（按游客水平与乐器渲染）。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| instrument | string | 否 | `guitar`（默认）或 `ukulele` |

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "netease_song_id": 25706282,
    "song_name": "南山南",
    "artist_name": "马頔",
    "cover_url": "https://p1.music.126.net/example2.jpg",
    "instrument": "guitar",
    "skill_level": "beginner",
    "key": "G",
    "capo": 0,
    "lines": [
      {"position": 0, "chord": "G", "lyric_line": "你在南方的艳阳里"},
      {"position": 8, "chord": "Em", "lyric_line": "大雪纷飞"},
      {"position": 12, "chord": "C", "lyric_line": "你会不会"},
      {"position": 16, "chord": "D", "lyric_line": "带着秋凉去"}
    ],
    "practice_tips": "整首歌以 G、Em、C、D 四个基础和弦循环，适合零基础练习扫弦节奏。"
  }
}
```

**响应（失败 404）：**

```json
{"code": 40403, "message": "暂无该歌曲谱面数据", "data": null}
```

---

### GET /api/v1/playlists

**说明：** 获取当前游客歌单列表（按 `updated_at` 倒序）。

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "pl-001",
        "name": "心情治愈",
        "description": "适合放松的曲子",
        "cover_url": "https://p1.music.126.net/example.jpg",
        "song_count": 3,
        "created_at": "2026-06-07T08:00:00Z",
        "updated_at": "2026-06-07T11:00:00Z"
      }
    ],
    "total": 1
  }
}
```

---

### POST /api/v1/playlists

**说明：** 创建空歌单。

**请求体：**

```json
{
  "name": "周末弹唱",
  "description": "适合周末练习的歌"
}
```

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "pl-002",
    "name": "周末弹唱",
    "description": "适合周末练习的歌",
    "cover_url": null,
    "song_count": 0,
    "created_at": "2026-06-07T12:00:00Z",
    "updated_at": "2026-06-07T12:00:00Z"
  }
}
```

---

### GET /api/v1/playlists/{playlist_id}

**说明：** 歌单详情含歌曲列表。

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "pl-001",
    "name": "心情治愈",
    "description": "适合放松的曲子",
    "cover_url": "https://p1.music.126.net/example.jpg",
    "song_count": 1,
    "created_at": "2026-06-07T08:00:00Z",
    "updated_at": "2026-06-07T11:00:00Z",
    "songs": [
      {
        "id": "pls-001",
        "netease_song_id": 186016,
        "song_name": "晴天",
        "artist_name": "周杰伦",
        "cover_url": "https://p1.music.126.net/example.jpg",
        "added_at": "2026-06-07T09:00:00Z"
      }
    ]
  }
}
```

**响应（失败 404）：**

```json
{"code": 40401, "message": "歌单不存在", "data": null}
```

---

### PUT /api/v1/playlists/{playlist_id}

**说明：** 编辑歌单名称与描述。

**请求体：**

```json
{
  "name": "心情治愈（更新）",
  "description": "更新后的描述"
}
```

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "pl-001",
    "name": "心情治愈（更新）",
    "description": "更新后的描述",
    "cover_url": "https://p1.music.126.net/example.jpg",
    "song_count": 1,
    "created_at": "2026-06-07T08:00:00Z",
    "updated_at": "2026-06-07T12:30:00Z"
  }
}
```

---

### DELETE /api/v1/playlists/{playlist_id}

**说明：** 删除歌单及其歌曲关联。

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "deleted": true,
    "playlist_id": "pl-001"
  }
}
```

---

### POST /api/v1/playlists/{playlist_id}/songs

**说明：** 向歌单添加歌曲（F-02-04 / F-03-05 收藏）。

**请求体：**

```json
{
  "netease_song_id": 25706282,
  "song_name": "南山南",
  "artist_name": "马頔",
  "cover_url": "https://p1.music.126.net/example2.jpg"
}
```

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "pls-002",
    "netease_song_id": 25706282,
    "song_name": "南山南",
    "artist_name": "马頔",
    "cover_url": "https://p1.music.126.net/example2.jpg",
    "added_at": "2026-06-07T12:35:00Z"
  }
}
```

**响应（失败 400）：**

```json
{"code": 40001, "message": "歌曲已在歌单中", "data": null}
```

---

### DELETE /api/v1/playlists/{playlist_id}/songs/{playlist_song_id}

**说明：** 从歌单移除歌曲。

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "deleted": true,
    "playlist_song_id": "pls-002"
  }
}
```
