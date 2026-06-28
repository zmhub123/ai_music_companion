"""荐歌 / 搜索 / 播放链路结构化日志。"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any
from uuid import uuid4

from pycore.core.logger import get_logger

logger = get_logger()

_flow_id: ContextVar[str | None] = ContextVar("recommend_flow_id", default=None)
_flow_label: ContextVar[str | None] = ContextVar("recommend_flow_label", default=None)


def begin_flow(label: str) -> str:
    """开启一条可跨函数调用的链路日志（同一次 HTTP 请求内有效）。"""
    flow_id = uuid4().hex[:8]
    _flow_id.set(flow_id)
    _flow_label.set(label)
    log_step("链路开始", label=label)
    return flow_id


def end_flow(**fields: Any) -> None:
    """结束链路并清理上下文。"""
    log_step("链路结束", **fields)
    _flow_id.set(None)
    _flow_label.set(None)


def current_flow_id() -> str | None:
    return _flow_id.get()


def log_step(step: str, **fields: Any) -> None:
    flow_id = _flow_id.get() or "-"
    label = _flow_label.get()
    prefix = f"[链路 {flow_id}]"
    if label:
        prefix = f"{prefix}[{label}]"
    if not fields:
        logger.info(f"{prefix} {step}")
        return
    parts = " | ".join(f"{key}={_format_value(value)}" for key, value in fields.items())
    logger.info(f"{prefix} {step} | {parts}")


def format_song_line(
    song: Any,
    *,
    index: int | None = None,
    extra: str = "",
) -> str:
    if isinstance(song, dict):
        song_id = song.get("netease_song_id")
        name = song.get("song_name")
        artist = song.get("artist_name")
        original = song.get("is_original")
        playable = song.get("playable")
        vip = song.get("vip_only")
    else:
        song_id = song.netease_song_id
        name = song.song_name
        artist = song.artist_name
        original = song.is_original
        playable = song.playable
        vip = song.vip_only

    head = f"{index}. " if index is not None else ""
    flags = []
    if original:
        flags.append("原版")
    if playable:
        flags.append("可播")
    if vip:
        flags.append("VIP")
    flag_text = f" [{','.join(flags)}]" if flags else ""
    suffix = f" {extra}" if extra else ""
    return f"{head}{name} - {artist} (id={song_id}){flag_text}{suffix}"


def log_song_list(step: str, songs: list[Any], *, limit: int = 10) -> None:
    if not songs:
        log_step(step, count=0)
        return
    lines = [format_song_line(song, index=idx + 1) for idx, song in enumerate(songs[:limit])]
    log_step(step, count=len(songs), preview=" || ".join(lines))


def _format_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        if not value:
            return "[]"
        if all(isinstance(item, (str, int, float, bool)) for item in value):
            return repr(list(value))
        return f"<{len(value)} items>"
    text = str(value)
    return text if len(text) <= 500 else text[:497] + "..."
