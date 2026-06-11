from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from pycore.api.responses import APIResponse, success_response
from src.api.deps import get_current_guest
from src.api.schemas.chat import SendMessageRequest
from src.db.models import GuestSession
from src.db.session import get_db
from src.services import chat_service

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.get("/messages")
async def get_messages(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    guest: GuestSession = Depends(get_current_guest),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    data = await chat_service.list_messages(db, guest.guest_id, page=page, page_size=page_size)
    return success_response(data)


@router.post("/messages")
async def post_message(
    payload: SendMessageRequest,
    guest: GuestSession = Depends(get_current_guest),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    data = await chat_service.send_message(db, guest, payload.content)
    return success_response(data)


@router.post("/reset")
async def reset_chat(
    guest: GuestSession = Depends(get_current_guest),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    data = await chat_service.reset_messages(db, guest.guest_id)
    return success_response(data)
