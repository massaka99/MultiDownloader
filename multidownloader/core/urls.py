"""URL parsing and deduplication helpers."""

from __future__ import annotations

from typing import Iterable


def parse_urls(text: str) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line not in seen:
            seen.add(line)
            urls.append(line)
    return urls


def unique_urls(urls: Iterable[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for url in urls:
        value = url.strip()
        if not value or value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique
