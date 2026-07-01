from __future__ import annotations

import json
from urllib.error import HTTPError
import urllib.request

from .config import ascii_header_value
from .config import Settings


class OpenRouterClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def chat(self, messages, temperature: float | None = None, max_tokens: int | None = None) -> str:
        if not self.settings.openrouter_api_key:
            raise RuntimeError("未配置 OPENROUTER_API_KEY。请在侧边栏或 .env 中填写。")
        payload_messages = messages if isinstance(messages, list) else [{"role": "user", "content": str(messages)}]
        temperature = self.settings.temperature if temperature is None else temperature
        max_tokens = self.settings.max_tokens if max_tokens is None else max_tokens
        return self._chat_with_urllib(payload_messages, temperature, max_tokens)

    def _headers(self) -> dict[str, str]:
        return {
            "HTTP-Referer": ascii_header_value(self.settings.openrouter_http_referer, "http://localhost:8501"),
            "X-OpenRouter-Title": ascii_header_value(
                self.settings.openrouter_app_title,
                "Mayuan Question Generator",
            ),
        }

    def _chat_with_urllib(self, messages, temperature: float, max_tokens: int) -> str:
        body = json.dumps(
            {
                "model": self.settings.openrouter_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        headers = self._ascii_headers(
            {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "Content-Type": "application/json",
            **self._headers(),
            }
        )
        request = urllib.request.Request(
            f"{self.settings.openrouter_base_url.rstrip('/')}/chat/completions",
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenRouter 请求失败：HTTP {exc.code} {detail}") from exc
        return data["choices"][0]["message"]["content"]

    def _ascii_headers(self, headers: dict[str, str]) -> dict[str, str]:
        safe: dict[str, str] = {}
        for key, value in headers.items():
            safe_key = ascii_header_value(key, "")
            safe_value = ascii_header_value(value, "")
            if safe_key and safe_value:
                safe[safe_key] = safe_value
        return safe
