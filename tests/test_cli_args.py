from __future__ import annotations

import argparse
import unittest

from multidownloader.cli.args import build_parser, parse_mode, positive_int


class TestCliArgs(unittest.TestCase):
    def test_parse_mode_aliases(self) -> None:
        self.assertEqual(parse_mode("video"), "video")
        self.assertEqual(parse_mode("v"), "video")
        self.assertEqual(parse_mode("audio"), "audio")
        self.assertEqual(parse_mode("a"), "audio")
        self.assertEqual(parse_mode("music"), "audio")
        self.assertEqual(parse_mode("both"), "both")
        self.assertEqual(parse_mode("b"), "both")

    def test_parse_mode_invalid(self) -> None:
        with self.assertRaises(argparse.ArgumentTypeError):
            parse_mode("invalid")

    def test_positive_int_valid(self) -> None:
        self.assertEqual(positive_int("1"), 1)
        self.assertEqual(positive_int("99"), 99)

    def test_positive_int_invalid(self) -> None:
        with self.assertRaises(argparse.ArgumentTypeError):
            positive_int("0")
        with self.assertRaises(argparse.ArgumentTypeError):
            positive_int("-4")
        with self.assertRaises(argparse.ArgumentTypeError):
            positive_int("x")

    def test_parser_mode_normalization(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--mode", "a", "https://example.com"])
        self.assertEqual(args.mode, "audio")
        self.assertEqual(args.urls, ["https://example.com"])

    def test_parser_default_mode_is_video(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["https://example.com"])
        self.assertEqual(args.mode, "video")


if __name__ == "__main__":
    unittest.main()
