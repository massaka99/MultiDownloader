"""Settings storage for Multi-Downloader."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

from .paths import app_root

_ALLOWED_KEYS = {
    "theme",
    "output",
    "cookies",
}


def _settings_dir() -> Path:
    base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
    if base:
        return Path(base) / "MultiDownloader"
    return Path.home() / "AppData" / "Local" / "MultiDownloader"


def settings_path() -> Path:
    return _settings_dir() / "settings.json"


def _is_embedded_cookies(value: str) -> bool:
    try:
        path = Path(value).expanduser().resolve()
    except Exception:
        return False
    if path.name.lower() != "cookies.txt":
        return False
    try:
        root = app_root().resolve()
    except Exception:
        return False
    return root in path.parents


def _sanitize(payload: Dict[str, Any]) -> Dict[str, str]:
    cleaned: Dict[str, str] = {}
    for key, value in payload.items():
        if key not in _ALLOWED_KEYS:
            continue
        if value is None:
            continue
        text = str(value).strip()
        if not text:
            continue
        if key == "theme" and text not in ("light", "dark"):
            continue
        if key == "cookies":
            path = Path(text).expanduser()
            if not path.is_file():
                continue
            if _is_embedded_cookies(text):
                continue
        cleaned[key] = text
    return cleaned


def load_settings() -> Dict[str, Any]:
    path = settings_path()
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_settings(updates: Dict[str, Any]) -> Dict[str, Any]:
    current = load_settings()
    cleaned = _sanitize(updates)
    if not cleaned:
        return current

    current.update(cleaned)
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(current, indent=2, ensure_ascii=True), encoding="utf-8")
    return current
