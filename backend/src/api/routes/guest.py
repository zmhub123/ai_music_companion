from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from pycore.api.responses import APIResponse, success_response
from src.api.deps import get_current_guest
from src.api.schemas.guest import OnboardingRequest, PreferencesRequest
from src.core.config import settings
from src.core.guest_cookie import set_guest_cookie
from src.db.models import GuestSession
from src.db.session import get_db
from src.services import guest_service

router = APIRouter(prefix="/api/v1/guest", tags=["guest"])


@router.post("/session")
async def create_session(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    guest = await guest_service.create_guest_session(db)
    set_guest_cookie(response, guest.guest_id, settings.guest_session_max_age_days)
    return success_response(
        {
            "guest_id": guest.guest_id,
            "onboarding_completed": guest.onboarding_completed,
            "skill_level": guest.skill_level,
            "style_preferences": guest.style_preferences or [],
        }
    )


@router.get("/me")
async def get_me(
    guest: GuestSession = Depends(get_current_guest),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    guest = await guest_service.touch_guest(db, guest)
    return success_response(guest_service.guest_to_me_dict(guest))


@router.post("/onboarding")
async def complete_onboarding(
    payload: OnboardingRequest,
    guest: GuestSession = Depends(get_current_guest),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    guest = await guest_service.complete_onboarding(
        db, guest, payload.skill_level, payload.style_preferences
    )
    return success_response(
        {
            "guest_id": guest.guest_id,
            "skill_level": guest.skill_level,
            "style_preferences": guest.style_preferences,
            "onboarding_completed": guest.onboarding_completed,
        }
    )


@router.put("/preferences")
async def update_preferences(
    payload: PreferencesRequest,
    guest: GuestSession = Depends(get_current_guest),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    guest = await guest_service.update_preferences(
        db, guest, payload.skill_level, payload.style_preferences
    )
    return success_response(
        {
            "skill_level": guest.skill_level,
            "style_preferences": guest.style_preferences,
        }
    )


@router.delete("/data")
async def clear_data(
    guest: GuestSession = Depends(get_current_guest),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    guest = await guest_service.clear_guest_data(db, guest)
    return success_response(
        {
            "cleared": True,
            "onboarding_completed": guest.onboarding_completed,
        }
    )
