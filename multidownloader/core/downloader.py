"""Download orchestration built on yt-dlp."""

from __future__ import annotations

import concurrent.futures as futures
from typing import Callable, Iterable

import yt_dlp

from .config import DownloadConfig, ensure_output_dir
from .urls import unique_urls

Logger = Callable[[str], None]

_DEFAULT_VIDEO_SELECTOR = "bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]"
_DEFAULT_AUDIO_SELECTOR = "bestaudio/best"
_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36"
)


def _log(logger: Logger | None, message: str) -> None:
    (logger or print)(message)


def _audio_postprocessor() -> dict[str, str]:
    return {
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "320",
    }


def build_options(config: DownloadConfig) -> dict:
    options: dict = {
        "outtmpl": str(config.output / "%(title).200s [%(id)s].%(ext)s"),
        "paths": {"home": str(config.output)},
        "noplaylist": True,
        "merge_output_format": "mp4",
        "nocheckcertificate": True,
        "no_warnings": False,
        "quiet": False,
        "retries": 5,
        "fragment_retries": 5,
        "concurrent_fragment_downloads": config.fragments,
        "continuedl": config.continue_download,
        "ignoreerrors": False,
        "overwrites": False,
        "clean_infojson": True,
        "http_headers": {"User-Agent": _BROWSER_USER_AGENT},
    }

    if config.cookies:
        options["cookiefile"] = str(config.cookies)
    if config.ffmpeg_location:
        options["ffmpeg_location"] = str(config.ffmpeg_location)

    format_selector = config.format_selector or _DEFAULT_VIDEO_SELECTOR
    if config.mode == "audio":
        options["format"] = config.format_selector or _DEFAULT_AUDIO_SELECTOR
        options["postprocessors"] = [_audio_postprocessor()]
    elif config.mode == "both":
        options["format"] = format_selector
        options["postprocessors"] = [_audio_postprocessor()]
        options["keepvideo"] = True
    else:
        options["format"] = format_selector

    return options


def download_single(url: str, config: DownloadConfig, logger: Logger | None) -> None:
    options = build_options(config)

    def _progress_hook(status: dict) -> None:
        if status.get("status") != "finished":
            return
        filename = status.get("filename") or status.get("info_dict", {}).get("_filename")
        if filename:
            _log(logger, f"[ok] Finished: {filename}")
        else:
            _log(logger, "[ok] Finished")

    options["progress_hooks"] = [_progress_hook]

    mode_label = {"video": "v", "audio": "a", "both": "b"}[config.mode]
    with yt_dlp.YoutubeDL(options) as ydl:
        _log(logger, f"-> {mode_label} | {url}")
        ydl.download([url])


def run_batch(urls: Iterable[str], config: DownloadConfig, logger: Logger | None = None) -> list[str]:
    items = unique_urls(urls)
    if not items:
        _log(logger, "No URLs provided. Exiting.")
        return []

    ensure_output_dir(config.output)
    worker_count = max(1, min(config.workers, len(items)))
    _log(
        logger,
        f"Downloading {len(items)} item(s) to '{config.output}' using {worker_count} worker(s)...",
    )

    errors: list[str] = []
    with futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_map = {executor.submit(download_single, url, config, logger): url for url in items}
        for future in futures.as_completed(future_map):
            url = future_map[future]
            try:
                future.result()
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{url}: {exc}")
                _log(logger, f"[error] {url}\n        {exc}")

    successful = len(items) - len(errors)
    if errors:
        _log(logger, f"Completed with errors ({successful}/{len(items)} succeeded).")
    else:
        _log(logger, "All downloads completed successfully.")
    return errors
