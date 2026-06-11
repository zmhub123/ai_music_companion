from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from pycore.api.responses import APIResponse, success_response
from src.api.deps import get_current_guest
from src.db.models import GuestSession
from src.db.session import get_db
from src.services import netease_service

router = APIRouter(prefix="/api/v1/netease", tags=["netease"])


@router.get("/auth/status")
async def netease_auth_status(
    guest: GuestSession = Depends(get_current_guest),
) -> APIResponse:
    return success_response(netease_service.netease_status(guest))


@router.post("/login/qr")
async def start_netease_qr_login(
    guest: GuestSession = Depends(get_current_guest),
) -> APIResponse:
    return success_response(await netease_service.start_login_qr(guest=guest))


@router.get("/login/qr/{login_token}")
async def poll_netease_qr_login(
    login_token: str,
    guest: GuestSession = Depends(get_current_guest),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    return success_response(await netease_service.poll_login_qr(db, guest, login_token))


@router.post("/logout")
async def logout_netease(
    guest: GuestSession = Depends(get_current_guest),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    guest = await netease_service.logout_netease(db, guest)
    return success_response(netease_service.netease_status(guest))
