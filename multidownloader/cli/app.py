"""CLI application orchestration."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from ..core import DownloadConfig, parse_urls, resolve_cookies, resolve_ffmpeg, resolve_output_path, run_batch, unique_urls
from .args import build_parser
from .interactive import prompt_mode, prompt_urls


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _collect_urls(args: argparse.Namespace, stdin_text: str | None) -> list[str]:
    candidates: list[str] = []

    if args.input:
        path = Path(args.input).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Input file not found: {path}")
        candidates.extend(parse_urls(_read_text(path)))

    if args.urls:
        candidates.extend(args.urls)

    if not candidates and stdin_text:
        candidates.extend(parse_urls(stdin_text))

    return unique_urls(candidates)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    stdin_is_tty = sys.stdin.isatty()
    stdin_text = None if stdin_is_tty else sys.stdin.read()
    interactive = stdin_is_tty and not args.urls and not args.input

    try:
        urls = _collect_urls(args, stdin_text)
    except FileNotFoundError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"[error] Failed to read input file: {exc}", file=sys.stderr)
        return 2

    if interactive and not urls:
        urls = prompt_urls()

    if not urls:
        print("[error] No URLs provided.", file=sys.stderr)
        parser.print_help()
        if interactive:
            input("Press Enter to exit...")
        return 2

    mode = args.mode or ("video" if not interactive else prompt_mode())
    try:
        cookies_path = resolve_cookies(args.cookies)
    except FileNotFoundError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        if interactive:
            input("Press Enter to exit...")
        return 2

    config = DownloadConfig(
        mode=mode,
        output=resolve_output_path(args.output),
        cookies=cookies_path,
        cookies_explicit=bool(args.cookies),
        workers=args.workers,
        fragments=args.fragments,
        ffmpeg_location=resolve_ffmpeg(),
    )

    if not config.ffmpeg_location:
        print("[warn] ffmpeg not found. Some formats may fail.")

    errors = run_batch(urls, config, logger=print)
    if interactive:
        input("Press Enter to exit...")
    return 1 if errors else 0
