"""歌曲搜索与播放服务。"""

from __future__ import annotations

from typing import Any

# netease_cookies 通过游客 Session 注入 pyncm，提升 VIP 曲目可播率

from pycore.core.logger import get_logger
from src.api.errors import AppApiError
from src.integrations.music_provider import (
    SongDetail,
    check_playability,
    get_song_detail,
    netease_song_url,
    resolve_direct_play_url,
    resolve_stream_source,
    search_songs,
)

logger = get_logger()


def _summary_dict(detail: SongDetail) -> dict[str, Any]:
    return {
        "netease_song_id": detail.netease_song_id,
        "song_name": detail.song_name,
        "artist_name": detail.artist_name,
        "cover_url": detail.cover_url,
        "album_name": detail.album_name,
        "duration_ms": detail.duration_ms,
    }


async def search_song_list(keywords: str, limit: int = 10) -> dict[str, Any]:
    q = keywords.strip()
    if not q:
        raise AppApiError(40001, "搜索关键词不能为空")

    limit = min(max(limit, 1), 30)
    try:
        candidates = await search_songs(q, limit=limit)
    except Exception as exc:
        logger.error("song search failed", error=str(exc))
        raise AppApiError(50002, "曲库搜索失败", http_status=500) from exc

    items = [
        {
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
        for song in candidates
    ]
    return {"items": items, "total": len(items)}


async def get_song(song_id: int) -> dict[str, Any]:
    detail = await get_song_detail(song_id)
    if detail is None:
        raise AppApiError(40402, "歌曲不存在", http_status=404)
    data = _summary_dict(detail)
    data["netease_url"] = netease_song_url(song_id)
    return data


async def get_play_url(song_id: int, *, netease_cookies: dict[str, Any] | None = None) -> dict[str, Any]:
    fallback = netease_song_url(song_id)
    if netease_cookies:
        from src.integrations.netease_session import run_with_netease_cookies
        from src.integrations.music_provider import _play_url_pyncm_sync
        import asyncio

        direct = await asyncio.to_thread(
            lambda: run_with_netease_cookies(netease_cookies, lambda: _play_url_pyncm_sync(song_id))
        )
    else:
        direct = await resolve_direct_play_url(song_id)
    if direct:
        return {
            "url": direct,
            "expires_in": 1200,
            "quality": "standard",
            "fallback_url": fallback,
        }

    detail = await get_song_detail(song_id)
    if detail is None:
        raise AppApiError(40402, "歌曲不存在", http_status=404)

    playability = await check_playability(song_id)
    if playability.vip_required:
        message = (
            "抱歉，呜呜音源要钱"
            if netease_cookies
            else "该歌曲为 VIP 专享，登录网易云后重试"
        )
        raise AppApiError(
            50004,
            message,
            http_status=500,
            data={
                "fallback_url": fallback,
                "vip_required": True,
                "need_netease_login": not bool(netease_cookies),
            },
        )

    raise AppApiError(
        50004,
        "暂无法获取播放地址，请尝试外链播放",
        http_status=500,
        data={"fallback_url": fallback, "vip_required": False},
    )


async def get_stream_source(song_id: int) -> str:
    source = await resolve_stream_source(song_id)
    if source is None:
        raise AppApiError(40402, "歌曲不存在", http_status=404)
    return source
