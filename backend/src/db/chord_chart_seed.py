"""启动时将 ChordPro 种子文件同步到 chord_charts 表。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.integrations.chord_library import CHORDPRO_DIR, list_chordpro_seed_files, load_chart_from_file
from src.integrations.chordpro_parser import parse_chordpro

from pycore.core.logger import get_logger
from src.db.models import ChordChart

logger = get_logger()


async def seed_chord_charts(db: AsyncSession) -> None:
    if not CHORDPRO_DIR.is_dir():
        return

    for path in list_chordpro_seed_files():
        stem = path.stem
        if "_" not in stem:
            continue
        song_id_str, vocal_version = stem.rsplit("_", 1)
        if vocal_version not in {"male", "female"}:
            continue

        song_id = int(song_id_str)
        existing = await db.execute(
            select(ChordChart).where(
                ChordChart.netease_song_id == song_id,
                ChordChart.vocal_version == vocal_version,
            )
        )
        if existing.scalar_one_or_none() is not None:
            continue

        chart = load_chart_from_file(song_id, vocal_version)
        if chart is None:
            continue

        parsed = parse_chordpro(path.read_text(encoding="utf-8"))
        db.add(
            ChordChart(
                netease_song_id=song_id,
                vocal_version=vocal_version,
                song_name=chart.song_name or parsed.title,
                artist_name=chart.artist_name or parsed.artist,
                key=chart.key,
                capo=chart.capo,
                chordpro_text=path.read_text(encoding="utf-8"),
                source=chart.source,
                rhythm_style=chart.rhythm_style,
                intro_duration_ms=chart.intro_duration_ms,
                ug_tab_id=chart.ug_tab_id,
            )
        )
        logger.info(
            "seeded chord chart",
            song_id=song_id,
            vocal_version=vocal_version,
            source=chart.source,
        )

    await db.commit()
