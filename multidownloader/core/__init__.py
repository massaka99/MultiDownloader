"""Core domain logic for Multi-Downloader."""

from .config import (
    DEFAULT_FRAGMENTS,
    DEFAULT_OUTPUT,
    DEFAULT_WORKERS,
    DownloadConfig,
    Mode,
    ensure_output_dir,
    resolve_cookies,
    resolve_ffmpeg,
    resolve_output_path,
)
from .downloader import run_batch
from .urls import parse_urls, unique_urls

__all__ = [
    "DEFAULT_FRAGMENTS",
    "DEFAULT_OUTPUT",
    "DEFAULT_WORKERS",
    "DownloadConfig",
    "Mode",
    "ensure_output_dir",
    "parse_urls",
    "resolve_cookies",
    "resolve_ffmpeg",
    "resolve_output_path",
    "run_batch",
    "unique_urls",
]
