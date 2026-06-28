"""歌曲搜索与播放服务。"""

from __future__ import annotations

from typing import Any

# netease_cookies 通过游客 Session 注入 pyncm，提升 VIP 曲目可播率
from pycore.core.logger import get_logger
from src.api.errors import AppApiError
from src.core.flow_log import begin_flow, end_flow, log_step
from src.integrations.music_provider import (
    SongDetail,
    TrackAudioResult,
    check_playability,
    get_song_detail,
    netease_song_url,
    resolve_stream_source,
    resolve_track_audio,
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
    flow_id = begin_flow("顶栏搜索")
    log_step("收到搜索请求", keywords=q, limit=limit)
    try:
        candidates = await search_songs(q, limit=limit)
    except Exception as exc:
        end_flow(status="failed", error=str(exc))
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
    end_flow(result_count=len(items), flow_id=flow_id)
    return {"items": items, "total": len(items)}


async def get_song(song_id: int) -> dict[str, Any]:
    detail = await get_song_detail(song_id)
    if detail is None:
        raise AppApiError(40402, "歌曲不存在", http_status=404)
    data = _summary_dict(detail)
    data["netease_url"] = netease_song_url(song_id)
    return data


def _play_url_payload(audio: TrackAudioResult, fallback: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "url": audio.url,
        "expires_in": 1200,
        "quality": "standard",
        "fallback_url": fallback,
    }
    if audio.info.trial_preview:
        payload["vip_trial"] = True
        payload["trial_duration_sec"] = audio.info.trial_duration_sec or 30
        payload["vip_only"] = True
    return payload


async def get_play_url(song_id: int, *, netease_cookies: dict[str, Any] | None = None) -> dict[str, Any]:
    flow_id = begin_flow("播放地址")
    log_step(
        "请求播放地址",
        song_id=song_id,
        has_netease_cookie=bool(netease_cookies),
    )
    fallback = netease_song_url(song_id)
    if netease_cookies:
        import asyncio

        from src.integrations.music_provider import _fetch_track_audio_pyncm_sync
        from src.integrations.netease_session import run_with_netease_cookies

        audio = await asyncio.to_thread(
            lambda: run_with_netease_cookies(
                netease_cookies, lambda: _fetch_track_audio_pyncm_sync(song_id)
            )
        )
        log_step(
            "使用游客网易云 Cookie 获取播放地址",
            song_id=song_id,
            hit=bool(audio and audio.url),
            vip_trial=bool(audio and audio.info.trial_preview),
        )
    else:
        audio = await resolve_track_audio(song_id)
        log_step(
            "使用默认 pyncm Session 获取播放地址",
            song_id=song_id,
            hit=bool(audio and audio.url),
            vip_trial=bool(audio and audio.info.trial_preview),
        )
    if audio and audio.url:
        end_flow(flow_id=flow_id, song_id=song_id, status="ok", source="direct")
        return _play_url_payload(audio, fallback)

    detail = await get_song_detail(song_id)
    if detail is None:
        end_flow(flow_id=flow_id, song_id=song_id, status="not_found")
        raise AppApiError(40402, "歌曲不存在", http_status=404)

    playability = await check_playability(song_id)
    log_step(
        "播放地址失败，检查可播性",
        song_id=song_id,
        playable=playability.playable,
        vip_required=playability.vip_required,
        song_name=getattr(detail, "song_name", None),
        artist_name=getattr(detail, "artist_name", None),
    )
    if playability.vip_required:
        message = (
            "抱歉，呜呜音源要钱"
            if netease_cookies
            else "该歌曲为 VIP 专享，登录网易云后重试"
        )
        end_flow(flow_id=flow_id, song_id=song_id, status="vip_required")
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

    end_flow(flow_id=flow_id, song_id=song_id, status="unavailable")
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
