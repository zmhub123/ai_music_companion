"""音频和弦时间轴 + 网易云 LRC + LLM 精修 → 完整弹唱谱。"""

from __future__ import annotations

from typing import Any

from src.integrations.llm_chord_refiner import refine_chords_with_llm
from src.integrations.rhythm_patterns import pick_rhythm
from src.integrations.chord_provider import ChordSource
from src.services.score_service import (
    BEGINNER_CHORD_MAP,
    DEFAULT_PRACTICE_TIPS,
    _generate_practice_tips,
    _normalize_skill_level,
    _normalize_vocal_version,
)

SCORE_AUDIO_VERSION = 9

GUITAR_TO_UKE: dict[str, str] = {
    "C": "C",
    "Cm": "Cm",
    "Cmaj7": "C",
    "D": "D",
    "Dm": "Dm",
    "Dm7": "Dm",
    "E": "E",
    "Em": "Em",
    "Em7": "Em",
    "F": "F",
    "Fm": "Fm",
    "G": "G",
    "G7": "G7",
    "Am": "Am",
    "Am7": "Am7",
    "A": "A",
    "B": "B",
    "Bm": "Bm",
}


def _simplify_chord(chord: str, skill_level: str) -> str:
    if skill_level != "beginner":
        return chord
    parts = chord.split()
    return " ".join(BEGINNER_CHORD_MAP.get(part, part) for part in parts)


def _to_instrument_chord(chord: str, instrument: str) -> str:
    if instrument != "ukulele":
        return chord
    parts = chord.split()
    return " ".join(GUITAR_TO_UKE.get(part, part) for part in parts)


def _apply_skill_and_instrument(
    lines: list[dict[str, Any]],
    *,
    instrument: str,
    skill_level: str,
) -> list[dict[str, Any]]:
    rendered: list[dict[str, Any]] = []
    for line in lines:
        marks = line.get("chord_marks") or []
        new_marks: list[dict[str, Any]] = []
        for mark in marks:
            chord = _to_instrument_chord(
                _simplify_chord(str(mark.get("chord") or "C"), skill_level),
                instrument,
            )
            new_marks.append({"position": int(mark.get("position") or 0), "chord": chord})
        primary = new_marks[0]["chord"] if new_marks else "C"
        rendered.append(
            {
                **line,
                "chord": primary,
                "position": new_marks[0]["position"] if new_marks else 0,
                "chord_marks": new_marks,
            }
        )
    return rendered


async def build_score_from_audio(
    *,
    llm,
    song_id: int,
    song_name: str,
    artist_name: str,
    cover_url: str,
    duration_ms: int | None,
    instrument: str,
    vocal_version: str,
    skill_level: str,
    chord_timeline: list[dict[str, Any]],
    lrc_lines: list[dict[str, Any]],
) -> dict[str, Any]:
    skill = _normalize_skill_level(skill_level)
    vocal = _normalize_vocal_version(vocal_version)

    refined_lines, key, capo, rhythm_style = await refine_chords_with_llm(
        llm,
        song_name=song_name,
        artist_name=artist_name,
        instrument=instrument,
        lrc_lines=lrc_lines,
        coarse_timeline=chord_timeline,
    )
    refined_lines = _apply_skill_and_instrument(
        refined_lines, instrument=instrument, skill_level=skill
    )

    lines: list[dict[str, Any]] = []
    intro_ms = int(lrc_lines[0]["start_ms"]) if lrc_lines else 0
    if intro_ms > 3000 and refined_lines:
        intro_chord = refined_lines[0]["chord"]
        lines.append(
            {
                "position": 0,
                "chord": intro_chord,
                "lyric_line": "（前奏）",
                "section": "intro",
                "start_ms": 0,
                "chord_marks": [{"position": 0, "chord": intro_chord}],
            }
        )
    lines.extend(refined_lines)

    if vocal == "female" and capo == 0:
        capo = 3

    practice_source = ChordSource(
        netease_song_id=song_id,
        song_name=song_name,
        artist_name=artist_name,
        cover_url=cover_url,
        key=key,
        capo=capo,
        guitar_lines=lines,
        ukulele_lines=lines,
        origin="audio_analysis",
        rhythm_style=rhythm_style,
    )
    practice_tips = await _generate_practice_tips(llm, practice_source, instrument, skill, lines)

    return {
        "_version": SCORE_AUDIO_VERSION,
        "netease_song_id": song_id,
        "song_name": song_name,
        "artist_name": artist_name,
        "cover_url": cover_url,
        "instrument": instrument,
        "skill_level": skill,
        "vocal_version": vocal,
        "key": key,
        "capo": capo,
        "lines": lines,
        "practice_tips": practice_tips,
        "rhythm_pattern": pick_rhythm(instrument, rhythm_style),
        "intro_duration_ms": intro_ms,
        "duration_ms": duration_ms,
        "lyric_source": "netease",
        "chord_source": "audio_analysis+llm",
    }
