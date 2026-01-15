"""Path helpers for packaged and source runs."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional


def app_root() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[1]


def resolve_resource(name: str) -> Path:
    return app_root() / name


def find_default_cookies() -> Optional[Path]:
    candidate = resolve_resource("cookies.txt")
    if candidate.is_file():
        return candidate
    return None


def find_ffmpeg() -> Optional[Path]:
    env_path = os.getenv("MULTIDOWNLOADER_FFMPEG") or os.getenv("FFMPEG_PATH")
    if env_path:
        candidate = Path(env_path).expanduser()
        if candidate.is_dir():
            exe = candidate / "ffmpeg.exe"
            if exe.is_file():
                return exe
        elif candidate.is_file():
            return candidate

    root = app_root()
    candidates = [
        root / "ffmpeg.exe",
        root / "bin" / "ffmpeg.exe",
        root / "ffmpeg" / "bin" / "ffmpeg.exe",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None
