"""弹唱节奏型模板（按乐器）。"""

from __future__ import annotations

from typing import Any

RhythmPattern = dict[str, Any]

BALLAD_4_4: dict[str, RhythmPattern] = {
    "guitar": {
        "label": "节奏型 · 4/4 慢板分解",
        "names": ["e", "B", "G", "D", "A", "E"],
        "rows": [
            ["×", "", "", "", "", ""],
            ["", "", "", "×", "", ""],
            ["", "", "×", "", "×", ""],
            ["", "×", "", "", "", "×"],
            ["", "", "", "", "", ""],
            ["", "", "", "", "", ""],
        ],
        "beats": ["↓", "", "↑", "↓", "", "↑"],
    },
    "ukulele": {
        "label": "节奏型 · 4/4 慢板扫弦",
        "names": ["A", "E", "C", "G"],
        "rows": [
            ["", "", "", ""],
            ["", "×", "", ""],
            ["×", "", "×", ""],
            ["", "", "×", ""],
        ],
        "beats": ["↓", "—", "↑", "↓"],
    },
}

DEFAULT_RHYTHM: dict[str, RhythmPattern] = {
    "guitar": {
        "label": "节奏型 · 4/4 基础扫弦",
        "names": ["e", "B", "G", "D", "A", "E"],
        "rows": [
            ["", "", "×", "", "", ""],
            ["", "×", "", "×", "", ""],
            ["", "", "×", "", "×", ""],
            ["", "", "", "×", "", ""],
            ["×", "", "", "", "", ""],
            ["", "", "", "", "", ""],
        ],
        "beats": ["↓", "", "↑↓", "", "↑", ""],
    },
    "ukulele": {
        "label": "节奏型 · 4/4 基础扫弦",
        "names": ["A", "E", "C", "G"],
        "rows": [
            ["", "", "", "×"],
            ["", "×", "", ""],
            ["×", "", "×", ""],
            ["", "", "×", ""],
        ],
        "beats": ["↓", "", "↑", "↓"],
    },
}


def pick_rhythm(instrument: str, style: str = "default") -> RhythmPattern:
    bank = BALLAD_4_4 if style == "ballad" else DEFAULT_RHYTHM
    return dict(bank.get(instrument, bank["guitar"]))
