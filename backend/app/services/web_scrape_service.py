from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from app.config import get_settings

try:
    from scrapling import Fetcher

    SCRAPLING_AVAILABLE = True
except Exception:  # pragma: no cover
    Fetcher = None
    SCRAPLING_AVAILABLE = False


def _clean_text(value: Any, limit: int = 2400) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}..."


def _is_supported_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _extract_headings(response: Any) -> list[str]:
    headings: list[str] = []
    for tag in ("h1", "h2"):
        try:
            nodes = response.find_all(tag) or []
        except Exception:
            nodes = []
        for node in nodes[:3]:
            text = _clean_text(getattr(node, "text", ""), limit=120)
            if text and text not in headings:
                headings.append(text)
    return headings[:5]


def scrape_page_snapshot(url: str, timeout_seconds: int | None = None) -> dict[str, Any]:
    if not SCRAPLING_AVAILABLE:
        return {"url": url, "error": "scrapling_unavailable"}

    if not _is_supported_url(url):
        return {"url": url, "error": "unsupported_url"}

    settings = get_settings()
    fetcher = Fetcher()
    fetcher.configure(auto_match=False)

    try:
        response = fetcher.get(url, timeout=timeout_seconds or settings.live_research_timeout_seconds)
        title = ""
        try:
            title_node = response.find("title")
            title = _clean_text(getattr(title_node, "text", ""), limit=180) if title_node else ""
        except Exception:
            title = ""

        text_excerpt = _clean_text(response.get_all_text(separator=" ", strip=True))
        payload = {
            "url": url,
            "final_url": str(getattr(response, "url", url)),
            "title": title or None,
            "headings": _extract_headings(response),
            "text_excerpt": text_excerpt,
        }
        return payload
    except Exception as exc:
        return {"url": url, "error": str(exc)}
