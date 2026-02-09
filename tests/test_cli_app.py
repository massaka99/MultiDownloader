from __future__ import annotations

import argparse
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from multidownloader.cli import app


class _FakeTTY(io.StringIO):
    def isatty(self) -> bool:
        return True


class _FakePipe(io.StringIO):
    def isatty(self) -> bool:
        return False


class TestCliApp(unittest.TestCase):
    def test_collect_urls_combines_sources_and_deduplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "urls.txt"
            path.write_text(
                "https://example.com/1\nhttps://example.com/2\nhttps://example.com/1\n",
                encoding="utf-8",
            )
            args = argparse.Namespace(
                input=str(path),
                urls=["https://example.com/2", "https://example.com/3"],
            )
            result = app._collect_urls(args, "https://example.com/4\n")
            self.assertEqual(
                result,
                [
                    "https://example.com/1",
                    "https://example.com/2",
                    "https://example.com/3",
                ],
            )

    def test_collect_urls_uses_stdin_when_no_other_source(self) -> None:
        args = argparse.Namespace(input=None, urls=[])
        result = app._collect_urls(args, "https://example.com/4\nhttps://example.com/4\n")
        self.assertEqual(result, ["https://example.com/4"])

    def test_collect_urls_missing_input_raises(self) -> None:
        args = argparse.Namespace(input="does-not-exist.txt", urls=[])
        with self.assertRaises(FileNotFoundError):
            app._collect_urls(args, None)

    def test_main_returns_2_when_no_urls(self) -> None:
        with (
            patch("multidownloader.cli.app.sys.stdin", _FakeTTY("")),
            patch("multidownloader.cli.app.prompt_urls", return_value=[]),
            patch("multidownloader.cli.app.print"),
        ):
            code = app.main([])
        self.assertEqual(code, 2)

    def test_main_returns_2_on_missing_cookies(self) -> None:
        with (
            patch("multidownloader.cli.app.sys.stdin", _FakePipe("")),
            patch("multidownloader.cli.app.resolve_cookies", side_effect=FileNotFoundError("missing")),
            patch("multidownloader.cli.app.print"),
        ):
            code = app.main(["https://example.com/1"])
        self.assertEqual(code, 2)

    def test_main_happy_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            with (
                patch("multidownloader.cli.app.sys.stdin", _FakePipe("")),
                patch("multidownloader.cli.app.resolve_cookies", return_value=None),
                patch("multidownloader.cli.app.resolve_ffmpeg", return_value=output / "ffmpeg.exe"),
                patch("multidownloader.cli.app.resolve_output_path", return_value=output),
                patch("multidownloader.cli.app.run_batch", return_value=[]) as run_batch,
                patch("multidownloader.cli.app.print"),
            ):
                code = app.main(["--mode", "audio", "https://example.com/1", "https://example.com/1"])

        self.assertEqual(code, 0)
        self.assertTrue(run_batch.called)
        urls_arg = run_batch.call_args[0][0]
        self.assertEqual(urls_arg, ["https://example.com/1"])
        config_arg = run_batch.call_args[0][1]
        self.assertEqual(config_arg.mode, "audio")
        self.assertEqual(config_arg.output, output)


if __name__ == "__main__":
    unittest.main()
