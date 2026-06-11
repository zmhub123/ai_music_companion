"""按游客绑定网易云 Cookie，隔离 pyncm 全局 Session。"""

from __future__ import annotations

import importlib
import json
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from pycore.core.logger import get_logger

from src.core.config import get_settings

logger = get_logger()

T = TypeVar("T")
_pyncm_lock = threading.Lock()
_env_cookies_loaded = False


def _pyncm_available() -> bool:
    try:
        importlib.import_module("pyncm")
        return True
    except ImportError:
        return False


def _load_env_cookies_if_needed() -> None:
    global _env_cookies_loaded
    if _env_cookies_loaded or not _pyncm_available():
        _env_cookies_loaded = True
        return
    cookie_path = get_settings().netease_cookie_path.strip()
    if not cookie_path:
        _env_cookies_loaded = True
        return
    path = Path(cookie_path).expanduser()
    if not path.is_file():
        _env_cookies_loaded = True
        return
    try:
        pyncm = importlib.import_module("pyncm")
        with path.open(encoding="utf-8") as f:
            cookies = json.load(f)
        pyncm.GetCurrentSession().cookies.update(cookies)
        logger.info("netease env cookies loaded", path=str(path))
    except Exception as exc:
        logger.warning("failed to load env netease cookies", error=str(exc))
    finally:
        _env_cookies_loaded = True


def run_with_netease_cookies(cookies: dict[str, Any] | None, fn: Callable[[], T]) -> T:
    """在临时注入 Cookie 的 pyncm Session 中执行同步调用。"""
    if not _pyncm_available():
        return fn()

    pyncm = importlib.import_module("pyncm")
    with _pyncm_lock:
        session = pyncm.GetCurrentSession()
        backup = session.cookies.get_dict()
        try:
            session.cookies.clear()
            if cookies:
                session.cookies.update(cookies)
            else:
                _load_env_cookies_if_needed()
            return fn()
        finally:
            session.cookies.clear()
            session.cookies.update(backup)
