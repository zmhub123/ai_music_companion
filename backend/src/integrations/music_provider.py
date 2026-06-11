"""歌曲搜索与播放：pyncm 直连网易云 API，不可用时降级种子召回。"""

from __future__ import annotations

import asyncio
import importlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pycore.core.logger import get_logger

logger = get_logger()

_pyncm_session_ready = False
_play_url_cache: dict[int, tuple[str, float]] = {}
PLAY_URL_CACHE_TTL = 1100.0

# 错误 ID → 元数据正版 ID（3339230677 实为专辑《不散》同名曲，非叶惠美版）
METADATA_ID_ALIASES: dict[int, int] = {
    3339230677: 186016,  # 晴天（叶惠美）
}

# 兼容旧引用
LEGACY_SONG_ID_ALIASES = METADATA_ID_ALIASES

SEED_SONGS: list[dict[str, Any]] = [
    {
        "netease_song_id": 186016,
        "song_name": "晴天",
        "artist_name": "周杰伦",
        "cover_url": "https://p1.music.126.net/example.jpg",
        "album_name": "叶惠美",
        "duration_ms": 269000,
        "tags": ["流行", "治愈", "轻松"],
    },
    {
        "netease_song_id": 29715551,
        "song_name": "南山南",
        "artist_name": "马頔",
        "cover_url": "https://p1.music.126.net/example2.jpg",
        "album_name": "南山南",
        "duration_ms": 251000,
        "tags": ["民谣", "弹唱", "吉他"],
    },
    {
        "netease_song_id": 436514312,
        "song_name": "成都",
        "artist_name": "赵雷",
        "cover_url": "https://p1.music.126.net/example3.jpg",
        "album_name": "无法长大",
        "duration_ms": 328000,
        "tags": ["民谣", "温暖", "弹唱"],
    },
    {
        "netease_song_id": 28815250,
        "song_name": "平凡之路",
        "artist_name": "朴树",
        "cover_url": "https://p1.music.126.net/example4.jpg",
        "album_name": "猎户星座",
        "duration_ms": 301000,
        "tags": ["摇滚", "励志", "公路"],
    },
    {
        "netease_song_id": 1330348068,
        "song_name": "起风了",
        "artist_name": "买辣椒也用券",
        "cover_url": "https://p1.music.126.net/example5.jpg",
        "album_name": "起风了",
        "duration_ms": 325000,
        "tags": ["流行", "治愈", "安静"],
    },
    {
        "netease_song_id": 478507889,
        "song_name": "卡农（经典钢琴版）",
        "artist_name": "dylanf",
        "cover_url": "",
        "album_name": "钢琴曲",
        "duration_ms": 240000,
        "tags": ["轻音乐", "安静"],
    },
    {
        "netease_song_id": 2023487708,
        "song_name": "茉莉花（轻音乐）",
        "artist_name": "天易",
        "cover_url": "",
        "album_name": "轻音乐",
        "duration_ms": 255000,
        "tags": ["轻音乐", "治愈"],
    },
]


@dataclass
class PlayabilityInfo:
    playable: bool
    vip_required: bool


@dataclass
class SongCandidate:
    netease_song_id: int
    song_name: str
    artist_name: str
    cover_url: str
    album_name: str | None = None
    duration_ms: int | None = None
    is_original: bool = False
    vip_only: bool = False
    playable: bool = False
    search_rank: int = 9999
    popularity: float = 0.0


@dataclass
class SongDetail:
    netease_song_id: int
    song_name: str
    artist_name: str
    cover_url: str
    album_name: str | None = None
    duration_ms: int | None = None


def netease_song_url(song_id: int) -> str:
    return f"https://music.163.com/song?id={song_id}"


_SONG_REQUEST_PREFIX = re.compile(
    r"^(?:请|帮我|给我|我想|想要|我要|想|来|放|播放|听|搜索|找|点)"
    r"(?:听|要|一首|首|段|点|播放|歌)?\s*",
    re.IGNORECASE,
)
_QUOTED_TITLE = re.compile(r"[《「『]([^》」』]+)[》」』]")


def _normalize_song_title(name: str) -> str:
    text = name.strip()
    text = re.sub(r"\s*[\(（].*?[\)）]\s*$", "", text).strip()
    return text


_SMALL_TALK_MARKERS = (
    "你好",
    "谢谢",
    "再见",
    "好累",
    "加班",
    "难过",
    "开心",
    "郁闷",
    "烦躁",
    "焦虑",
    "怎么办",
    "为什么",
    "可以吗",
    "在吗",
)


_MOOD_STYLE_TARGET_MARKERS = (
    "欢快",
    "轻快",
    "开心",
    "快乐",
    "愉快",
    "伤感",
    "难过",
    "安静",
    "治愈",
    "放松",
    "温柔",
    "甜蜜",
    "浪漫",
    "励志",
    "流行",
    "民谣",
    "摇滚",
    "古风",
    "独立",
    "爵士",
    "说唱",
    "节奏",
    "动感",
    "慵懒",
    "嗨",
    "元气",
    "emo",
    "那种",
    "这种",
    "一点",
    "一些",
    "几首",
    "风格",
    "类型",
)


def _extract_listen_target(text: str) -> str | None:
    match = re.search(
        r"(?:想听|我要听|播放|放一首|听一下|来一首|点一首|给我来|帮我找)\s*"
        r"([^，,。！!？?；;]+)",
        text,
    )
    if not match:
        return None
    return re.sub(r"^(?:一首|首|点|些)\s*", "", match.group(1).strip()).strip() or None


def _looks_like_mood_style_target(target: str) -> bool:
    cleaned = target.strip()
    if not cleaned or cleaned in {"歌", "曲", "音乐", "歌曲"}:
        return True
    if any(marker in cleaned for marker in _MOOD_STYLE_TARGET_MARKERS):
        return True
    if re.search(r"(的)?(歌|曲|音乐)$", cleaned) and len(cleaned) <= 12:
        return True
    return False


def is_direct_song_request(content: str) -> bool:
    """用户是否在点歌/说歌名（含「形容」「我想听晴天」等）。"""
    text = content.strip()
    if not text:
        return False

    if any(kw in text for kw in ("推荐", "来几首", "荐歌", "有什么歌", "哪些歌", "适合听")):
        return False

    if _QUOTED_TITLE.search(text):
        return True

    if re.search(r"(想听|我要听|播放|放一首|听一下|来一首|点一首|给我来|帮我找)", text):
        target = _extract_listen_target(text)
        if target and _looks_like_mood_style_target(target):
            return False
        if target:
            return True

    stripped = text
    for _ in range(4):
        next_text = _SONG_REQUEST_PREFIX.sub("", stripped).strip()
        if next_text == stripped:
            break
        stripped = next_text
    stripped = re.sub(r"^(?:的|一首|首|歌)\s*", "", stripped).strip()

    if any(marker in text for marker in _SMALL_TALK_MARKERS) and not stripped:
        return False

    if 2 <= len(stripped) <= 12 and not re.search(r"[？?！!。，]", stripped):
        if any(marker in text for marker in _SMALL_TALK_MARKERS):
            return False
        if any(kw in text for kw in ("几首", "适合", "风格", "类型", "一点")):
            return False
        return True

    return False


def extract_song_search_keywords(content: str) -> str:
    """从「我想听晴天」等口语中提取可搜索的歌名/关键词。"""
    text = content.strip()
    if not text:
        return ""

    quoted = _QUOTED_TITLE.search(text)
    if quoted:
        return _normalize_song_title(quoted.group(1))

    for item in SEED_SONGS:
        seed_name = str(item["song_name"])
        if seed_name and seed_name in text:
            return seed_name

    cleaned = text
    for _ in range(4):
        next_text = _SONG_REQUEST_PREFIX.sub("", cleaned).strip()
        if next_text == cleaned:
            break
        cleaned = next_text

    cleaned = re.sub(r"^(?:的|一首|首|歌)\s*", "", cleaned).strip()
    if cleaned:
        return cleaned[:30]
    return text[:30]


def _relevance_score(song: SongCandidate, keywords: str) -> int:
    k = _normalize_song_title(keywords).lower()
    if not k:
        return 0

    name = _normalize_song_title(song.song_name).lower()
    artist = song.artist_name.lower()

    if k == name:
        return 100
    if name.startswith(k) or k.startswith(name):
        return 90
    if k in name:
        return 80
    if name in k:
        return 70
    if k in artist:
        return 40

    score = 0
    for part in re.split(r"[\s,，、]+", k):
        if len(part) < 2:
            continue
        if part in name:
            score += 35
        if part in artist:
            score += 10
    return score


def _normalize_artist_key(name: str) -> str:
    return re.sub(r"[.、\-_\s·]", "", name.lower())


def _strict_artist_equals(actual: str, expected: str) -> bool:
    if actual.strip().endswith((".", "-", "、", "·")):
        return False
    return _normalize_artist_key(actual) == _normalize_artist_key(expected)


_COVER_TITLE_KEYWORDS = (
    "翻唱",
    "女声版",
    "男声版",
    "钢琴版",
    "吉他版",
    "尤克里里",
    "伤感版",
    "深情版",
    "正式版",
    "DJ版",
    "铃声",
    "伴奏",
    "纯音乐",
    "instrumental",
    "伴奏版",
    "cover",
    "live",
    "remix",
    "混音",
    "改编",
    "gamer",
    "version",
    "versi",
    "伴奏版",
    "演奏版",
    "朗读",
    "念白",
)
_COVER_TITLE_REGEX = re.compile(r"原唱[：:\s]|翻唱|\([^)]*版\)|（[^）]*版）", re.I)


def _official_seed_ids() -> set[int]:
    return {int(item["netease_song_id"]) for item in SEED_SONGS}


def _official_seed_for_title(title: str) -> dict[str, Any] | None:
    norm = _normalize_song_title(title)
    for item in SEED_SONGS:
        if _normalize_song_title(str(item["song_name"])) == norm:
            return item
    return None


def _is_official_seed_song(song: SongCandidate) -> bool:
    if song.netease_song_id in _official_seed_ids():
        return True
    seed = _official_seed_for_title(_normalize_song_title(song.song_name))
    if seed is None:
        return False
    if _normalize_song_title(song.song_name) != _normalize_song_title(str(seed["song_name"])):
        return False
    return _strict_artist_equals(song.artist_name, str(seed["artist_name"]))


def _latin_keyword_in_title(name: str, keyword: str) -> bool:
    lowered = name.lower()
    kw = keyword.lower()
    if kw not in lowered:
        return False
    return bool(
        re.search(
            rf"(?:^|[\s(（\[「『:/-]){re.escape(kw)}(?:\b|[\s)）\]」』:/-]|$)",
            lowered,
        )
    )


def _is_obvious_cover(song: SongCandidate) -> bool:
    name = song.song_name
    latin_markers = {"cover", "live", "remix", "version", "gamer", "versi", "instrumental"}
    for keyword in _COVER_TITLE_KEYWORDS:
        if keyword.lower() in latin_markers:
            if _latin_keyword_in_title(name, keyword):
                return True
        elif keyword.lower() in name.lower():
            return True
    if _COVER_TITLE_REGEX.search(name):
        return True

    artist = song.artist_name.strip()
    if artist.endswith((".", "-", "、", "·")):
        return True
    return False


def _is_cover_version(song: SongCandidate, *, canonical: SongCandidate | None = None) -> bool:
    if song.netease_song_id in _official_seed_ids():
        return False
    if _is_obvious_cover(song):
        return True

    title = _normalize_song_title(song.song_name)
    seed = _official_seed_for_title(title)
    if seed is not None:
        official_artist = str(seed["artist_name"])
        if not _strict_artist_equals(song.artist_name, official_artist):
            return True

    if canonical is not None and song.netease_song_id != canonical.netease_song_id:
        if title == _normalize_song_title(canonical.song_name):
            if _strict_artist_equals(song.artist_name, canonical.artist_name):
                return False
            canon_pop = canonical.popularity or 0.0
            song_pop = song.popularity or 0.0
            if canon_pop >= 30 and song_pop < canon_pop * 0.65:
                return True
            if (
                canon_pop > 0
                and song_pop <= canon_pop * 0.8
                and song.search_rank > canonical.search_rank + 1
            ):
                return True
    return False


def _pick_netease_canonical(candidates: list[SongCandidate], query: str) -> SongCandidate | None:
    title = _normalize_song_title(query)
    if not title:
        return None

    exact_matches = [
        song
        for song in sorted(candidates, key=lambda item: item.search_rank)
        if _normalize_song_title(song.song_name) == title and not _is_obvious_cover(song)
    ]
    if not exact_matches:
        exact_matches = [
            song
            for song in sorted(candidates, key=lambda item: item.search_rank)
            if title in _normalize_song_title(song.song_name) and not _is_obvious_cover(song)
        ]
    if not exact_matches:
        return None

    seed = _official_seed_for_title(title)
    if seed is not None:
        for song in exact_matches:
            if _strict_artist_equals(song.artist_name, str(seed["artist_name"])):
                return song

    return max(
        exact_matches,
        key=lambda song: (
            song.popularity,
            0 if not re.search(r"[\(（\[]", song.song_name) else -1,
            -len(song.song_name),
            -song.search_rank,
        ),
    )


def _official_seed_candidates(query: str, limit: int = 3) -> list[SongCandidate]:
    norm = _normalize_song_title(query)
    matched: list[SongCandidate] = []
    for item in SEED_SONGS:
        seed_name = _normalize_song_title(str(item["song_name"]))
        if seed_name != norm and norm not in seed_name:
            continue
        matched.append(
            SongCandidate(
                netease_song_id=int(item["netease_song_id"]),
                song_name=str(item["song_name"]),
                artist_name=str(item["artist_name"]),
                cover_url=str(item.get("cover_url") or ""),
                album_name=str(item.get("album_name") or "") or None,
                duration_ms=int(item["duration_ms"]) if item.get("duration_ms") else None,
                is_original=True,
                search_rank=0,
            )
        )
    return matched[:limit]


def _rank_score(song: SongCandidate, keywords: str) -> tuple[int, int, int]:
    relevance = _relevance_score(song, keywords)
    official_boost = 80 if _is_official_seed_song(song) else 0
    album_boost = 0
    seed = _official_seed_for_title(keywords)
    if seed and (song.album_name or "") == str(seed.get("album_name") or ""):
        album_boost = 30
    return (relevance + official_boost + album_boost, relevance, song.duration_ms or 0)


def _sort_by_relevance(candidates: list[SongCandidate], keywords: str) -> list[SongCandidate]:
    if not candidates:
        return candidates
    return sorted(
        candidates,
        key=lambda song: _rank_score(song, keywords),
        reverse=True,
    )


def _build_search_queries(keywords: str) -> list[str]:
    query = extract_song_search_keywords(keywords) or keywords.strip()
    if not query:
        return [keywords.strip()]

    queries = [query]
    if len(query) <= 12:
        for extra in (f"{query} 原唱",):
            if extra not in queries:
                queries.append(extra)
    for item in SEED_SONGS:
        if str(item["song_name"]) == query:
            combined = f"{query} {item['artist_name']}"
            if combined not in queries:
                queries.append(combined)
            break
    return queries


def _resolve_metadata_ids(song_id: int) -> list[int]:
    canonical = METADATA_ID_ALIASES.get(song_id)
    if canonical is not None:
        return [canonical, song_id]
    return [song_id]


def _resolve_song_ids(song_id: int) -> list[int]:
    """播放与可播检测：严格使用搜索/荐歌返回的曲目 ID，不做静默替换。"""
    return [song_id]


def _pyncm_available() -> bool:
    try:
        importlib.import_module("pyncm")
        return True
    except ImportError:
        return False


def _ensure_pyncm_session() -> None:
    """加载可选 Cookie，提升 VIP 曲目播放成功率。"""
    global _pyncm_session_ready
    if _pyncm_session_ready or not _pyncm_available():
        return

    try:
        from src.core.config import get_settings

        cookie_path = get_settings().netease_cookie_path.strip()
        if not cookie_path:
            _pyncm_session_ready = True
            return

        path = Path(cookie_path).expanduser()
        if not path.is_file():
            logger.warning("netease cookie file not found", path=str(path))
            _pyncm_session_ready = True
            return

        pyncm = importlib.import_module("pyncm")
        with path.open(encoding="utf-8") as f:
            cookies = json.load(f)
        pyncm.GetCurrentSession().cookies.update(cookies)
        logger.info("netease cookies loaded", path=str(path))
    except Exception as exc:
        logger.warning("failed to load netease cookies", error=str(exc))
    finally:
        _pyncm_session_ready = True


def _search_seed(keywords: str, limit: int) -> list[SongCandidate]:
    q = keywords.strip().lower()
    matched: list[SongCandidate] = []
    for item in SEED_SONGS:
        haystack = " ".join(
            [item["song_name"], item["artist_name"], *item.get("tags", [])]
        ).lower()
        if not q or q in haystack or any(part in haystack for part in q.split()):
            matched.append(
                SongCandidate(
                    netease_song_id=int(item["netease_song_id"]),
                    song_name=str(item["song_name"]),
                    artist_name=str(item["artist_name"]),
                    cover_url=str(item.get("cover_url") or ""),
                )
            )
    if not matched:
        matched = [
            SongCandidate(
                netease_song_id=int(item["netease_song_id"]),
                song_name=str(item["song_name"]),
                artist_name=str(item["artist_name"]),
                cover_url=str(item.get("cover_url") or ""),
            )
            for item in SEED_SONGS
        ]
    return matched[:limit]


def _search_pyncm_sync(keywords: str, limit: int) -> list[SongCandidate]:
    _ensure_pyncm_session()
    apis = importlib.import_module("pyncm.apis")
    result = apis.cloudsearch.GetSearchResult(keywords, stype=1, limit=limit)
    songs = result.get("result", {}).get("songs", []) if isinstance(result, dict) else []
    candidates: list[SongCandidate] = []
    for song in songs[:limit]:
        if not isinstance(song, dict):
            continue
        song_id = song.get("id")
        if song_id is None:
            continue
        artists = song.get("ar") or song.get("artists") or []
        artist_name = "未知歌手"
        if artists and isinstance(artists[0], dict):
            artist_name = str(artists[0].get("name") or artist_name)
        album = song.get("al") or song.get("album") or {}
        cover_url = ""
        if isinstance(album, dict):
            cover_url = str(album.get("picUrl") or album.get("blurPicUrl") or "")
        album_name = None
        if isinstance(album, dict) and album.get("name"):
            album_name = str(album["name"])
        duration_ms = song.get("dt") or song.get("duration")
        pop_raw = song.get("pop")
        popularity = float(pop_raw) if pop_raw is not None else 0.0
        candidates.append(
            SongCandidate(
                netease_song_id=int(song_id),
                song_name=str(song.get("name") or "未知歌曲"),
                artist_name=artist_name,
                cover_url=cover_url,
                album_name=album_name,
                duration_ms=int(duration_ms) if duration_ms else None,
                popularity=popularity,
            )
        )
    return candidates


def _seed_by_id(song_id: int) -> dict[str, Any] | None:
    for item in SEED_SONGS:
        if int(item["netease_song_id"]) == song_id:
            return item
    return None


def _seed_to_detail(item: dict[str, Any]) -> SongDetail:
    return SongDetail(
        netease_song_id=int(item["netease_song_id"]),
        song_name=str(item["song_name"]),
        artist_name=str(item["artist_name"]),
        cover_url=str(item.get("cover_url") or ""),
        album_name=str(item["album_name"]) if item.get("album_name") else None,
        duration_ms=int(item["duration_ms"]) if item.get("duration_ms") else None,
    )


def _detail_pyncm_sync(song_id: int) -> SongDetail | None:
    _ensure_pyncm_session()
    apis = importlib.import_module("pyncm.apis")
    result = apis.track.GetTrackDetail(song_id)
    song = result.get("songs", [{}])[0] if isinstance(result, dict) else {}
    if not isinstance(song, dict) or not song.get("id"):
        return None
    artists = song.get("ar") or song.get("artists") or []
    artist_name = "未知歌手"
    if artists and isinstance(artists[0], dict):
        artist_name = str(artists[0].get("name") or artist_name)
    album = song.get("al") or song.get("album") or {}
    album_name = None
    cover_url = ""
    if isinstance(album, dict):
        album_name = str(album.get("name")) if album.get("name") else None
        cover_url = str(album.get("picUrl") or album.get("blurPicUrl") or "")
    return SongDetail(
        netease_song_id=int(song["id"]),
        song_name=str(song.get("name") or "未知歌曲"),
        artist_name=artist_name,
        cover_url=cover_url,
        album_name=album_name,
        duration_ms=int(song.get("dt") or song.get("duration") or 0) or None,
    )


def _extract_play_url(audio_item: dict[str, Any]) -> str | None:
    if audio_item.get("code") not in (None, 200):
        return None
    url = audio_item.get("url")
    return str(url) if url else None


def _playability_map_sync(song_ids: list[int]) -> dict[int, PlayabilityInfo]:
    if not song_ids:
        return {}
    _ensure_pyncm_session()
    apis = importlib.import_module("pyncm.apis")
    result = apis.track.GetTrackAudio(song_ids)
    if not isinstance(result, dict):
        return {}

    info_map: dict[int, PlayabilityInfo] = {}
    for item in result.get("data") or []:
        if not isinstance(item, dict):
            continue
        song_id = item.get("id")
        if song_id is None:
            continue
        sid = int(song_id)
        if _extract_play_url(item):
            info_map[sid] = PlayabilityInfo(playable=True, vip_required=False)
            continue
        code = item.get("code")
        fee = item.get("fee")
        vip_required = code == 404 or fee == 1
        info_map[sid] = PlayabilityInfo(playable=False, vip_required=vip_required)
    return info_map


def _playable_ids_pyncm_sync(song_ids: list[int]) -> set[int]:
    return {
        sid
        for sid, info in _playability_map_sync(song_ids).items()
        if info.playable
    }


def _play_url_pyncm_sync(song_id: int) -> str | None:
    _ensure_pyncm_session()
    apis = importlib.import_module("pyncm.apis")
    for sid in _resolve_song_ids(song_id):
        result = apis.track.GetTrackAudio([sid])
        if not isinstance(result, dict):
            continue
        data_list = result.get("data") or []
        if not data_list or not isinstance(data_list[0], dict):
            continue
        url = _extract_play_url(data_list[0])
        if url:
            return url
    return None


async def check_playability(song_id: int) -> PlayabilityInfo:
    if not _pyncm_available():
        return PlayabilityInfo(playable=False, vip_required=False)
    try:
        info_map = await asyncio.to_thread(_playability_map_sync, [song_id])
        return info_map.get(song_id, PlayabilityInfo(playable=False, vip_required=False))
    except Exception as exc:
        logger.warning("playability check failed", song_id=song_id, error=str(exc))
        return PlayabilityInfo(playable=False, vip_required=False)


async def _enrich_playability(candidates: list[SongCandidate]) -> list[SongCandidate]:
    if not candidates or not _pyncm_available():
        return candidates
    ids = [song.netease_song_id for song in candidates]
    try:
        info_map = await asyncio.to_thread(_playability_map_sync, ids[:20])
    except Exception as exc:
        logger.warning("playability enrich failed", error=str(exc))
        return candidates

    for song in candidates:
        info = info_map.get(song.netease_song_id)
        if info is None:
            continue
        song.playable = info.playable
        song.vip_only = info.vip_required and not info.playable
    return candidates


def _sort_original_first(candidates: list[SongCandidate], keywords: str) -> list[SongCandidate]:
    query = _normalize_song_title(keywords)

    def sort_key(song: SongCandidate) -> tuple[int, int, int, int, int, int, int]:
        title = _normalize_song_title(song.song_name)
        cover_penalty = 1 if _is_obvious_cover(song) else 0
        suffix_penalty = 1 if re.search(r"[\(（\[]", song.song_name) else 0
        title_penalty = 0 if title == query else (1 if query and query in title else 2)
        original = 0 if song.is_original else 1
        play_tier = 0 if song.playable else (1 if song.vip_only else 2)
        rank = _rank_score(song, keywords)
        return (
            cover_penalty,
            suffix_penalty,
            original,
            title_penalty,
            play_tier,
            -int(song.popularity),
            song.search_rank,
            -rank[0],
        )

    return sorted(candidates, key=sort_key)


def _merge_candidates(
    primary: list[SongCandidate], secondary: list[SongCandidate]
) -> list[SongCandidate]:
    by_id: dict[int, SongCandidate] = {}
    for song in primary + secondary:
        existing = by_id.get(song.netease_song_id)
        if existing is None or song.search_rank < existing.search_rank:
            by_id[song.netease_song_id] = song
    return sorted(by_id.values(), key=lambda item: item.search_rank)


def _assign_search_ranks(candidates: list[SongCandidate], start: int = 0) -> int:
    rank = start
    for song in candidates:
        song.search_rank = rank
        rank += 1
    return rank


def _candidate_to_dict(song: SongCandidate) -> dict[str, Any]:
    return {
        "netease_song_id": song.netease_song_id,
        "song_name": song.song_name,
        "artist_name": song.artist_name,
        "cover_url": song.cover_url,
        "album_name": song.album_name,
        "duration_ms": song.duration_ms,
        "is_original": song.is_original,
        "vip_only": song.vip_only,
        "playable": song.playable,
    }


async def search_songs(keywords: str, limit: int = 10, *, fetch_limit: int | None = None) -> list[SongCandidate]:
    query = extract_song_search_keywords(keywords) or keywords.strip()
    search_queries = _build_search_queries(keywords)
    official = _official_seed_candidates(query, limit)
    remote_fetch = fetch_limit or max(limit * 4, 20)

    remote_originals: list[SongCandidate] = []
    netease_canonical: SongCandidate | None = None
    if _pyncm_available():
        try:
            remote: list[SongCandidate] = []
            rank_cursor = 0
            for q in search_queries:
                batch = await asyncio.to_thread(_search_pyncm_sync, q, remote_fetch)
                _assign_search_ranks(batch, rank_cursor)
                rank_cursor += len(batch)
                remote = _merge_candidates(remote, batch)
            netease_canonical = _pick_netease_canonical(remote, query)
            remote_originals = [
                song
                for song in remote
                if not _is_cover_version(song, canonical=netease_canonical)
            ]
            for song in remote_originals:
                if _is_official_seed_song(song):
                    song.is_original = True
                elif netease_canonical is not None and song.netease_song_id == netease_canonical.netease_song_id:
                    song.is_original = True
                elif netease_canonical is not None and _normalize_song_title(
                    song.song_name
                ) == _normalize_song_title(netease_canonical.song_name) and _strict_artist_equals(
                    song.artist_name, netease_canonical.artist_name
                ):
                    song.is_original = True
                else:
                    song.is_original = False
            if remote:
                logger.info(
                    "pyncm search hit",
                    keywords=keywords,
                    query=query,
                    search_queries=search_queries,
                    total=len(remote),
                    originals=len(remote_originals),
                    canonical_id=netease_canonical.netease_song_id if netease_canonical else None,
                )
        except Exception as exc:
            logger.warning("pyncm search failed, fallback to seed", error=str(exc))

    candidates = _merge_candidates(official, remote_originals)
    if not candidates:
        candidates = official or [
            song
            for song in _search_seed(query, limit)
            if not _is_cover_version(song, canonical=netease_canonical)
        ]
        logger.info("music search using seed fallback", keywords=keywords, query=query)

    for song in candidates:
        if _is_official_seed_song(song):
            song.is_original = True

    candidates = await _enrich_playability(candidates)
    candidates = _sort_original_first(candidates, query)
    return candidates[:limit]


async def get_song_detail(song_id: int) -> SongDetail | None:
    if _pyncm_available():
        try:
            for sid in _resolve_metadata_ids(song_id):
                detail = await asyncio.to_thread(_detail_pyncm_sync, sid)
                if detail is not None:
                    return detail
        except Exception as exc:
            logger.warning("pyncm detail failed, fallback to seed", song_id=song_id, error=str(exc))

    seed = _seed_by_id(song_id)
    if seed is None:
        return None
    return _seed_to_detail(seed)


async def resolve_direct_play_url(song_id: int) -> str | None:
    now = time.monotonic()
    cached = _play_url_cache.get(song_id)
    if cached and now < cached[1]:
        return cached[0]

    if _pyncm_available():
        try:
            url = await asyncio.to_thread(_play_url_pyncm_sync, song_id)
            if url:
                _play_url_cache[song_id] = (url, now + PLAY_URL_CACHE_TTL)
                return url
        except Exception as exc:
            logger.warning("pyncm play url failed", song_id=song_id, error=str(exc))
    return None


async def resolve_stream_source(song_id: int) -> str | None:
    direct = await resolve_direct_play_url(song_id)
    if direct:
        return direct

    logger.info("no playable url for song", song_id=song_id)
    return None
