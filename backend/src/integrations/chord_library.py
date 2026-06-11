"""ChordPro 谱库：文件种子 + DB 查询，支持人声版本移调。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.integrations.chordpro_parser import ParsedChordPro, chart_to_score_lines, parse_chordpro
from src.integrations.music_provider import LEGACY_SONG_ID_ALIASES

ScoreLine = dict[str, Any]

BACKEND_DIR = Path(__file__).resolve().parents[2]
CHORDPRO_DIR = BACKEND_DIR / "data" / "chordpro"

_CHORD_UP_5: dict[str, str] = {
    "C": "G",
    "Cmaj7": "Gmaj7",
    "D": "A",
    "Dm": "Am",
    "Dm7": "Am7",
    "E": "B",
    "E7": "B7",
    "Em": "Bm",
    "Em7": "Bm7",
    "F": "C",
    "Fm": "Cm",
    "G": "D",
    "Gsus4": "Dsus4",
    "Am": "Em",
    "Am7": "Em7",
    "A": "E",
    "B": "F#",
    "Bm": "F#m",
}


@dataclass(frozen=True)
class LibraryChart:
    netease_song_id: int
    vocal_version: str
    song_name: str
    artist_name: str
    key: str
    capo: int
    source: str
    rhythm_style: str
    intro_duration_ms: int
    parsed: ParsedChordPro
    ug_tab_id: int | None = None


def transpose_chord_name(chord: str, semitones: int = 5) -> str:
    if semitones == 0 or not chord:
        return chord
    if semitones == 5:
        parts = chord.split()
        return " ".join(_CHORD_UP_5.get(part, part) for part in parts)
    return chord


def _transpose_parsed(chart: ParsedChordPro, semitones: int) -> ParsedChordPro:
    if semitones == 0:
        return chart

    def _shift_lines(lines: list[ScoreLine]) -> list[ScoreLine]:
        shifted: list[ScoreLine] = []
        for line in lines:
            shifted.append(
                {
                    **line,
                    "chord": transpose_chord_name(str(line.get("chord") or ""), semitones),
                }
            )
        return shifted

    return ParsedChordPro(
        title=chart.title,
        artist=chart.artist,
        key=transpose_chord_name(chart.key, semitones) if chart.key else chart.key,
        capo=chart.capo,
        source=chart.source,
        ug_tab_id=chart.ug_tab_id,
        rhythm_style=chart.rhythm_style,
        intro_duration_ms=chart.intro_duration_ms,
        guitar_lines=_shift_lines(chart.guitar_lines),
        ukulele_lines=_shift_lines(chart.ukulele_lines),
    )


def _resolve_song_id(song_id: int) -> int:
    return LEGACY_SONG_ID_ALIASES.get(song_id, song_id)


def _chart_from_file(path: Path, *, vocal_version: str) -> LibraryChart | None:
    if not path.is_file():
        return None

    parsed = parse_chordpro(path.read_text(encoding="utf-8"))
    song_id = int(path.stem.split("_")[0])
    semitones = 5 if vocal_version == "female" else 0
    if vocal_version == "female":
        parsed = _transpose_parsed(parsed, semitones)

    return LibraryChart(
        netease_song_id=song_id,
        vocal_version=vocal_version,
        song_name=parsed.title,
        artist_name=parsed.artist,
        key=parsed.key,
        capo=0 if vocal_version == "female" else parsed.capo,
        source=parsed.source,
        rhythm_style=parsed.rhythm_style,
        intro_duration_ms=parsed.intro_duration_ms,
        parsed=parsed,
        ug_tab_id=parsed.ug_tab_id,
    )


def list_chordpro_seed_files() -> list[Path]:
    if not CHORDPRO_DIR.is_dir():
        return []
    return sorted(CHORDPRO_DIR.glob("*.chordpro"))


def load_chart_from_file(song_id: int, vocal_version: str) -> LibraryChart | None:
    resolved = _resolve_song_id(song_id)
    for candidate_id in (song_id, resolved):
        path = CHORDPRO_DIR / f"{candidate_id}_{vocal_version}.chordpro"
        chart = _chart_from_file(path, vocal_version=vocal_version)
        if chart is not None:
            if candidate_id != song_id:
                return LibraryChart(
                    netease_song_id=song_id,
                    vocal_version=chart.vocal_version,
                    song_name=chart.song_name,
                    artist_name=chart.artist_name,
                    key=chart.key,
                    capo=chart.capo,
                    source=chart.source,
                    rhythm_style=chart.rhythm_style,
                    intro_duration_ms=chart.intro_duration_ms,
                    parsed=chart.parsed,
                    ug_tab_id=chart.ug_tab_id,
                )
            return chart

    male_path = CHORDPRO_DIR / f"{resolved}_male.chordpro"
    if vocal_version == "female" and male_path.is_file():
        return _chart_from_file(male_path, vocal_version="female")
    if vocal_version == "male":
        return _chart_from_file(male_path, vocal_version="male")
    return None


async def get_library_chart(
    db: AsyncSession | None,
    song_id: int,
    vocal_version: str,
) -> LibraryChart | None:
    from src.db.models import ChordChart

    resolved = _resolve_song_id(song_id)
    if db is not None:
        result = await db.execute(
            select(ChordChart).where(
                ChordChart.netease_song_id.in_([song_id, resolved]),
                ChordChart.vocal_version == vocal_version,
            )
        )
        row = result.scalar_one_or_none()
        if row is None and vocal_version == "female":
            male_result = await db.execute(
                select(ChordChart).where(
                    ChordChart.netease_song_id.in_([song_id, resolved]),
                    ChordChart.vocal_version == "male",
                )
            )
            row = male_result.scalar_one_or_none()
            if row is not None:
                parsed = _transpose_parsed(parse_chordpro(row.chordpro_text), 5)
                return LibraryChart(
                    netease_song_id=song_id,
                    vocal_version="female",
                    song_name=row.song_name,
                    artist_name=row.artist_name,
                    key=transpose_chord_name(row.key, 5),
                    capo=0,
                    source=row.source,
                    rhythm_style=row.rhythm_style,
                    intro_duration_ms=row.intro_duration_ms,
                    parsed=parsed,
                    ug_tab_id=row.ug_tab_id,
                )
        if row is not None:
            parsed = parse_chordpro(row.chordpro_text)
            if row.vocal_version == vocal_version:
                return LibraryChart(
                    netease_song_id=song_id,
                    vocal_version=vocal_version,
                    song_name=row.song_name,
                    artist_name=row.artist_name,
                    key=row.key,
                    capo=row.capo,
                    source=row.source,
                    rhythm_style=row.rhythm_style,
                    intro_duration_ms=row.intro_duration_ms,
                    parsed=parsed,
                    ug_tab_id=row.ug_tab_id,
                )

    return load_chart_from_file(song_id, vocal_version)


def library_chart_to_lines(chart: LibraryChart, instrument: str) -> list[ScoreLine]:
    return chart_to_score_lines(chart.parsed, instrument)
