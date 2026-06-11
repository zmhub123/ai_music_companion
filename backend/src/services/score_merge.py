"""和弦谱与网易云 LRC 歌词合并（字级对齐）。"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

ScoreLine = dict[str, Any]


def _norm_lyric(text: str) -> str:
    cleaned = re.sub(r"\s+", "", text.strip())
    return cleaned.replace("一般", "一半")


def _norm_index_map(raw: str) -> list[int]:
    return [index for index, ch in enumerate(raw) if not ch.isspace()]


def _render_intro_lines(
    intro_lines: list[ScoreLine],
    first_vocal_ms: int,
    skill_level: str,
    simplify_chord,
) -> list[ScoreLine]:
    if not intro_lines:
        return []
    step = first_vocal_ms / len(intro_lines) if first_vocal_ms > 0 else 4000
    rendered: list[ScoreLine] = []
    for index, line in enumerate(intro_lines):
        chord = simplify_chord(str(line.get("chord") or ""), skill_level)
        rendered.append(
            {
                "position": int(line.get("position") or 0),
                "chord": chord,
                "lyric_line": str(line.get("lyric_line") or ""),
                "section": "intro",
                "start_ms": int(index * step),
                "chord_marks": [{"position": int(line.get("position") or 0), "chord": chord}],
            }
        )
    return rendered


def _build_seed_chord_stream(vocal_chords: list[ScoreLine], simplify_chord, skill_level: str):
    """种子谱：每个归一化字符对应一个和弦（行首换和弦）。"""
    chars: list[str] = []
    chords: list[str | None] = []
    for line in vocal_chords:
        raw = str(line.get("lyric_line") or "")
        chord = simplify_chord(str(line.get("chord") or ""), skill_level)
        position = int(line.get("position") or 0)
        norm = _norm_lyric(raw)
        for index, _ch in enumerate(norm):
            chars.append(_ch)
            if index == position:
                chords.append(chord or None)
            else:
                chords.append(None)
    return "".join(chars), chords


def _assign_chords_char_level(
    vocal_chords: list[ScoreLine],
    lrc_lines: list[ScoreLine],
    *,
    skill_level: str,
    simplify_chord,
) -> list[ScoreLine]:
    seed_str, seed_chords = _build_seed_chord_stream(vocal_chords, simplify_chord, skill_level)

    lrc_entries: list[tuple[int, int, str]] = []
    for line_index, lrc in enumerate(lrc_lines):
        raw = str(lrc["lyric_line"])
        for char_index, ch in enumerate(raw):
            if ch.isspace():
                continue
            lrc_entries.append((line_index, char_index, ch))

    lrc_str = "".join(item[2] for item in lrc_entries)
    if not lrc_str:
        return []

    matcher = SequenceMatcher(None, seed_str, lrc_str)
    lrc_chord_at: list[str | None] = [None] * len(lrc_entries)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag not in {"equal", "replace"}:
            continue
        for seed_i, lrc_j in zip(range(i1, i2), range(j1, j2), strict=False):
            if seed_i >= len(seed_chords):
                continue
            chord = seed_chords[seed_i]
            if chord:
                lrc_chord_at[lrc_j] = chord

    # 前向填充：行内延续上一个和弦，便于弹唱
    last: str | None = None
    for index, chord in enumerate(lrc_chord_at):
        if chord:
            last = chord
        elif last:
            lrc_chord_at[index] = last

    merged: list[ScoreLine] = []
    for line_index, lrc in enumerate(lrc_lines):
        raw = str(lrc["lyric_line"])
        norm_map = _norm_index_map(raw)
        marks: list[dict[str, Any]] = []
        prev: str | None = None
        for norm_i, raw_i in enumerate(norm_map):
            entry_index = next(
                (idx for idx, ent in enumerate(lrc_entries) if ent[0] == line_index and ent[1] == raw_i),
                None,
            )
            if entry_index is None:
                continue
            chord = lrc_chord_at[entry_index]
            if chord and chord != prev:
                marks.append({"position": raw_i, "chord": chord})
                prev = chord

        primary = marks[0]["chord"] if marks else ""
        primary_pos = marks[0]["position"] if marks else 0
        merged.append(
            {
                "position": primary_pos,
                "chord": primary,
                "lyric_line": raw,
                "section": "vocal",
                "start_ms": int(lrc["start_ms"]),
                "chord_marks": marks,
            }
        )
    return merged


def merge_chords_with_lrc(
    chord_lines: list[ScoreLine],
    lrc_lines: list[ScoreLine],
    *,
    skill_level: str,
    simplify_chord,
) -> list[ScoreLine]:
    if not lrc_lines:
        return []

    intro_lines = [line for line in chord_lines if line.get("section") == "intro"]
    vocal_chords = [line for line in chord_lines if line.get("section") != "intro"]
    first_vocal_ms = int(lrc_lines[0]["start_ms"])

    merged = _render_intro_lines(intro_lines, first_vocal_ms, skill_level, simplify_chord)
    merged.extend(
        _assign_chords_char_level(
            vocal_chords,
            lrc_lines,
            skill_level=skill_level,
            simplify_chord=simplify_chord,
        )
    )
    return merged
