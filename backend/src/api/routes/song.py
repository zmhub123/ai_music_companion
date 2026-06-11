import httpx
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from pycore.api.responses import APIResponse, success_response
from src.api.deps import get_current_guest
from src.api.errors import AppApiError
from src.db.models import GuestSession
from src.db.session import get_db
from src.services import music_service, score_job_service, score_service

router = APIRouter(prefix="/api/v1/songs", tags=["songs"])


@router.get("/search")
async def search_songs(
    q: str = Query(min_length=1),
    limit: int = Query(default=10, ge=1, le=30),
) -> APIResponse:
    data = await music_service.search_song_list(q, limit=limit)
    return success_response(data)


@router.get("/{netease_song_id}")
async def get_song(netease_song_id: int) -> APIResponse:
    data = await music_service.get_song(netease_song_id)
    return success_response(data)


@router.get("/{netease_song_id}/play-url")
async def get_play_url(
    netease_song_id: int,
    guest: GuestSession = Depends(get_current_guest),
) -> APIResponse:
    data = await music_service.get_play_url(
        netease_song_id, netease_cookies=guest.netease_cookies
    )
    return success_response(data)


@router.get("/{netease_song_id}/score")
async def get_song_score(
    netease_song_id: int,
    instrument: str = Query(default="guitar"),
    vocal_version: str = Query(default="male"),
    db: AsyncSession = Depends(get_db),
    guest: GuestSession = Depends(get_current_guest),
) -> APIResponse:
    data = await score_service.get_song_score(
        db, guest, netease_song_id, instrument=instrument, vocal_version=vocal_version
    )
    return success_response(data)


@router.post("/{netease_song_id}/score/jobs")
async def create_score_job(
    netease_song_id: int,
    instrument: str = Query(default="guitar"),
    vocal_version: str = Query(default="male"),
    db: AsyncSession = Depends(get_db),
    guest: GuestSession = Depends(get_current_guest),
) -> APIResponse:
    job = await score_job_service.create_score_job(
        db, guest, netease_song_id, instrument=instrument, vocal_version=vocal_version
    )
    return success_response(score_job_service.job_to_dict(job))


@router.get("/score/jobs/{job_id}")
async def get_score_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    guest: GuestSession = Depends(get_current_guest),
) -> APIResponse:
    job = await score_job_service.get_score_job(db, guest, job_id)
    return success_response(score_job_service.job_to_dict(job))


@router.get("/{netease_song_id}/stream", response_model=None)
async def stream_song(netease_song_id: int):
    try:
        source_url = await music_service.get_stream_source(netease_song_id)
    except AppApiError as exc:
        return JSONResponse(
            status_code=exc.http_status,
            content={"code": exc.code, "message": exc.message, "data": exc.data},
        )

    async def iter_bytes():
        async with httpx.AsyncClient(
            trust_env=False, timeout=60.0, follow_redirects=True
        ) as client:
            async with client.stream("GET", source_url) as response:  # noqa: SIM117
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    yield chunk

    return StreamingResponse(iter_bytes(), media_type="audio/mpeg")
