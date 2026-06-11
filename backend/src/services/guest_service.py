"""游客 Session 业务逻辑。"""

from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.errors import AppApiError
from src.db.models import ChatMessage, GuestSession, Playlist, PlaylistSong


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def guest_to_me_dict(guest: GuestSession) -> dict:
    logged_in = bool(getattr(guest, "netease_cookies", None))
    return {
        "guest_id": guest.guest_id,
        "skill_level": guest.skill_level,
        "style_preferences": guest.style_preferences or [],
        "onboarding_completed": guest.onboarding_completed,
        "created_at": _iso(guest.created_at),
        "last_active_at": _iso(guest.last_active_at),
        "netease_logged_in": logged_in,
        "netease_nickname": guest.netease_nickname if logged_in else None,
    }


async def create_guest_session(db: AsyncSession) -> GuestSession:
    guest = GuestSession()
    db.add(guest)
    await db.commit()
    await db.refresh(guest)
    return guest


async def touch_guest(db: AsyncSession, guest: GuestSession) -> GuestSession:
    guest.last_active_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(guest)
    return guest


async def complete_onboarding(
    db: AsyncSession,
    guest: GuestSession,
    skill_level: str,
    style_preferences: list[str],
) -> GuestSession:
    if len(style_preferences) < 1:
        raise AppApiError(40001, "style_preferences 至少选择 1 项")

    guest.skill_level = skill_level
    guest.style_preferences = style_preferences
    guest.onboarding_completed = True
    guest.last_active_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(guest)
    return guest


async def update_preferences(
    db: AsyncSession,
    guest: GuestSession,
    skill_level: str,
    style_preferences: list[str],
) -> GuestSession:
    if len(style_preferences) < 1:
        raise AppApiError(40001, "style_preferences 至少选择 1 项")

    guest.skill_level = skill_level
    guest.style_preferences = style_preferences
    guest.onboarding_completed = True
    guest.last_active_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(guest)
    return guest


async def clear_guest_data(db: AsyncSession, guest: GuestSession) -> GuestSession:
    playlist_ids = (
        await db.execute(select(Playlist.id).where(Playlist.guest_id == guest.guest_id))
    ).scalars().all()

    if playlist_ids:
        await db.execute(delete(PlaylistSong).where(PlaylistSong.playlist_id.in_(playlist_ids)))
        await db.execute(delete(Playlist).where(Playlist.guest_id == guest.guest_id))

    await db.execute(delete(ChatMessage).where(ChatMessage.guest_id == guest.guest_id))

    guest.skill_level = None
    guest.style_preferences = []
    guest.onboarding_completed = False
    guest.netease_cookies = None
    guest.netease_nickname = None
    guest.last_active_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(guest)
    return guest
