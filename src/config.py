from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None


def _load_env(project_root: str | Path = ".") -> None:
    if load_dotenv:
        load_dotenv(Path(project_root) / ".env")


def normalize_openrouter_model(model: str | None) -> str:
    value = (model or "deepseek/deepseek-chat").strip()
    if value.startswith("openrouter/"):
        value = value.removeprefix("openrouter/")
    if value.startswith("~"):
        value = value[1:]
    return value


def ascii_header_value(value: str | None, fallback: str) -> str:
    """httpx requires header values to be ASCII encodable."""
    clean = (value or "").strip()
    if not clean:
        return fallback
    try:
        clean.encode("ascii")
    except UnicodeEncodeError:
        return fallback
    return clean


@dataclass
class Settings:
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "deepseek/deepseek-chat"
    openrouter_http_referer: str = "http://localhost:8501"
    openrouter_app_title: str = "Mayuan Question Generator"
    temperature: float = 0.35
    max_tokens: int = 4096

    @classmethod
    def from_env(cls, project_root: str | Path = ".") -> "Settings":
        _load_env(project_root)
        model = os.getenv("OPENROUTER_MODEL") or "deepseek/deepseek-chat"
        return cls(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
            openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            openrouter_model=normalize_openrouter_model(model),
            openrouter_http_referer=ascii_header_value(
                os.getenv("OPENROUTER_HTTP_REFERER", os.getenv("OPENROUTER_SITE_URL")),
                "http://localhost:8501",
            ),
            openrouter_app_title=ascii_header_value(
                os.getenv("OPENROUTER_APP_TITLE", os.getenv("OPENROUTER_SITE_NAME")),
                "Mayuan Question Generator",
            ),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.35")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
        )
