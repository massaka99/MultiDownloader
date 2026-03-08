"""Download orchestration built on yt-dlp."""

from __future__ import annotations

import concurrent.futures as futures
from dataclasses import replace
import shutil
from typing import Callable, Iterable

import yt_dlp
from yt_dlp.utils import DownloadError

from .config import DownloadConfig, ensure_output_dir
from .urls import unique_urls

Logger = Callable[[str], None]

_DEFAULT_AUDIO_SELECTOR = "bestaudio/best"
_DEFAULT_VIDEO_SELECTOR = "bv*+ba/b"


def _log(logger: Logger | None, message: str) -> None:
    (logger or print)(message)


def _audio_postprocessor() -> dict[str, str]:
    return {
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "320",
    }


def _detect_js_runtime() -> dict[str, dict]:
    deno = shutil.which("deno")
    if deno:
        return {"deno": {"path": deno}}
    node = shutil.which("node")
    if node:
        return {"node": {"path": node}}
    return {}


def _is_youtube_url(url: str) -> bool:
    lowered = url.lower()
    return "youtube.com/" in lowered or "youtu.be/" in lowered


def _has_ffmpeg(config: DownloadConfig) -> bool:
    if config.ffmpeg_location and config.ffmpeg_location.is_file():
        return True
    return shutil.which("ffmpeg") is not None


def build_options(config: DownloadConfig) -> dict:
    has_ffmpeg = _has_ffmpeg(config)
    options: dict = {
        "outtmpl": str(config.output / "%(title).200s [%(id)s].%(ext)s"),
        "paths": {"home": str(config.output)},
        "noplaylist": True,
        "no_warnings": False,
        "quiet": False,
        "retries": 5,
        "fragment_retries": 5,
        "extractor_retries": 5,
        "concurrent_fragment_downloads": config.fragments,
        "continuedl": config.continue_download,
        "ignoreerrors": False,
        "overwrites": False,
        "clean_infojson": True,
        "windowsfilenames": True,
        "trim_file_name": 200,
        "geo_bypass": True,
        "socket_timeout": 30,
    }

    if config.cookies:
        options["cookiefile"] = str(config.cookies)
    if config.ffmpeg_location:
        options["ffmpeg_location"] = str(config.ffmpeg_location)
    js_runtimes = _detect_js_runtime()
    if js_runtimes:
        options["js_runtimes"] = js_runtimes
        options["remote_components"] = ("ejs:github",)

    if config.mode == "audio":
        options["format"] = config.format_selector or _DEFAULT_AUDIO_SELECTOR
        if has_ffmpeg:
            options["postprocessors"] = [_audio_postprocessor()]
    elif config.mode == "both":
        options["format"] = config.format_selector or _DEFAULT_VIDEO_SELECTOR
        if has_ffmpeg:
            options["postprocessors"] = [_audio_postprocessor()]
            options["keepvideo"] = True
    else:
        options["format"] = config.format_selector or _DEFAULT_VIDEO_SELECTOR

    return options


def _attach_progress_hook(options: dict, logger: Logger | None) -> None:
    def _progress_hook(status: dict) -> None:
        if status.get("status") != "finished":
            return
        filename = status.get("filename") or status.get("info_dict", {}).get("_filename")
        if filename:
            _log(logger, f"[ok] Finished: {filename}")
        else:
            _log(logger, "[ok] Finished")

    options["progress_hooks"] = [_progress_hook]


def _download(url: str, mode_label: str, options: dict, logger: Logger | None) -> None:
    _attach_progress_hook(options, logger)
    with yt_dlp.YoutubeDL(options) as ydl:
        _log(logger, f"-> {mode_label} | {url}")
        ydl.download([url])


def download_single(url: str, config: DownloadConfig, logger: Logger | None) -> None:
    mode_label = {"video": "v", "audio": "a", "both": "b"}[config.mode]
    has_ffmpeg = _has_ffmpeg(config)
    if config.mode in {"audio", "both"} and not has_ffmpeg:
        _log(logger, "[warn] ffmpeg not found: downloading best available stream without conversion")
    if config.cookies and not config.cookies_explicit and _is_youtube_url(url):
        no_cookie_config = replace(config, cookies=None)
        try:
            _download(url, mode_label, build_options(no_cookie_config), logger)
            return
        except DownloadError:
            _log(logger, "[info] unauthenticated attempt failed, retrying with cookies")

    _download(url, mode_label, build_options(config), logger)


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
