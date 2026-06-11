"""弹唱谱服务：Mock 和弦 + 水平简化 + 缓存。"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pycore.core.logger import get_logger
from src.api.errors import AppApiError
from src.core.config import get_settings
from src.db.models import ChordCache, GuestSession, ScoreCache
from src.integrations.chord_library import get_library_chart, library_chart_to_lines
from src.integrations.chord_provider import ChordSource, resolve_chord_source
from src.integrations.dashscope_client import DashScopeClient, get_dashscope_client
from src.integrations.lyric_provider import get_netease_lrc_lines
from src.integrations.music_provider import get_song_detail
from src.integrations.rhythm_patterns import pick_rhythm
from src.services.score_merge import merge_chords_with_lrc

logger = get_logger()

SCORE_RENDER_VERSION = 7

BEGINNER_CHORD_MAP: dict[str, str] = {
    "F": "C",
    "Fm": "Am",
    "Bm": "Am",
    "B": "G",
    "Bb": "C",
    "Bbm": "Am",
    "D7": "D",
    "G7": "G",
    "C7": "C",
    "A7": "Am",
    "E7": "Em",
}

DEFAULT_PRACTICE_TIPS: dict[str, str] = {
    "guitar": "整首歌以基础和弦循环，适合练习扫弦节奏，注意换和弦时保持手腕放松。",
    "ukulele": "尤克里里版本建议使用分解和弦，注意节拍稳定，拇指负责低音弦。",
}


def _normalize_skill_level(skill_level: str | None) -> str:
    if skill_level in {"beginner", "intermediate", "advanced"}:
        return skill_level
    return "beginner"


def _normalize_vocal_version(vocal_version: str | None) -> str:
    if vocal_version in {"male", "female"}:
        return vocal_version
    return "male"


def _cache_skill_key(skill_level: str, vocal_version: str) -> str:
    return f"{skill_level}:{vocal_version}"


def _simplify_chord(chord: str, skill_level: str) -> str:
    if skill_level != "beginner":
        return chord
    parts = chord.split()
    return " ".join(BEGINNER_CHORD_MAP.get(part, part) for part in parts)


def _render_lines(lines: list[dict[str, Any]], skill_level: str) -> list[dict[str, Any]]:
    rendered: list[dict[str, Any]] = []
    for line in lines:
        item: dict[str, Any] = {
            "position": int(line.get("position") or 0),
            "chord": _simplify_chord(str(line.get("chord") or ""), skill_level),
            "lyric_line": str(line.get("lyric_line") or ""),
            "section": str(line.get("section") or "vocal"),
        }
        if line.get("start_ms") is not None:
            item["start_ms"] = int(line["start_ms"])
        rendered.append(item)
    return rendered


def _apply_line_timings(
    lines: list[dict[str, Any]],
    duration_ms: int | None,
    intro_duration_ms: int,
) -> list[dict[str, Any]]:
    if not lines:
        return lines
    if all(line.get("start_ms") is not None for line in lines):
        return lines

    total_ms = duration_ms if duration_ms and duration_ms > 0 else 240_000
    intro_ms = intro_duration_ms if any(line.get("section") == "intro" for line in lines) else 0
    intro_ms = min(intro_ms, max(total_ms - 5_000, 0))

    intro_timed: list[dict[str, Any]] = []
    vocal_timed: list[dict[str, Any]] = []

    intro_lines = [line for line in lines if line.get("section") == "intro"]
    vocal_lines = [line for line in lines if line.get("section") != "intro"]

    if intro_lines:
        step = intro_ms / len(intro_lines) if intro_lines else 0
        for index, line in enumerate(intro_lines):
            intro_timed.append({**line, "start_ms": int(index * step)})

    vocal_budget = max(total_ms - intro_ms - 2_000, 1_000)
    weights = [max(len(str(line.get("lyric_line") or "")), 6) for line in vocal_lines]
    weight_total = sum(weights) or 1
    cursor = intro_ms
    for line, weight in zip(vocal_lines, weights, strict=False):
        vocal_timed.append({**line, "start_ms": int(cursor)})
        cursor += vocal_budget * weight / weight_total

    intro_idx = 0
    vocal_idx = 0
    merged: list[dict[str, Any]] = []
    for line in lines:
        if line.get("section") == "intro":
            merged.append(intro_timed[intro_idx])
            intro_idx += 1
        else:
            merged.append(vocal_timed[vocal_idx])
            vocal_idx += 1
    return merged


async def _generate_practice_tips(
    client: DashScopeClient,
    source: ChordSource,
    instrument: str,
    skill_level: str,
    lines: list[dict[str, Any]],
) -> str:
    if client.use_mock:
        return DEFAULT_PRACTICE_TIPS.get(instrument, DEFAULT_PRACTICE_TIPS["guitar"])

    chords = sorted({line["chord"] for line in lines if line.get("chord")})
    prompt = (
        f"你是吉他/尤克里里老师。歌曲《{source.song_name}》-{source.artist_name}，"
        f"乐器={instrument}，水平={skill_level}，调性={source.key}，和弦={', '.join(chords)}。"
        "用一句中文给出练习建议，不超过 60 字，不要换行。"
    )
    try:
        tips = (await client.generate(prompt, temperature=0.3)).strip()
        return tips[:120] if tips else DEFAULT_PRACTICE_TIPS[instrument]
    except Exception as exc:
        logger.warning("practice tips llm failed, use default", error=str(exc))
        return DEFAULT_PRACTICE_TIPS.get(instrument, DEFAULT_PRACTICE_TIPS["guitar"])


async def _ensure_chord_cache(
    db: AsyncSession, source: ChordSource, *, source_tag: str = "mock"
) -> None:
    result = await db.execute(
        select(ChordCache).where(ChordCache.netease_song_id == source.netease_song_id)
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        return

    chords = sorted(
        {
            line["chord"]
            for line in source.guitar_lines + source.ukulele_lines
            if line.get("chord")
        }
    )
    db.add(
        ChordCache(
            netease_song_id=source.netease_song_id,
            song_name=source.song_name,
            artist_name=source.artist_name,
            key=source.key,
            chords=[{"name": name} for name in chords],
            source=source_tag,
        )
    )
    await db.flush()


def _pick_lines(source: ChordSource, instrument: str) -> list[dict[str, Any]]:
    if instrument == "ukulele":
        return list(source.ukulele_lines)
    return list(source.guitar_lines)


async def get_song_score(
    db: AsyncSession,
    guest: GuestSession,
    song_id: int,
    instrument: str = "guitar",
    vocal_version: str = "male",
    *,
    client: DashScopeClient | None = None,
) -> dict[str, Any]:
    if instrument not in {"guitar", "ukulele"}:
        raise AppApiError(40001, "instrument 仅支持 guitar 或 ukulele")

    if get_settings().chord_provider != "mock":
        raise AppApiError(50003, "和弦数据源暂不可用", http_status=500)

    skill_level = _normalize_skill_level(guest.skill_level)
    vocal_version = _normalize_vocal_version(vocal_version)
    cache_key = _cache_skill_key(skill_level, vocal_version)

    cached = await db.execute(
        select(ScoreCache).where(
            ScoreCache.netease_song_id == song_id,
            ScoreCache.instrument == instrument,
            ScoreCache.skill_level == cache_key,
        )
    )
    hit = cached.scalar_one_or_none()
    if hit is not None:
        cached_payload = dict(hit.rendered_score)
        if cached_payload.get("_version") == SCORE_RENDER_VERSION:
            logger.info("score cache hit", song_id=song_id, instrument=instrument)
            return cached_payload
        await db.delete(hit)
        await db.flush()

    llm = client or get_dashscope_client()

    library_chart = await get_library_chart(db, song_id, vocal_version)
    if library_chart is not None:
        raw_lines = library_chart_to_lines(library_chart, instrument)
        score_key = library_chart.key
        score_capo = library_chart.capo
        chord_source = f"verified:{library_chart.source}"
        rhythm_style = library_chart.rhythm_style
        intro_duration_seed = library_chart.intro_duration_ms
        song_name = library_chart.song_name
        artist_name = library_chart.artist_name
        cover_url = ""
        source_origin = library_chart.source
    else:
        source = await resolve_chord_source(song_id, client=llm)
        if source is None:
            raise AppApiError(40403, "暂无该歌曲谱面数据", http_status=404)

        raw_lines = _pick_lines(source, instrument)
        score_key = source.key
        score_capo = source.capo
        chord_source = source.origin
        rhythm_style = source.rhythm_style
        intro_duration_seed = source.intro_duration_ms
        song_name = source.song_name
        artist_name = source.artist_name
        cover_url = source.cover_url
        source_origin = source.origin

    cache_source = "verified" if chord_source.startswith("verified:") else (
        "mock" if source_origin == "seed" else source_origin
    )
    await _ensure_chord_cache(
        db,
        ChordSource(
            netease_song_id=song_id,
            song_name=song_name,
            artist_name=artist_name,
            cover_url=cover_url,
            key=score_key,
            capo=score_capo,
            guitar_lines=raw_lines,
            ukulele_lines=raw_lines,
            origin=source_origin,
        ),
        source_tag=cache_source,
    )

    detail = await get_song_detail(song_id)
    duration_ms = detail.duration_ms if detail and detail.duration_ms else None

    lrc_lines = await get_netease_lrc_lines(song_id)
    lyric_source = "seed"
    if lrc_lines:
        lines = merge_chords_with_lrc(
            raw_lines,
            lrc_lines,
            skill_level=skill_level,
            simplify_chord=_simplify_chord,
        )
        has_vocal_chords = any(
            line.get("chord") or line.get("chord_marks")
            for line in lines
            if line.get("section") != "intro"
        )
        if not has_vocal_chords:
            lines = _render_lines(raw_lines, skill_level)
            lines = _apply_line_timings(lines, duration_ms, intro_duration_seed)
            lyric_source = "seed"
            intro_duration_ms = intro_duration_seed
        else:
            lyric_source = "netease"
            intro_duration_ms = (
                int(lrc_lines[0]["start_ms"]) if lrc_lines else intro_duration_seed
            )
    else:
        lines = _render_lines(raw_lines, skill_level)
        lines = _apply_line_timings(lines, duration_ms, intro_duration_seed)
        intro_duration_ms = intro_duration_seed

    tips_source = ChordSource(
        netease_song_id=song_id,
        song_name=song_name,
        artist_name=artist_name,
        cover_url=cover_url,
        key=score_key,
        capo=score_capo,
        guitar_lines=raw_lines,
        ukulele_lines=raw_lines,
        origin=source_origin,
    )
    practice_tips = await _generate_practice_tips(llm, tips_source, instrument, skill_level, lines)

    payload: dict[str, Any] = {
        "_version": SCORE_RENDER_VERSION,
        "netease_song_id": song_id,
        "song_name": song_name,
        "artist_name": artist_name,
        "cover_url": cover_url,
        "instrument": instrument,
        "skill_level": skill_level,
        "vocal_version": vocal_version,
        "key": score_key,
        "capo": score_capo,
        "lines": lines,
        "practice_tips": practice_tips,
        "rhythm_pattern": pick_rhythm(instrument, rhythm_style),
        "intro_duration_ms": intro_duration_ms,
        "duration_ms": duration_ms,
        "lyric_source": lyric_source,
        "chord_source": chord_source,
    }

    db.add(
        ScoreCache(
            netease_song_id=song_id,
            instrument=instrument,
            skill_level=cache_key,
            rendered_score=payload,
        )
    )
    await db.commit()
    return payload
