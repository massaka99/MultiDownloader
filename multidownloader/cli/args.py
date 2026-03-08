"""Argument parsing for the CLI."""

from __future__ import annotations

import argparse

from .. import __version__
from ..core import DEFAULT_FRAGMENTS, DEFAULT_OUTPUT, DEFAULT_WORKERS, Mode

_MODE_ALIASES: dict[str, Mode] = {
    "v": "video",
    "video": "video",
    "a": "audio",
    "audio": "audio",
    "sound": "audio",
    "music": "audio",
    "b": "both",
    "both": "both",
}


def parse_mode(value: str) -> Mode:
    mode = _MODE_ALIASES.get(value.strip().lower())
    if mode:
        return mode
    raise argparse.ArgumentTypeError("Invalid mode. Use video/audio/both (or v/a/b).")


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Must be an integer.") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("Must be >= 1.")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="multi-downloader",
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
        type=parse_mode,
        metavar="{video|audio|both|v|a|b}",
        default="video",
        help="Download mode.",
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
        type=positive_int,
        default=DEFAULT_WORKERS,
        help="Concurrent download workers.",
    )
    parser.add_argument(
        "--fragments",
        type=positive_int,
        default=DEFAULT_FRAGMENTS,
        help="Concurrent fragment downloads.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Multi-Downloader {__version__}",
    )
    return parser
