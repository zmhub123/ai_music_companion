"""网易云歌词（LRC）拉取与解析。"""

from __future__ import annotations

import asyncio
import importlib
import re
from typing import Any

from pycore.core.logger import get_logger

from src.integrations.music_provider import _pyncm_available, _ensure_pyncm_session

logger = get_logger()

LRC_LINE_RE = re.compile(r"^\[(\d+):(\d+)(?:\.(\d+))?\](.*)$")


def _lrc_timestamp_to_ms(minute: str, second: str, fraction: str | None) -> int:
    mm = int(minute)
    ss = int(second)
    if fraction:
        frac = fraction.ljust(3, "0")[:3]
        sub_ms = int(int(frac) * (1000 / (10 ** len(frac))))
    else:
        sub_ms = 0
    return mm * 60_000 + ss * 1000 + sub_ms


def parse_lrc_text(lrc_text: str) -> list[dict[str, Any]]:
    """解析标准 LRC 行，忽略网易云 JSON 元数据行。"""
    parsed: list[dict[str, Any]] = []
    seen: set[tuple[int, str]] = set()

    for raw in lrc_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("{"):
            continue
        match = LRC_LINE_RE.match(line)
        if not match:
            continue
        minute, second, fraction, lyric = match.groups()
        text = lyric.strip()
        if not text:
            continue
        start_ms = _lrc_timestamp_to_ms(minute, second, fraction)
        key = (start_ms, text)
        if key in seen:
            continue
        seen.add(key)
        parsed.append({"start_ms": start_ms, "lyric_line": text, "section": "vocal"})

    parsed.sort(key=lambda item: item["start_ms"])
    return parsed


def _fetch_lrc_sync(song_id: int) -> list[dict[str, Any]]:
    if not _pyncm_available():
        return []
    try:
        _ensure_pyncm_session()
        apis = importlib.import_module("pyncm.apis")
        result = apis.track.GetTrackLyricsNew(song_id)
        if not isinstance(result, dict):
            return []
        lrc_block = result.get("lrc")
        if not isinstance(lrc_block, dict):
            return []
        lrc_text = str(lrc_block.get("lyric") or "")
        if not lrc_text:
            return []
        lines = parse_lrc_text(lrc_text)
        logger.info("netease lrc loaded", song_id=song_id, lines=len(lines))
        return lines
    except Exception as exc:
        logger.warning("netease lrc fetch failed", song_id=song_id, error=str(exc))
        return []


async def get_netease_lrc_lines(song_id: int) -> list[dict[str, Any]]:
    return await asyncio.to_thread(_fetch_lrc_sync, song_id)
