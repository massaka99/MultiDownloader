"""CLI application orchestration."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from ..core import DownloadConfig, parse_urls, resolve_cookies, resolve_ffmpeg, resolve_output_path, run_batch, unique_urls
from .args import build_parser


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

    stdin_text = None if sys.stdin.isatty() else sys.stdin.read()

    try:
        urls = _collect_urls(args, stdin_text)
    except FileNotFoundError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"[error] Failed to read input file: {exc}", file=sys.stderr)
        return 2

    if not urls:
        print("[error] No URLs provided.", file=sys.stderr)
        parser.print_help()
        return 2

    try:
        cookies_path = resolve_cookies(args.cookies)
    except FileNotFoundError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    config = DownloadConfig(
        mode=args.mode,
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
    return 1 if errors else 0
