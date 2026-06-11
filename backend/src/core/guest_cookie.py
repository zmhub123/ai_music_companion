"""游客 Cookie 工具。"""

from fastapi import Response

GUEST_COOKIE_NAME = "guest_id"


def guest_cookie_max_age(max_age_days: int) -> int:
    return max_age_days * 24 * 60 * 60


def set_guest_cookie(response: Response, guest_id: str, max_age_days: int) -> None:
    response.set_cookie(
        key=GUEST_COOKIE_NAME,
        value=guest_id,
        httponly=True,
        samesite="lax",
        max_age=guest_cookie_max_age(max_age_days),
        path="/",
    )


def clear_guest_cookie(response: Response) -> None:
    response.delete_cookie(key=GUEST_COOKIE_NAME, path="/")
