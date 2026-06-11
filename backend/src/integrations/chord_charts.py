"""弹唱和弦谱表：按人声版本 + 乐器维护，供与 LRC 字级对齐。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ScoreLine = dict[str, Any]

# 升 5 度（男声 C 调 → 女声 G 调常用移调）
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
class VocalChart:
    vocal_version: str
    key: str
    capo: int
    intro_rows: list[tuple[str, str, str]]
    vocal_rows: list[tuple[str, str, str, int]]  # guitar, ukulele, lyric, position


def transpose_chord_name(chord: str, semitones: int = 5) -> str:
    if semitones == 0:
        return chord
    if semitones == 5:
        parts = chord.split()
        return " ".join(_CHORD_UP_5.get(p, p) for p in parts)
    return chord


def _transpose_rows(
    rows: list[tuple[str, str, str, int]], semitones: int
) -> list[tuple[str, str, str, int]]:
    return [
        (transpose_chord_name(g, semitones), transpose_chord_name(u, semitones), lyric, pos)
        for g, u, lyric, pos in rows
    ]


def _yiban_vocal_rows_male() -> list[tuple[str, str, str, int]]:
    """Top Barry 男声版（C 调 + 变调夹 2 品），position 为和弦落字索引。"""
    return [
        ("Cmaj7", "C", "无力感在把眼泪一点一点吞噬", 0),
        ("E7", "E7", "空旷的街道早没了一点声", 0),
        ("Am7", "Am", "那天回到我们俩熟悉的城市", 0),
        ("Am7", "Am", "马路上关闭的灯有一半熟悉一半生", 0),
        ("F", "F", "酒精让我一半温热一半冷", 0),
        ("Em7", "Em", "可你扮演着成熟", 0),
        ("E7", "E7", "我一半没感觉一半疼", 0),
        ("Am7", "Am", "就最后变成一半猜忌 一半问", 0),
        ("Dm7", "Dm", "我可能是自己一半爱你 一半恨", 0),
        ("G", "G", "这离别是我灵感的秤砣", 0),
        ("E7", "E7", "我内心的痛是", 0),
        ("Am7", "Am", "不对等的沉默", 0),
        ("Am7", "Am", "思念是困住我俩的绳索", 0),
        ("F", "F", "就算血肉模糊", 0),
        ("Em7", "Em", "我也没办法挣脱", 0),
        ("F", "F", "完美的你终于接受放过剩下的我走", 0),
        ("Em7", "Em", "我接受这结果 你画的杰作", 0),
        ("Am7", "Am", "我找不到线索 像被牵着走", 0),
        ("G", "G", "但是我不想要一半一半 一半一半", 0),
        ("C", "C", "可是我们这一段一段 已断已断", 0),
        ("Em7", "Em", "街上的路灯一盏一盏 一闪一闪", 0),
        ("Am7", "Am", "眼泪滴在路上 一瓣一瓣 一瓣一瓣", 0),
        ("F", "F", "可是我不想要一半一半 一半一半", 0),
        ("Em7", "Em", "我深陷在一边喜欢 一边离开", 0),
        ("Dm7", "Dm", "他们问我丢掉了太多遗不遗憾", 0),
        ("G", "G", "一半一半", 0),
    ]


_YIBAN_INTRO = [
    ("Cmaj7", "C", "（前奏）"),
    ("G", "G", "· · · ·"),
    ("Am7", "Am", "· · · ·"),
    ("F", "F", "· · Fm ·"),
]

_VOCAL_CHARTS: dict[int, dict[str, VocalChart]] = {
    3333988321: {
        "male": VocalChart(
            vocal_version="male",
            key="C",
            capo=2,
            intro_rows=_YIBAN_INTRO,
            vocal_rows=_yiban_vocal_rows_male(),
        ),
        "female": VocalChart(
            vocal_version="female",
            key="G",
            capo=0,
            intro_rows=[
                (transpose_chord_name(g, 5), transpose_chord_name(u, 5), lyric)
                for g, u, lyric in _YIBAN_INTRO
            ],
            vocal_rows=_transpose_rows(_yiban_vocal_rows_male(), 5),
        ),
    }
}


def get_vocal_chart(song_id: int, vocal_version: str) -> VocalChart | None:
    charts = _VOCAL_CHARTS.get(song_id)
    if not charts:
        return None
    return charts.get(vocal_version) or charts.get("male")


def chart_to_score_lines(chart: VocalChart, instrument: str) -> list[ScoreLine]:
    lines: list[ScoreLine] = []
    for g, u, lyric in chart.intro_rows:
        chord = g if instrument == "guitar" else u
        lines.append(
            {
                "position": 0,
                "chord": chord,
                "lyric_line": lyric,
                "section": "intro",
            }
        )
    for g, u, lyric, position in chart.vocal_rows:
        chord = g if instrument == "guitar" else u
        lines.append(
            {
                "position": position,
                "chord": chord,
                "lyric_line": lyric,
                "section": "vocal",
            }
        )
    return lines
