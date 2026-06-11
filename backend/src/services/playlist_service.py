"""歌单 CRUD 业务逻辑。"""

from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.errors import AppApiError
from src.db.models import Playlist, PlaylistSong


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


async def _song_count(db: AsyncSession, playlist_id: str) -> int:
    count = await db.scalar(
        select(func.count()).select_from(PlaylistSong).where(PlaylistSong.playlist_id == playlist_id)
    )
    return int(count or 0)


def _summary_dict(playlist: Playlist, song_count: int) -> dict:
    return {
        "id": playlist.id,
        "name": playlist.name,
        "description": playlist.description or "",
        "cover_url": playlist.cover_url,
        "song_count": song_count,
        "created_at": _iso(playlist.created_at),
        "updated_at": _iso(playlist.updated_at),
    }


def _song_dict(song: PlaylistSong) -> dict:
    return {
        "id": song.id,
        "netease_song_id": song.netease_song_id,
        "song_name": song.song_name,
        "artist_name": song.artist_name,
        "cover_url": song.cover_url or "",
        "added_at": _iso(song.added_at),
    }


async def _get_owned_playlist(
    db: AsyncSession, guest_id: str, playlist_id: str
) -> Playlist:
    result = await db.execute(
        select(Playlist).where(Playlist.id == playlist_id, Playlist.guest_id == guest_id)
    )
    playlist = result.scalar_one_or_none()
    if playlist is None:
        raise AppApiError(40401, "歌单不存在", http_status=404)
    return playlist


async def list_playlists(db: AsyncSession, guest_id: str) -> dict:
    result = await db.execute(
        select(Playlist).where(Playlist.guest_id == guest_id).order_by(Playlist.updated_at.desc())
    )
    playlists = result.scalars().all()
    items = []
    for playlist in playlists:
        count = await _song_count(db, playlist.id)
        items.append(_summary_dict(playlist, count))
    return {"items": items, "total": len(items)}


async def create_playlist(
    db: AsyncSession, guest_id: str, name: str, description: str
) -> dict:
    playlist = Playlist(
        guest_id=guest_id,
        name=name,
        description=description or None,
    )
    db.add(playlist)
    await db.commit()
    await db.refresh(playlist)
    return _summary_dict(playlist, 0)


async def get_playlist_detail(
    db: AsyncSession, guest_id: str, playlist_id: str
) -> dict:
    playlist = await _get_owned_playlist(db, guest_id, playlist_id)
    songs_result = await db.execute(
        select(PlaylistSong)
        .where(PlaylistSong.playlist_id == playlist.id)
        .order_by(PlaylistSong.added_at.desc())
    )
    songs = songs_result.scalars().all()
    data = _summary_dict(playlist, len(songs))
    data["songs"] = [_song_dict(song) for song in songs]
    return data


async def update_playlist(
    db: AsyncSession, guest_id: str, playlist_id: str, name: str, description: str
) -> dict:
    playlist = await _get_owned_playlist(db, guest_id, playlist_id)
    playlist.name = name
    playlist.description = description or None
    playlist.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(playlist)
    count = await _song_count(db, playlist.id)
    return _summary_dict(playlist, count)


async def delete_playlist(db: AsyncSession, guest_id: str, playlist_id: str) -> dict:
    playlist = await _get_owned_playlist(db, guest_id, playlist_id)
    await db.execute(delete(PlaylistSong).where(PlaylistSong.playlist_id == playlist.id))
    await db.delete(playlist)
    await db.commit()
    return {"deleted": True, "playlist_id": playlist_id}


async def add_song_to_playlist(
    db: AsyncSession,
    guest_id: str,
    playlist_id: str,
    netease_song_id: int,
    song_name: str,
    artist_name: str,
    cover_url: str,
) -> dict:
    playlist = await _get_owned_playlist(db, guest_id, playlist_id)

    existing = await db.execute(
        select(PlaylistSong).where(
            PlaylistSong.playlist_id == playlist.id,
            PlaylistSong.netease_song_id == netease_song_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise AppApiError(40001, "歌曲已在歌单中")

    song = PlaylistSong(
        playlist_id=playlist.id,
        netease_song_id=netease_song_id,
        song_name=song_name,
        artist_name=artist_name,
        cover_url=cover_url or None,
    )
    db.add(song)

    if playlist.cover_url is None and cover_url:
        playlist.cover_url = cover_url

    playlist.updated_at = datetime.now(UTC)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise AppApiError(40001, "歌曲已在歌单中") from exc

    await db.refresh(song)
    return _song_dict(song)


async def remove_song_from_playlist(
    db: AsyncSession, guest_id: str, playlist_id: str, playlist_song_id: str
) -> dict:
    playlist = await _get_owned_playlist(db, guest_id, playlist_id)
    result = await db.execute(
        select(PlaylistSong).where(
            PlaylistSong.id == playlist_song_id,
            PlaylistSong.playlist_id == playlist.id,
        )
    )
    song = result.scalar_one_or_none()
    if song is None:
        raise AppApiError(40401, "歌单不存在", http_status=404)

    await db.delete(song)
    playlist.updated_at = datetime.now(UTC)
    await db.commit()
    return {"deleted": True, "playlist_song_id": playlist_song_id}
