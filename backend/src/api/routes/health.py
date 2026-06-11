from fastapi import APIRouter

from pycore.api.responses import APIResponse, success_response

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> APIResponse:
    return success_response({"status": "ok"})
