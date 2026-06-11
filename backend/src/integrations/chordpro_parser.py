"""ChordPro 解析：元数据指令、段落标记、行首/行内和弦。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

ScoreLine = dict[str, Any]

_DIRECTIVE = re.compile(r"^\{([^:}]+)(?::([^}]*))?\}\s*$")
_CHORD_TOKEN = re.compile(r"\[([^\[\]]+)\]")


@dataclass
class ParsedChordPro:
    title: str = ""
    artist: str = ""
    key: str = "C"
    capo: int = 0
    source: str = "verified"
    ug_tab_id: int | None = None
    rhythm_style: str = "default"
    intro_duration_ms: int = 0
    guitar_lines: list[ScoreLine] = field(default_factory=list)
    ukulele_lines: list[ScoreLine] = field(default_factory=list)


def _split_dual_chord(raw: str) -> tuple[str, str]:
    if "|" in raw:
        guitar, ukulele = raw.split("|", 1)
        return guitar.strip(), ukulele.strip()
    chord = raw.strip()
    return chord, chord


def _parse_content_line(line: str, *, section: str) -> tuple[ScoreLine, ScoreLine] | None:
    stripped = line.strip()
    if not stripped:
        return None

    lyric_parts: list[str] = []
    guitar_chord = ""
    ukulele_chord = ""
    position = 0
    found = False

    cursor = 0
    for match in _CHORD_TOKEN.finditer(stripped):
        lyric_parts.append(stripped[cursor : match.start()])
        if not found:
            position = len("".join(lyric_parts))
            found = True
        guitar_part, ukulele_part = _split_dual_chord(match.group(1))
        if not guitar_chord:
            guitar_chord = guitar_part
            ukulele_chord = ukulele_part
        cursor = match.end()
    lyric_parts.append(stripped[cursor:])
    lyric_line = "".join(lyric_parts).strip()
    if not lyric_line and not guitar_chord:
        return None

    base = {
        "position": position,
        "lyric_line": lyric_line,
        "section": section,
    }
    guitar_line: ScoreLine = {**base, "chord": guitar_chord}
    ukulele_line: ScoreLine = {**base, "chord": ukulele_chord or guitar_chord}
    return guitar_line, ukulele_line


def parse_chordpro(text: str) -> ParsedChordPro:
    chart = ParsedChordPro()
    section = "vocal"

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue

        directive = _DIRECTIVE.match(line.strip())
        if directive:
            name = directive.group(1).strip().lower()
            value = (directive.group(2) or "").strip()
            if name in {"title", "t"}:
                chart.title = value
            elif name in {"artist", "subtitle"}:
                chart.artist = value
            elif name == "key":
                chart.key = value or chart.key
            elif name == "capo":
                chart.capo = int(value or 0)
            elif name == "source":
                chart.source = value or chart.source
            elif name == "ug_tab_id":
                chart.ug_tab_id = int(value) if value else None
            elif name == "rhythm_style":
                chart.rhythm_style = value or chart.rhythm_style
            elif name == "intro_duration_ms":
                chart.intro_duration_ms = int(value or 0)
            elif name == "start_of_intro":
                section = "intro"
            elif name == "end_of_intro":
                section = "vocal"
            elif name.startswith("start_of_"):
                section = "vocal"
            elif name.startswith("end_of_"):
                section = "vocal"
            elif name == "comment":
                continue
            continue

        parsed = _parse_content_line(line, section=section)
        if parsed is None:
            continue
        guitar_line, ukulele_line = parsed
        chart.guitar_lines.append(guitar_line)
        chart.ukulele_lines.append(ukulele_line)

    return chart


def chart_to_score_lines(chart: ParsedChordPro, instrument: str) -> list[ScoreLine]:
    if instrument == "ukulele":
        return list(chart.ukulele_lines)
    return list(chart.guitar_lines)
