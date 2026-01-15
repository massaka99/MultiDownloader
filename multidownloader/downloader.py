"""Download orchestration using yt-dlp."""

from __future__ import annotations

import concurrent.futures as futures
from typing import Callable, Iterable, List, Optional

import yt_dlp

from .config import DownloadConfig, ensure_output_dir

Logger = Callable[[str], None]


def _log(logger: Optional[Logger], message: str) -> None:
    (logger or print)(message)


def build_common_opts(config: DownloadConfig) -> dict:
    opts: dict = {
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
        "continuedl": config.continue_dl,
        "ignoreerrors": False,
        "overwrites": False,
        "clean_infojson": True,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0 Safari/537.36"
            )
        },
    }

    if config.cookies:
        opts["cookiefile"] = str(config.cookies)
    if config.ffmpeg_location:
        opts["ffmpeg_location"] = str(config.ffmpeg_location)
    return opts


def build_opts(config: DownloadConfig, download_type: str) -> dict:
    format_selector = config.format_selector or "bestvideo*+bestaudio/best"

    opts = build_common_opts(config)
    if download_type == "audio":
        opts.update(
            {
                "format": config.format_selector or "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "320",
                    }
                ],
            }
        )
    elif download_type == "video":
        opts.update({"format": format_selector})
    else:
        opts.update(
            {
                "format": format_selector,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "320",
                    }
                ],
                "keepvideo": True,
            }
        )
    return opts


def download_single(url: str, config: DownloadConfig, logger: Optional[Logger]) -> None:
    opts = build_opts(config, config.download_type)

    def _progress_hook(status: dict) -> None:
        if status.get("status") == "finished":
            _log(logger, f"[ok] Finished: {status.get('filename')}")

    opts["progress_hooks"] = [_progress_hook]

    label_map = {"video": "v", "audio": "a", "both": "b"}
    label = label_map.get(config.download_type, config.download_type)
    with yt_dlp.YoutubeDL(opts) as ydl:
        _log(logger, f"-> {label} | {url}")
        ydl.download([url])


def run_batch(urls: Iterable[str], config: DownloadConfig, logger: Optional[Logger] = None) -> List[str]:
    urls = list(urls)
    if not urls:
        _log(logger, "No URLs provided. Exiting.")
        return []

    ensure_output_dir(config.output)
    worker_count = max(1, min(config.workers, len(urls)))
    _log(
        logger,
        f"Downloading {len(urls)} item(s) to '{config.output}' using {worker_count} worker(s)...",
    )

    errors: List[str] = []
    with futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_map = {executor.submit(download_single, url, config, logger): url for url in urls}
        for future in futures.as_completed(future_map):
            url = future_map[future]
            try:
                future.result()
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{url}: {exc}")
                _log(logger, f"[error] {url}\n        {exc}")

    if errors:
        _log(logger, "Completed with some errors.")
    else:
        _log(logger, "All downloads completed successfully.")
    return errors


def load_urls_from_text(text: str) -> List[str]:
    lines = [line.strip() for line in text.splitlines()]
    seen = set()
    urls: List[str] = []
    for line in lines:
        if not line or line.lstrip().startswith("#"):
            continue
        if line not in seen:
            seen.add(line)
            urls.append(line)
    return urls
