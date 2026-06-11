"""网易云扫码登录（基于 pyncm）。"""

from __future__ import annotations

import asyncio
import base64
import importlib
import io
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any

from pycore.core.logger import get_logger

logger = get_logger()

_pyncm_lock = threading.Lock()
_pending_logins: dict[str, dict[str, Any]] = {}
_PENDING_TTL_SEC = 180


@dataclass
class QrLoginStart:
    login_token: str
    qr_content: str
    qr_image_base64: str
    expires_in: int


def _import_pyncm():
    import importlib

    return importlib.import_module("pyncm")


def _make_qr_base64(content: str) -> str:
    import qrcode

    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(content)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _purge_expired() -> None:
    now = time.time()
    expired = [key for key, item in _pending_logins.items() if now - item["created_at"] > _PENDING_TTL_SEC]
    for key in expired:
        _pending_logins.pop(key, None)


def start_qr_login(*, guest_id: str) -> QrLoginStart:
    _purge_expired()
    pyncm = _import_pyncm()

    apis = importlib.import_module("pyncm.apis")
    with _pyncm_lock:
        result = apis.login.LoginQrcodeUnikey(1)
    if result.get("code") != 200:
        raise RuntimeError("获取网易云登录二维码失败")

    unikey = str(result["unikey"])
    qr_content = f"https://music.163.com/login?codekey={unikey}"
    login_token = str(uuid.uuid4())
    _pending_logins[login_token] = {
        "guest_id": guest_id,
        "unikey": unikey,
        "created_at": time.time(),
    }
    return QrLoginStart(
        login_token=login_token,
        qr_content=qr_content,
        qr_image_base64=_make_qr_base64(qr_content),
        expires_in=_PENDING_TTL_SEC,
    )


def poll_qr_login(login_token: str) -> dict[str, Any]:
    _purge_expired()
    pending = _pending_logins.get(login_token)
    if pending is None:
        return {"status": "expired", "message": "二维码已过期，请重新获取"}

    pyncm = _import_pyncm()
    apis = importlib.import_module("pyncm.apis")
    with _pyncm_lock:
        result = apis.login.LoginQrcodeCheck(pending["unikey"])
    code = int(result.get("code") or 0)

    if code == 800:
        _pending_logins.pop(login_token, None)
        return {"status": "expired", "message": "二维码已过期，请重新获取"}
    if code == 801:
        return {"status": "waiting", "message": "请使用网易云 App 扫码"}
    if code == 802:
        return {"status": "scanned", "message": "扫码成功，请在手机上确认登录"}
    if code != 803:
        return {"status": "waiting", "message": "等待扫码"}

    with _pyncm_lock:
        if "cookie" in result:
            pyncm.apis.login.WriteLoginInfo(result["cookie"])
        cookies = pyncm.GetCurrentSession().cookies.get_dict()
        nickname = "网易云用户"
        try:
            user_info = pyncm.apis.login.GetCurrentLoginStatus()
            if user_info.get("profile"):
                nickname = str(user_info["profile"].get("nickname") or nickname)
        except Exception as exc:
            logger.warning("netease login status fetch failed", error=str(exc))

    _pending_logins.pop(login_token, None)
    return {
        "status": "success",
        "message": "登录成功",
        "nickname": nickname,
        "cookies": cookies,
    }


async def start_qr_login_async(*, guest_id: str) -> QrLoginStart:
    return await asyncio.to_thread(start_qr_login, guest_id=guest_id)


async def poll_qr_login_async(login_token: str) -> dict[str, Any]:
    return await asyncio.to_thread(poll_qr_login, login_token)
