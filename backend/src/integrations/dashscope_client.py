"""阿里云百炼 DashScope HTTP 客户端（OpenAI 兼容模式）。"""

from __future__ import annotations

import json
from typing import Any, cast

import httpx
from src.core.config import AppSettings, get_settings

from pycore.core.logger import get_logger

logger = get_logger()


class DashScopeError(Exception):
    """百炼 API 调用失败。"""


def is_mock_key(api_key: str) -> bool:
    if not api_key or len(api_key) < 8:
        return True
    lowered = api_key.strip().lower()
    if lowered in {"your-dashscope-api-key", "test-key", "test-key-placeholder"}:
        return True
    return lowered.startswith("test-") or "placeholder" in lowered


class DashScopeClient:
    def __init__(self, settings: AppSettings | None = None, *, force_mock: bool = False) -> None:
        self._settings = settings or get_settings()
        self._force_mock = force_mock
        self._base_url = self._settings.llm_base_url.rstrip("/")

    @property
    def use_mock(self) -> bool:
        return self._force_mock or is_mock_key(self._settings.dashscope_api_key)

    def _auth_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._settings.dashscope_api_key}",
            "Content-Type": "application/json",
        }

    async def _post_json(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(trust_env=False, timeout=60.0) as client:
            response = await client.post(url, headers=self._auth_headers(), json=payload)
        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            raise DashScopeError(f"Invalid JSON response (HTTP {response.status_code})") from exc

        if response.status_code >= 400:
            message = data.get("message") or data.get("error", {}).get("message") or response.text
            raise DashScopeError(f"DashScope HTTP {response.status_code}: {message}")

        return cast(dict[str, Any], data)

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        if self.use_mock:
            logger.warning("DashScope chat_completion using mock fallback")
            return messages[-1]["content"] if messages else ""

        payload = {
            "model": model or self._settings.llm_model_chat,
            "messages": messages,
            "temperature": temperature,
        }
        data = await self._post_json(f"{self._base_url}/chat/completions", payload)
        try:
            return str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise DashScopeError("Failed to parse chat completion response") from exc

    async def generate(self, prompt: str, *, temperature: float = 0.7) -> str:
        return await self.chat_completion(
            [{"role": "user", "content": prompt}],
            temperature=temperature,
        )


def get_dashscope_client() -> DashScopeClient:
    return DashScopeClient()
