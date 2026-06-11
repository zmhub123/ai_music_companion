"""网易云账号绑定（按游客 Session 存储 Cookie）。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import GuestSession
from src.integrations.netease_auth import poll_qr_login_async, start_qr_login_async


async def start_login_qr(*, guest: GuestSession) -> dict[str, Any]:
    started = await start_qr_login_async(guest_id=guest.guest_id)
    return {
        "login_token": started.login_token,
        "qr_content": started.qr_content,
        "qr_image_base64": started.qr_image_base64,
        "expires_in": started.expires_in,
    }


async def poll_login_qr(
    db: AsyncSession, guest: GuestSession, login_token: str
) -> dict[str, Any]:
    result = await poll_qr_login_async(login_token)
    if result.get("status") != "success":
        return result

    guest.netease_cookies = result.get("cookies") or {}
    guest.netease_nickname = str(result.get("nickname") or "网易云用户")
    guest.last_active_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(guest)
    return {
        "status": "success",
        "message": result.get("message") or "登录成功",
        "nickname": guest.netease_nickname,
        "logged_in": True,
    }


async def logout_netease(db: AsyncSession, guest: GuestSession) -> GuestSession:
    guest.netease_cookies = None
    guest.netease_nickname = None
    guest.last_active_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(guest)
    return guest


def netease_status(guest: GuestSession) -> dict[str, Any]:
    logged_in = bool(guest.netease_cookies)
    return {
        "logged_in": logged_in,
        "nickname": guest.netease_nickname if logged_in else None,
    }
