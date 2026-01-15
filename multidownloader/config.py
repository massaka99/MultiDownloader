"""Configuration and defaults."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .paths import find_default_cookies, find_ffmpeg

DEFAULT_OUTPUT = Path.home() / "Downloads"
DEFAULT_WORKERS = 3
DEFAULT_FRAGMENTS = 8


@dataclass
class DownloadConfig:
    download_type: str
    output: Path
    cookies: Optional[Path]
    format_selector: Optional[str]
    continue_dl: bool
    workers: int = DEFAULT_WORKERS
    fragments: int = DEFAULT_FRAGMENTS
    ffmpeg_location: Optional[Path] = None


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def resolve_output_path(value: str) -> Path:
    target = value or str(DEFAULT_OUTPUT)
    output = Path(target).expanduser()
    ensure_output_dir(output)
    return output


def resolve_cookies(provided: Optional[str]) -> Optional[Path]:
    if provided:
        path = Path(provided).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Cookies file not found: {path}")
        return path
    return find_default_cookies()


def resolve_ffmpeg() -> Optional[Path]:
    return find_ffmpeg()
