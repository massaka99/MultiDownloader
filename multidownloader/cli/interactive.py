"""Interactive prompts for CLI mode."""

from __future__ import annotations

import argparse

from ..core import Mode, parse_urls
from .args import parse_mode


def prompt_urls() -> list[str]:
    print("Paste URLs (one per line). Submit an empty line to start.")
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not line.strip():
            break
        lines.append(line)
    return parse_urls("\n".join(lines))


def prompt_mode(default: Mode = "video") -> Mode:
    while True:
        raw_value = input("Choose mode (v/a/b) [v]: ").strip()
        if not raw_value:
            return default
        try:
            return parse_mode(raw_value)
        except argparse.ArgumentTypeError:
            print("Invalid choice. Enter v, a, or b.")
