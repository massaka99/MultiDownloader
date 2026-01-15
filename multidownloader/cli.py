"""Command-line interface for Multi-Downloader."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List, Optional

from .config import (
    DEFAULT_FRAGMENTS,
    DEFAULT_OUTPUT,
    DEFAULT_WORKERS,
    DownloadConfig,
    resolve_cookies,
    resolve_ffmpeg,
    resolve_output_path,
)
from .downloader import load_urls_from_text, run_batch
from .paths import find_default_cookies


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _merge_urls(urls: Iterable[str], seen: set[str], out: List[str]) -> None:
    for url in urls:
        if url and url not in seen:
            seen.add(url)
            out.append(url)


def _collect_urls(args: argparse.Namespace) -> List[str]:
    seen: set[str] = set()
    collected: List[str] = []

    if args.input:
        path = Path(args.input).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Input file not found: {path}")
        _merge_urls(load_urls_from_text(_read_text(path)), seen, collected)

    if args.urls:
        _merge_urls(args.urls, seen, collected)

    if not collected and not sys.stdin.isatty():
        _merge_urls(load_urls_from_text(sys.stdin.read()), seen, collected)

    return collected


def _prompt_urls() -> List[str]:
    print("Paste URLs (one per line). Submit an empty line to start.")
    lines: List[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not line.strip():
            break
        lines.append(line)
    return load_urls_from_text("\n".join(lines))


def _normalize_mode(value: str) -> Optional[str]:
    lowered = value.strip().lower()
    if lowered in ("v", "video"):
        return "video"
    if lowered in ("a", "audio", "sound", "music"):
        return "audio"
    if lowered in ("b", "both"):
        return "both"
    return None


def _prompt_mode(default: str = "video") -> str:
    while True:
        choice = input("Choose mode (v/a/b) [v]: ").strip()
        if not choice:
            return default
        normalized = _normalize_mode(choice)
        if normalized:
            return normalized
        print("Invalid choice. Enter v, a, or b.")


def _resolve_cookies(args: argparse.Namespace) -> Optional[Path]:
    if args.cookies:
        return resolve_cookies(args.cookies)
    default_cookies = find_default_cookies()
    if default_cookies:
        return default_cookies
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Multi-Downloader (CLI)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("urls", nargs="*", help="One or more URLs to download.")
    parser.add_argument(
        "-i",
        "--input",
        help="Path to a text file containing URLs (one per line).",
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=("video", "audio", "both", "v", "a", "b"),
        help="Download mode (video/audio/both or v/a/b).",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Output directory.",
    )
    parser.add_argument(
        "-c",
        "--cookies",
        help="Path to cookies.txt (optional).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help="Concurrent download workers.",
    )
    parser.add_argument(
        "--fragments",
        type=int,
        default=DEFAULT_FRAGMENTS,
        help="Concurrent fragment downloads.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        urls = _collect_urls(args)
    except FileNotFoundError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    interactive = sys.stdin.isatty() and not args.urls and not args.input
    if not urls and interactive:
        urls = _prompt_urls()

    if not urls:
        print("[error] No URLs provided.", file=sys.stderr)
        parser.print_help()
        return 2

    mode = _normalize_mode(args.mode) if args.mode else None
    if not mode:
        mode = "video" if not interactive else _prompt_mode()

    try:
        cookies_path = _resolve_cookies(args)
    except FileNotFoundError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    output_path = resolve_output_path(args.output)
    ffmpeg_path = resolve_ffmpeg()

    config = DownloadConfig(
        download_type=mode,
        output=output_path,
        cookies=cookies_path,
        format_selector=None,
        continue_dl=True,
        workers=args.workers,
        fragments=args.fragments,
        ffmpeg_location=ffmpeg_path,
    )

    def logger(message: str) -> None:
        print(message)

    if config.cookies:
        logger(f"[info] cookies: {config.cookies}")
    if not config.ffmpeg_location:
        logger("[warn] ffmpeg.exe not found. Some formats may fail.")

    errors = run_batch(urls, config, logger=logger)
    if interactive:
        input("Press Enter to exit...")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
