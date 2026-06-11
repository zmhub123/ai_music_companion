from fastapi import Cookie, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.errors import AppApiError
from src.core.guest_cookie import GUEST_COOKIE_NAME
from src.db.models import GuestSession
from src.db.session import get_db


async def get_current_guest(
    db: AsyncSession = Depends(get_db),
    guest_id: str | None = Cookie(default=None, alias=GUEST_COOKIE_NAME),
) -> GuestSession:
    if not guest_id:
        raise AppApiError(40101, "游客 Session 无效", http_status=401)

    result = await db.execute(select(GuestSession).where(GuestSession.guest_id == guest_id))
    guest = result.scalar_one_or_none()
    if guest is None:
        raise AppApiError(40101, "游客 Session 无效", http_status=401)
    return guest
