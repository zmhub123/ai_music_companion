"""异步谱面生成任务：进度可视化 + 音频扒谱。"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pycore.core.logger import get_logger
from src.api.errors import AppApiError
from src.db.models import GuestSession, ScoreCache, ScoreGenerationJob
from src.db.session import async_session_maker
from src.integrations.audio_analyzer import analyze_audio_from_url
from src.integrations.dashscope_client import get_dashscope_client
from src.integrations.lyric_provider import get_netease_lrc_lines
from src.integrations.music_provider import get_song_detail
from src.integrations.netease_session import run_with_netease_cookies
from src.services.music_service import get_play_url
from src.services.score_audio_pipeline import SCORE_AUDIO_VERSION, build_score_from_audio
logger = get_logger()

_ANALYZE_TIMEOUT_SEC = 90.0
_STALE_JOB_AFTER = timedelta(minutes=3)

STAGE_LABELS = {
    "queued": "排队中",
    "checking_playback": "检查播放权限",
    "fetching_audio": "下载音频",
    "analyzing_chords": "分析和弦",
    "fetching_lyrics": "拉取歌词",
    "aligning": "生成曲谱",
    "rendering": "整理输出",
    "completed": "完成",
    "failed": "失败",
}


async def _update_job(
    db: AsyncSession,
    job: ScoreGenerationJob,
    *,
    status: str | None = None,
    progress: int | None = None,
    stage: str | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
    result: dict[str, Any] | None = None,
) -> None:
    if status is not None:
        job.status = status
    if progress is not None:
        job.progress = max(0, min(100, progress))
    if stage is not None:
        job.stage = stage
    if error_code is not None:
        job.error_code = error_code
    if error_message is not None:
        job.error_message = error_message
    if result is not None:
        job.result = result
    job.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(job)


def job_to_dict(job: ScoreGenerationJob) -> dict[str, Any]:
    return {
        "job_id": job.id,
        "netease_song_id": job.netease_song_id,
        "instrument": job.instrument,
        "vocal_version": job.vocal_version,
        "status": job.status,
        "progress": job.progress,
        "stage": job.stage,
        "stage_label": STAGE_LABELS.get(job.stage, job.stage),
        "error_code": job.error_code,
        "error_message": job.error_message,
        "result": job.result,
    }


async def _find_cached_score(
    db: AsyncSession,
    job: ScoreGenerationJob,
) -> dict[str, Any] | None:
    cache_key = f"{job.skill_level}:{job.vocal_version}"
    result = await db.execute(
        select(ScoreCache).where(
            ScoreCache.netease_song_id == job.netease_song_id,
            ScoreCache.instrument == job.instrument,
            ScoreCache.skill_level == cache_key,
        )
    )
    hit = result.scalar_one_or_none()
    if hit is None:
        return None
    payload = dict(hit.rendered_score)
    if payload.get("_version") != SCORE_AUDIO_VERSION:
        return None
    if payload.get("chord_source") != "audio_analysis+llm":
        return None
    return payload


async def create_score_job(
    db: AsyncSession,
    guest: GuestSession,
    song_id: int,
    instrument: str,
    vocal_version: str,
) -> ScoreGenerationJob:
    skill_level = guest.skill_level or "beginner"
    existing = await db.execute(
        select(ScoreGenerationJob).where(
            ScoreGenerationJob.guest_id == guest.guest_id,
            ScoreGenerationJob.netease_song_id == song_id,
            ScoreGenerationJob.instrument == instrument,
            ScoreGenerationJob.vocal_version == vocal_version,
            ScoreGenerationJob.status.in_(("pending", "running")),
        )
    )
    running = existing.scalar_one_or_none()
    if running is not None:
        updated_at = running.updated_at or running.created_at
        if updated_at and datetime.now(UTC) - updated_at > _STALE_JOB_AFTER:
            await _update_job(
                db,
                running,
                status="failed",
                stage="failed",
                progress=100,
                error_code="TIMEOUT",
                error_message="谱面生成任务超时，请重试",
            )
        else:
            return running

    job = ScoreGenerationJob(
        guest_id=guest.guest_id,
        netease_song_id=song_id,
        instrument=instrument,
        vocal_version=vocal_version,
        skill_level=skill_level,
        status="pending",
        progress=0,
        stage="queued",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    asyncio.create_task(run_score_job(job.id))
    return job


async def get_score_job(db: AsyncSession, guest: GuestSession, job_id: str) -> ScoreGenerationJob:
    result = await db.execute(
        select(ScoreGenerationJob).where(
            ScoreGenerationJob.id == job_id,
            ScoreGenerationJob.guest_id == guest.guest_id,
        )
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise AppApiError(40404, "谱面生成任务不存在", http_status=404)
    return job


async def run_score_job(job_id: str) -> None:
    async with async_session_maker() as db:
        result = await db.execute(select(ScoreGenerationJob).where(ScoreGenerationJob.id == job_id))
        job = result.scalar_one_or_none()
        if job is None:
            return

        guest_result = await db.execute(
            select(GuestSession).where(GuestSession.guest_id == job.guest_id)
        )
        guest = guest_result.scalar_one_or_none()
        if guest is None:
            await _update_job(
                db,
                job,
                status="failed",
                stage="failed",
                progress=100,
                error_code="40101",
                error_message="游客 Session 无效",
            )
            return

        try:
            await _update_job(db, job, status="running", progress=5, stage="checking_playback")

            cached_score = await _find_cached_score(db, job)
            if cached_score is not None:
                await _update_job(
                    db,
                    job,
                    status="completed",
                    stage="completed",
                    progress=100,
                    result=cached_score,
                )
                return

            cookies = guest.netease_cookies
            try:
                play = await get_play_url_for_guest(job.netease_song_id, cookies)
            except AppApiError as exc:
                if exc.code == 50004 and exc.data and exc.data.get("vip_required"):
                    if not cookies:
                        await _update_job(
                            db,
                            job,
                            status="failed",
                            stage="failed",
                            progress=100,
                            error_code="NEED_NETEASE_LOGIN",
                            error_message="需要登录网易云账号后重试",
                        )
                        return
                    await _update_job(
                        db,
                        job,
                        status="failed",
                        stage="failed",
                        progress=100,
                        error_code="VIP_REQUIRED",
                        error_message="抱歉，呜呜音源要钱",
                    )
                    return
                if not cookies:
                    await _update_job(
                        db,
                        job,
                        status="failed",
                        stage="failed",
                        progress=100,
                        error_code="NEED_NETEASE_LOGIN",
                        error_message="需要登录网易云账号后重试",
                    )
                    return
                raise

            await _update_job(db, job, progress=15, stage="fetching_audio")
            stream_url = play.get("stream_url") or play.get("url")
            if not stream_url:
                if not cookies:
                    await _update_job(
                        db,
                        job,
                        status="failed",
                        stage="failed",
                        progress=100,
                        error_code="NEED_NETEASE_LOGIN",
                        error_message="需要登录网易云账号后重试",
                    )
                    return
                await _update_job(
                    db,
                    job,
                    status="failed",
                    stage="failed",
                    progress=100,
                    error_code="VIP_REQUIRED",
                    error_message="抱歉，呜呜音源要钱",
                )
                return

            await _update_job(db, job, progress=35, stage="analyzing_chords")
            job_id = job.id

            async def _report_analyze_sub(frac: int) -> None:
                async with async_session_maker() as progress_db:
                    row = await progress_db.get(ScoreGenerationJob, job_id)
                    if row is None or row.status != "running":
                        return
                    row.progress = min(60, 35 + int(frac * 0.25))
                    row.updated_at = datetime.now(UTC)
                    await progress_db.commit()

            def _on_analyze_progress(frac: int) -> None:
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(_report_analyze_sub(frac))
                except RuntimeError:
                    pass

            detail = await get_song_detail(job.netease_song_id)
            if detail is None:
                raise AppApiError(40402, "歌曲不存在", http_status=404)

            try:
                chord_timeline = await asyncio.wait_for(
                    analyze_audio_from_url(
                        stream_url,
                        duration_ms=detail.duration_ms,
                        on_progress=_on_analyze_progress,
                    ),
                    timeout=_ANALYZE_TIMEOUT_SEC,
                )
            except TimeoutError as exc:
                raise AppApiError(
                    50005,
                    "音频分析超时，请稍后重试",
                    http_status=500,
                ) from exc

            await _update_job(db, job, progress=65, stage="fetching_lyrics")
            lrc_lines = await get_netease_lrc_lines_with_cookies(job.netease_song_id, cookies)
            if not lrc_lines:
                raise AppApiError(40405, "暂无歌词，无法生成完整曲谱", http_status=404)

            await _update_job(db, job, progress=85, stage="aligning")
            llm = get_dashscope_client()
            score = await build_score_from_audio(
                llm=llm,
                song_id=job.netease_song_id,
                song_name=detail.song_name,
                artist_name=detail.artist_name,
                cover_url=detail.cover_url or "",
                duration_ms=detail.duration_ms,
                instrument=job.instrument,
                vocal_version=job.vocal_version,
                skill_level=job.skill_level,
                chord_timeline=chord_timeline,
                lrc_lines=lrc_lines,
            )

            await _update_job(db, job, progress=95, stage="rendering")

            cache_key = f"{job.skill_level}:{job.vocal_version}"
            cache_hit = await db.execute(
                select(ScoreCache).where(
                    ScoreCache.netease_song_id == job.netease_song_id,
                    ScoreCache.instrument == job.instrument,
                    ScoreCache.skill_level == cache_key,
                )
            )
            existing_cache = cache_hit.scalar_one_or_none()
            if existing_cache is None:
                db.add(
                    ScoreCache(
                        netease_song_id=job.netease_song_id,
                        instrument=job.instrument,
                        skill_level=cache_key,
                        rendered_score=score,
                    )
                )
            else:
                existing_cache.rendered_score = score

            await _update_job(
                db,
                job,
                status="completed",
                stage="completed",
                progress=100,
                result=score,
            )
        except AppApiError as exc:
            await _update_job(
                db,
                job,
                status="failed",
                stage="failed",
                progress=100,
                error_code=str(exc.code),
                error_message=exc.message,
            )
        except Exception as exc:
            logger.exception("score job failed", job_id=job_id, error=str(exc))
            await _update_job(
                db,
                job,
                status="failed",
                stage="failed",
                progress=100,
                error_code="50000",
                error_message="谱面生成失败，请稍后重试",
            )


async def get_play_url_for_guest(song_id: int, cookies: dict[str, Any] | None) -> dict[str, Any]:
    play = await get_play_url(song_id, netease_cookies=cookies)
    url = play.get("url")
    if url:
        play["stream_url"] = url
    return play


async def get_netease_lrc_lines_with_cookies(
    song_id: int, cookies: dict[str, Any] | None
) -> list[dict[str, Any]]:
    if not cookies:
        return await get_netease_lrc_lines(song_id)

    def _fetch():
        from src.integrations.lyric_provider import _fetch_lrc_sync

        return _fetch_lrc_sync(song_id)

    return await asyncio.to_thread(lambda: run_with_netease_cookies(cookies, _fetch))
