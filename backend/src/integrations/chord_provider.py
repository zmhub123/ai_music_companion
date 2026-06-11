"""和弦谱 Mock 数据源（CHORD_PROVIDER=mock），未知曲目可 LLM/模板生成。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from pycore.core.logger import get_logger

from src.integrations.dashscope_client import DashScopeClient, get_dashscope_client
from src.integrations.music_provider import LEGACY_SONG_ID_ALIASES, SongDetail, get_song_detail

logger = get_logger()

ScoreLine = dict[str, Any]


@dataclass
class ChordSource:
    netease_song_id: int
    song_name: str
    artist_name: str
    cover_url: str
    key: str
    capo: int
    guitar_lines: list[ScoreLine]
    ukulele_lines: list[ScoreLine]
    origin: str = "seed"
    rhythm_style: str = "default"
    intro_duration_ms: int = 0


def _score_line(
    position: int,
    chord: str,
    lyric: str,
    *,
    section: str = "vocal",
    start_ms: int | None = None,
) -> ScoreLine:
    line: ScoreLine = {
        "position": position,
        "chord": chord,
        "lyric_line": lyric,
        "section": section,
    }
    if start_ms is not None:
        line["start_ms"] = start_ms
    return line


def _build_dual_lines(
    rows: list[tuple[str, str, str]],
    *,
    section: str = "vocal",
) -> tuple[list[ScoreLine], list[ScoreLine]]:
    guitar = [_score_line(0, g, lyric, section=section) for g, _, lyric in rows]
    ukulele = [_score_line(0, u, lyric, section=section) for _, u, lyric in rows]
    return guitar, ukulele


_YIBAN_INTRO_ROWS: list[tuple[str, str, str]] = [
    ("Cmaj7", "C", "（前奏）"),
    ("G", "G", "· · · ·"),
    ("Am7", "Am", "· · · ·"),
    ("F", "F", "· · Fm ·"),
]


_YIBAN_YIBAN_ROWS: list[tuple[str, str, str]] = [
    ("Cmaj7", "C", "无力感在把眼泪一点一点吞噬"),
    ("E7", "E7", "空旷的街道早没了一点声"),
    ("Am7", "Am", "那天回到我们俩熟悉的城市"),
    ("Am7", "Am", "马路上关闭的灯有一半熟悉一半生"),
    ("F", "F", "酒精让我一半温热一半冷"),
    ("Em7", "Em", "可你扮演着成熟 我一半没感觉一半疼"),
    ("Am7", "Am", "就最后变成一半猜忌一半问"),
    ("Dm7", "Dm", "我可能是自己一半爱你一半恨"),
    ("G", "G", "但是我不想要一半一半 一半一半"),
    ("C", "C", "可是我们这一段一段 已断已断"),
    ("Em7", "Em", "街上的路灯一盏一盏 一闪一闪"),
    ("Am7", "Am", "眼泪滴在路上 一瓣一瓣 一瓣一瓣"),
    ("F", "F", "可是我不想要一半一半 一半一半"),
    ("Em7", "Em", "我深陷在一边喜欢 一边离开"),
    ("Dm7", "Dm", "他们问我丢掉了太多遗不遗憾"),
    ("G", "G", "一半一半"),
    ("Cmaj7", "C", "这离别是我灵感的秤砣"),
    ("E7", "E7", "我内心的痛是不对等的沉默"),
    ("Am7", "Am", "思念是困住我俩的绳索"),
    ("Am7", "Am", "就算血肉模糊我也没办法挣脱"),
    ("F", "F", "完美的你终于接受放过剩下的我走"),
    ("Em7", "Em", "我接受这结果 你画的杰作"),
    ("Am7", "Am", "我找不到线索 像被牵着走"),
    ("Dm7", "Dm", "就最后变成一半猜忌一半问"),
    ("G", "G", "但是我不想要一半一半 一半一半"),
    ("C", "C", "可是我们这一段一段 已断已断"),
    ("Em7", "Em", "街上的路灯一盏一盏 一闪一闪"),
    ("Am7", "Am", "眼泪滴在路上 一瓣一瓣"),
    ("F", "F", "可是我不想要一半一半"),
    ("Em7", "Em", "我深陷在一边喜欢 一边离开"),
    ("Dm7", "Dm", "他们问我丢掉了太多遗不遗憾"),
    ("G", "G", "一半一半"),
]

_YIBAN_INTRO_GUITAR, _YIBAN_INTRO_UKULELE = _build_dual_lines(_YIBAN_INTRO_ROWS, section="intro")
_YIBAN_VOCAL_GUITAR, _YIBAN_VOCAL_UKULELE = _build_dual_lines(_YIBAN_YIBAN_ROWS)
_YIBAN_GUITAR = _YIBAN_INTRO_GUITAR + _YIBAN_VOCAL_GUITAR
_YIBAN_UKULELE = _YIBAN_INTRO_UKULELE + _YIBAN_VOCAL_UKULELE


def _resolve_score_song_id(song_id: int) -> int:
    return LEGACY_SONG_ID_ALIASES.get(song_id, song_id)


_MOCK_SOURCES: dict[int, ChordSource] = {
    186016: ChordSource(
        netease_song_id=186016,
        song_name="晴天",
        artist_name="周杰伦",
        cover_url="https://p1.music.126.net/example.jpg",
        key="G",
        capo=0,
        guitar_lines=[
            {"position": 0, "chord": "Em", "lyric_line": "故事的小黄花"},
            {"position": 8, "chord": "C", "lyric_line": "从出生那年就飘着"},
            {"position": 16, "chord": "G", "lyric_line": "童年的荡秋千"},
            {"position": 24, "chord": "D", "lyric_line": "随记忆一直晃到现在"},
        ],
        ukulele_lines=[
            {"position": 0, "chord": "Em", "lyric_line": "故事的小黄花"},
            {"position": 8, "chord": "C", "lyric_line": "从出生那年就飘着"},
            {"position": 16, "chord": "G", "lyric_line": "童年的荡秋千"},
            {"position": 24, "chord": "D", "lyric_line": "随记忆一直晃到现在"},
        ],
    ),
    29715551: ChordSource(
        netease_song_id=29715551,
        song_name="南山南",
        artist_name="马頔",
        cover_url="https://p1.music.126.net/example2.jpg",
        key="G",
        capo=0,
        guitar_lines=[
            {"position": 0, "chord": "G", "lyric_line": "你在南方的艳阳里"},
            {"position": 8, "chord": "Em", "lyric_line": "大雪纷飞"},
            {"position": 12, "chord": "C", "lyric_line": "你会不会"},
            {"position": 16, "chord": "D", "lyric_line": "带着秋凉去"},
        ],
        ukulele_lines=[
            {"position": 0, "chord": "G", "lyric_line": "你在南方的艳阳里"},
            {"position": 8, "chord": "Em", "lyric_line": "大雪纷飞"},
            {"position": 12, "chord": "C", "lyric_line": "你会不会"},
            {"position": 16, "chord": "D", "lyric_line": "带着秋凉去"},
        ],
    ),
    478507889: ChordSource(
        netease_song_id=478507889,
        song_name="卡农（经典钢琴版）",
        artist_name="dylanf",
        cover_url="",
        key="C",
        capo=0,
        guitar_lines=[
            {"position": 0, "chord": "C", "lyric_line": "（纯音乐，无歌词）"},
            {"position": 4, "chord": "G", "lyric_line": "主旋律段"},
            {"position": 8, "chord": "Am", "lyric_line": "副旋律段"},
            {"position": 12, "chord": "F", "lyric_line": "回归主题"},
        ],
        ukulele_lines=[
            {"position": 0, "chord": "C", "lyric_line": "（纯音乐，无歌词）"},
            {"position": 4, "chord": "G", "lyric_line": "主旋律段"},
            {"position": 8, "chord": "Am", "lyric_line": "副旋律段"},
            {"position": 12, "chord": "C", "lyric_line": "回归主题"},
        ],
    ),
    3333988321: ChordSource(
        netease_song_id=3333988321,
        song_name="一半一半",
        artist_name="Top Barry",
        cover_url="",
        key="C",
        capo=2,
        guitar_lines=_YIBAN_GUITAR,
        ukulele_lines=_YIBAN_UKULELE,
        rhythm_style="ballad",
        intro_duration_ms=14_400,
    ),
}

# 旧 ID 也指向同一谱面
for legacy_id, canonical_id in LEGACY_SONG_ID_ALIASES.items():
    if canonical_id in _MOCK_SOURCES and legacy_id not in _MOCK_SOURCES:
        src = _MOCK_SOURCES[canonical_id]
        _MOCK_SOURCES[legacy_id] = ChordSource(
            netease_song_id=legacy_id,
            song_name=src.song_name,
            artist_name=src.artist_name,
            cover_url=src.cover_url,
            key=src.key,
            capo=src.capo,
            guitar_lines=list(src.guitar_lines),
            ukulele_lines=list(src.ukulele_lines),
            rhythm_style=src.rhythm_style,
            intro_duration_ms=src.intro_duration_ms,
        )


def _normalize_title(name: str) -> str:
    text = name.strip()
    return re.sub(r"\s*[\(（].*?[\)）]\s*$", "", text).strip()


def _build_title_index() -> dict[str, ChordSource]:
    index: dict[str, ChordSource] = {}
    for source in _MOCK_SOURCES.values():
        title = _normalize_title(source.song_name)
        if title not in index:
            index[title] = source
    return index


_MOCK_BY_TITLE = _build_title_index()


def _template_chord_source(song_id: int, detail: SongDetail) -> ChordSource:
    progression = ["C", "G", "Am", "F"]
    labels = ["主歌 A", "主歌 B", "副歌", "桥段"]
    guitar_lines: list[ScoreLine] = []
    ukulele_lines: list[ScoreLine] = []
    for idx, label in enumerate(labels):
        chord = progression[idx % len(progression)]
        lyric = f"《{detail.song_name}》{label}（AI 模板谱，请对照原唱）"
        guitar_lines.append({"position": 0, "chord": chord, "lyric_line": lyric})
        ukulele_lines.append({"position": 0, "chord": chord, "lyric_line": lyric})
    return ChordSource(
        netease_song_id=song_id,
        song_name=detail.song_name,
        artist_name=detail.artist_name,
        cover_url=detail.cover_url or "",
        key="C",
        capo=0,
        guitar_lines=guitar_lines,
        ukulele_lines=ukulele_lines,
        origin="generated",
    )


def _parse_llm_chord_source(song_id: int, detail: SongDetail, raw: str) -> ChordSource | None:
    try:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(match.group(0) if match else raw)
        guitar_lines = data.get("guitar_lines") or data.get("lines") or []
        ukulele_lines = data.get("ukulele_lines") or guitar_lines
        if not isinstance(guitar_lines, list) or not guitar_lines:
            return None
        normalized_guitar: list[ScoreLine] = []
        for line in guitar_lines:
            if not isinstance(line, dict):
                continue
            normalized_guitar.append(
                {
                    "position": int(line.get("position") or 0),
                    "chord": str(line.get("chord") or "C"),
                    "lyric_line": str(line.get("lyric_line") or ""),
                }
            )
        if not normalized_guitar:
            return None
        normalized_ukulele: list[ScoreLine] = []
        for line in ukulele_lines:
            if not isinstance(line, dict):
                continue
            normalized_ukulele.append(
                {
                    "position": int(line.get("position") or 0),
                    "chord": str(line.get("chord") or "C"),
                    "lyric_line": str(line.get("lyric_line") or ""),
                }
            )
        return ChordSource(
            netease_song_id=song_id,
            song_name=detail.song_name,
            artist_name=detail.artist_name,
            cover_url=detail.cover_url or "",
            key=str(data.get("key") or "C"),
            capo=int(data.get("capo") or 0),
            guitar_lines=normalized_guitar,
            ukulele_lines=normalized_ukulele or list(normalized_guitar),
            origin="llm",
        )
    except (json.JSONDecodeError, AttributeError, TypeError, ValueError) as exc:
        logger.warning("llm chord parse failed", song_id=song_id, error=str(exc))
        return None


async def generate_chord_source(
    song_id: int,
    *,
    client: DashScopeClient | None = None,
) -> ChordSource | None:
    detail = await get_song_detail(song_id)
    if detail is None:
        return None

    llm = client or get_dashscope_client()
    if llm.use_mock:
        return _template_chord_source(song_id, detail)

    prompt = (
        f"为歌曲《{detail.song_name}》-{detail.artist_name} 生成吉他弹唱谱 JSON。"
        "只返回 JSON 对象，字段：key(原调)、capo(变调夹品数)、"
        "guitar_lines、ukulele_lines（各为数组，元素含 position/chord/lyric_line）。"
        "每首歌 6-12 行，和弦用常见开放和弦，歌词用简体中文主歌/副歌片段。"
    )
    try:
        raw = await llm.generate(prompt, temperature=0.2)
        parsed = _parse_llm_chord_source(song_id, detail, raw)
        if parsed is not None:
            return parsed
    except Exception as exc:
        logger.warning("llm chord generation failed", song_id=song_id, error=str(exc))
    return _template_chord_source(song_id, detail)


def _clone_source_for_song(source: ChordSource, song_id: int, detail) -> ChordSource:
    return ChordSource(
        netease_song_id=song_id,
        song_name=detail.song_name,
        artist_name=detail.artist_name,
        cover_url=detail.cover_url or source.cover_url,
        key=source.key,
        capo=source.capo,
        guitar_lines=list(source.guitar_lines),
        ukulele_lines=list(source.ukulele_lines),
        origin=source.origin,
        rhythm_style=source.rhythm_style,
        intro_duration_ms=source.intro_duration_ms,
    )


async def get_chord_source(song_id: int) -> ChordSource | None:
    resolved = _resolve_score_song_id(song_id)
    source = _MOCK_SOURCES.get(song_id) or _MOCK_SOURCES.get(resolved)
    if source is not None:
        return source

    detail = await get_song_detail(song_id)
    if detail is None:
        return None

    target = _normalize_title(detail.song_name)
    seed = _MOCK_BY_TITLE.get(target)
    if seed is not None:
        return _clone_source_for_song(seed, song_id, detail)
    return None


async def resolve_chord_source(
    song_id: int,
    *,
    client: DashScopeClient | None = None,
) -> ChordSource | None:
    source = await get_chord_source(song_id)
    if source is not None:
        return source
    return await generate_chord_source(song_id, client=client)
