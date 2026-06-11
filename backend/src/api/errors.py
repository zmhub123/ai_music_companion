"""统一 API 错误响应。"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppApiError(Exception):
    def __init__(
        self,
        code: int,
        message: str,
        http_status: int = 400,
        data: Any = None,
    ) -> None:
        self.code = code
        self.message = message
        self.http_status = http_status
        self.data = data


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppApiError)
    async def app_api_exception_handler(
        _request: Request, exc: AppApiError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content={"code": exc.code, "message": exc.message, "data": exc.data},
        )
