"""CLI package entrypoints."""

from .app import main
from .args import build_parser

__all__ = ["build_parser", "main"]
