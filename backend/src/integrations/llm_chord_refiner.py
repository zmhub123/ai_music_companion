"""音频粗和弦 + LRC → LLM 精修字级和弦（弹唱谱）。"""

from __future__ import annotations

import json
import re
from typing import Any

from pycore.core.logger import get_logger

from src.integrations.dashscope_client import DashScopeClient

logger = get_logger()

# 常见抒情歌 C 调走向（后来等）
_BALLAD_FALLBACK = ["C", "Em7", "Am", "Em7", "F", "G7", "Em7", "Am"]


def _norm_chars(lyric: str) -> list[int]:
    return [index for index, ch in enumerate(lyric) if ch.strip()]


_KNOWN_PROGRESSIONS: dict[str, list[str]] = {
    "后来": ["C", "Em7", "Am", "Em7", "F", "G7", "Em7", "Am"],
}


def _fallback_lines(
    lrc_lines: list[dict[str, Any]],
    *,
    song_name: str,
    instrument: str,
) -> list[dict[str, Any]]:
    """无 LLM 时的规则回落：按行均分常见走向。"""
    lines: list[dict[str, Any]] = []
    prog = list(_KNOWN_PROGRESSIONS.get(song_name.strip(), _BALLAD_FALLBACK))
    for line_index, lrc in enumerate(lrc_lines):
        lyric = str(lrc["lyric_line"])
        indices = _norm_chars(lyric)
        if not indices:
            continue
        slots = min(4, max(2, len(indices) // 3))
        marks: list[dict[str, Any]] = []
        for slot in range(slots):
            chord = prog[(line_index * slots + slot) % len(prog)]
            pos = indices[min(int(slot * len(indices) / slots), len(indices) - 1)]
            marks.append({"position": pos, "chord": chord})
        primary = marks[0]["chord"] if marks else "C"
        lines.append(
            {
                "lyric_line": lyric,
                "start_ms": int(lrc["start_ms"]),
                "chord_marks": marks,
                "chord": primary,
                "position": marks[0]["position"] if marks else 0,
                "section": "vocal",
            }
        )
    return lines


def _parse_llm_lines(raw: str, lrc_lines: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
    try:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(match.group(0) if match else raw)
        payload = data.get("lines") or []
        if not isinstance(payload, list) or not payload:
            return None
        parsed: list[dict[str, Any]] = []
        for index, item in enumerate(payload):
            if not isinstance(item, dict):
                continue
            lyric = str(item.get("lyric_line") or (lrc_lines[index]["lyric_line"] if index < len(lrc_lines) else ""))
            marks = item.get("chord_marks") or []
            normalized_marks: list[dict[str, Any]] = []
            if isinstance(marks, list):
                for mark in marks:
                    if not isinstance(mark, dict):
                        continue
                    normalized_marks.append(
                        {
                            "position": int(mark.get("position") or 0),
                            "chord": str(mark.get("chord") or "C"),
                        }
                    )
            if not normalized_marks:
                chord = str(item.get("chord") or "C")
                normalized_marks = [{"position": 0, "chord": chord}]
            parsed.append(
                {
                    "lyric_line": lyric,
                    "start_ms": int(lrc_lines[index]["start_ms"]) if index < len(lrc_lines) else 0,
                    "chord_marks": normalized_marks,
                    "chord": normalized_marks[0]["chord"],
                    "position": normalized_marks[0]["position"],
                    "section": "vocal",
                }
            )
        return parsed if parsed else None
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.warning("llm chord refine parse failed", error=str(exc))
        return None


async def refine_chords_with_llm(
    client: DashScopeClient,
    *,
    song_name: str,
    artist_name: str,
    instrument: str,
    lrc_lines: list[dict[str, Any]],
    coarse_timeline: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], str, int, str]:
    """返回 (lines, key, capo, rhythm_style)。"""
    if client.use_mock:
        return (
            _fallback_lines(lrc_lines, song_name=song_name, instrument=instrument),
            "C",
            0,
            "ballad",
        )

    sample_lyrics = "\n".join(
        f'{index + 1}. [{int(line["start_ms"])}ms] {line["lyric_line"]}'
        for index, line in enumerate(lrc_lines[:24])
    )
    coarse = ", ".join(
        f'{int(item["start_ms"])}ms:{item["chord"]}' for item in coarse_timeline[:24]
    )
    prompt = (
        f"你是专业弹唱谱编配师。歌曲《{song_name}》-{artist_name}，乐器={instrument}。\n"
        f"音频粗分析和弦时间轴：{coarse}\n"
        "请根据歌词行与音频走向，输出 JSON：\n"
        '{"key":"C","capo":0,"rhythm_style":"ballad","lines":[{"lyric_line":"...","chord_marks":[{"position":0,"chord":"C"}]}]}\n'
        "要求：\n"
        "1. lines 顺序与下列歌词一致，每行 2～4 个和弦，position 为字索引（从 0 起）；\n"
        "2. 和弦用常见弹唱和弦（C Am F G G7 Em Em7 Am7 Dm 等）；\n"
        "3. 只返回 JSON，不要解释。\n"
        f"歌词：\n{sample_lyrics}"
    )
    if len(lrc_lines) > 24:
        prompt += f"\n... 共 {len(lrc_lines)} 行，请输出全部行的 lines。"

    try:
        raw = await client.generate(prompt, temperature=0.15)
        parsed = _parse_llm_lines(raw, lrc_lines)
        if parsed:
            key = "C"
            capo = 0
            rhythm_style = "ballad"
            try:
                match = re.search(r"\{.*\}", raw, re.DOTALL)
                meta = json.loads(match.group(0) if match else raw)
                key = str(meta.get("key") or key)
                capo = int(meta.get("capo") or capo)
                rhythm_style = str(meta.get("rhythm_style") or rhythm_style)
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
            if len(parsed) < len(lrc_lines):
                tail = _fallback_lines(
                    lrc_lines[len(parsed) :],
                    song_name=song_name,
                    instrument=instrument,
                )
                parsed.extend(tail)
            return parsed[: len(lrc_lines)], key, capo, rhythm_style
    except Exception as exc:
        logger.warning("llm chord refine failed", error=str(exc))

    return (
        _fallback_lines(lrc_lines, song_name=song_name, instrument=instrument),
        "C",
        0,
        "ballad",
    )
