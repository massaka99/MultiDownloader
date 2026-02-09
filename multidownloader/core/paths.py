"""Runtime path helpers for source and packaged execution."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

_FFMPEG_ENV_VARS = ("MULTIDOWNLOADER_FFMPEG", "FFMPEG_PATH")
_FFMPEG_BINARY_NAMES = ("ffmpeg.exe", "ffmpeg") if os.name == "nt" else ("ffmpeg", "ffmpeg.exe")


def runtime_root() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[2]


def resolve_resource(name: str) -> Path:
    return runtime_root() / name


def find_default_cookies() -> Path | None:
    for candidate in _cookie_candidates():
        if candidate.is_file():
            return candidate
    return None


def _cookie_candidates() -> list[Path]:
    candidates = [resolve_resource("cookies.txt"), Path.cwd() / "cookies.txt"]
    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate.resolve(strict=False))
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def find_ffmpeg() -> Path | None:
    for env_name in _FFMPEG_ENV_VARS:
        configured = os.getenv(env_name)
        if configured:
            resolved = _resolve_ffmpeg_candidate(Path(configured).expanduser())
            if resolved:
                return resolved

    root = runtime_root()
    for binary in _FFMPEG_BINARY_NAMES:
        candidates = (
            root / binary,
            root / "bin" / binary,
            root / "ffmpeg" / "bin" / binary,
        )
        for candidate in candidates:
            if candidate.is_file():
                return candidate

    which = shutil.which("ffmpeg")
    if which:
        return Path(which)
    return None


def _resolve_ffmpeg_candidate(candidate: Path) -> Path | None:
    if candidate.is_file():
        return candidate
    if candidate.is_dir():
        for binary in _FFMPEG_BINARY_NAMES:
            exe = candidate / binary
            if exe.is_file():
                return exe
    return None
