"""Configuration objects and path resolution for downloads."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .paths import find_default_cookies, find_ffmpeg

Mode = Literal["video", "audio", "both"]

DEFAULT_OUTPUT = Path.home() / "Downloads"
DEFAULT_WORKERS = 3
DEFAULT_FRAGMENTS = 8


@dataclass(slots=True)
class DownloadConfig:
    mode: Mode
    output: Path
    cookies: Path | None
    cookies_explicit: bool = False
    workers: int = DEFAULT_WORKERS
    fragments: int = DEFAULT_FRAGMENTS
    ffmpeg_location: Path | None = None
    format_selector: str | None = None
    continue_download: bool = True


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def resolve_output_path(value: str | None) -> Path:
    target = value or str(DEFAULT_OUTPUT)
    output = Path(target).expanduser()
    ensure_output_dir(output)
    return output


def resolve_cookies(provided: str | None) -> Path | None:
    if provided:
        path = Path(provided).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Cookies file not found: {path}")
        return path
    return find_default_cookies()


def resolve_ffmpeg() -> Path | None:
    return find_ffmpeg()
