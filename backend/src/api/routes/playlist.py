from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from pycore.api.responses import APIResponse, success_response
from src.api.deps import get_current_guest
from src.api.schemas.playlist import AddSongRequest, CreatePlaylistRequest, UpdatePlaylistRequest
from src.db.models import GuestSession
from src.db.session import get_db
from src.services import playlist_service

router = APIRouter(prefix="/api/v1/playlists", tags=["playlists"])


@router.get("")
async def list_playlists(
    guest: GuestSession = Depends(get_current_guest),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    data = await playlist_service.list_playlists(db, guest.guest_id)
    return success_response(data)


@router.post("")
async def create_playlist(
    payload: CreatePlaylistRequest,
    guest: GuestSession = Depends(get_current_guest),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    data = await playlist_service.create_playlist(
        db, guest.guest_id, payload.name, payload.description
    )
    return success_response(data)


@router.get("/{playlist_id}")
async def get_playlist(
    playlist_id: str,
    guest: GuestSession = Depends(get_current_guest),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    data = await playlist_service.get_playlist_detail(db, guest.guest_id, playlist_id)
    return success_response(data)


@router.put("/{playlist_id}")
async def update_playlist(
    playlist_id: str,
    payload: UpdatePlaylistRequest,
    guest: GuestSession = Depends(get_current_guest),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    data = await playlist_service.update_playlist(
        db, guest.guest_id, playlist_id, payload.name, payload.description
    )
    return success_response(data)


@router.delete("/{playlist_id}")
async def delete_playlist(
    playlist_id: str,
    guest: GuestSession = Depends(get_current_guest),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    data = await playlist_service.delete_playlist(db, guest.guest_id, playlist_id)
    return success_response(data)


@router.post("/{playlist_id}/songs")
async def add_song(
    playlist_id: str,
    payload: AddSongRequest,
    guest: GuestSession = Depends(get_current_guest),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    data = await playlist_service.add_song_to_playlist(
        db,
        guest.guest_id,
        playlist_id,
        payload.netease_song_id,
        payload.song_name,
        payload.artist_name,
        payload.cover_url,
    )
    return success_response(data)


@router.delete("/{playlist_id}/songs/{playlist_song_id}")
async def remove_song(
    playlist_id: str,
    playlist_song_id: str,
    guest: GuestSession = Depends(get_current_guest),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    data = await playlist_service.remove_song_from_playlist(
        db, guest.guest_id, playlist_id, playlist_song_id
    )
    return success_response(data)
