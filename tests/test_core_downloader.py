from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from yt_dlp.utils import DownloadError

from multidownloader.core.config import DownloadConfig
from multidownloader.core.downloader import build_options, download_single


class _SpyYDL:
    init_calls = 0
    formats_seen: list[str | None] = []
    cookies_seen: list[str | None] = []

    def __init__(self, options: dict) -> None:
        type(self).init_calls += 1
        type(self).formats_seen.append(options.get("format"))
        type(self).cookies_seen.append(options.get("cookiefile"))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def download(self, urls: list[str]) -> None:
        _ = urls


class _FailWithoutCookiesYDL:
    cookiefiles_seen: list[str | None] = []

    def __init__(self, options: dict) -> None:
        self._cookie = options.get("cookiefile")
        type(self).cookiefiles_seen.append(self._cookie)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def download(self, urls: list[str]) -> None:
        _ = urls
        if not self._cookie:
            raise DownloadError("sign in required")


class TestCoreDownloader(unittest.TestCase):
    def test_build_options_video_sets_default_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = DownloadConfig(mode="video", output=Path(tmp), cookies=None)
            with patch("multidownloader.core.downloader.shutil.which", return_value=None):
                options = build_options(config)
        self.assertNotIn("extractor_args", options)
        self.assertEqual(options.get("format"), "bv*+ba/b")
        self.assertNotIn("js_runtimes", options)
        self.assertNotIn("remote_components", options)

    def test_build_options_audio_sets_audio_selector(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ffmpeg = Path(tmp) / "ffmpeg.exe"
            ffmpeg.write_text("binary", encoding="utf-8")
            config = DownloadConfig(mode="audio", output=Path(tmp), cookies=None, ffmpeg_location=ffmpeg)
            with patch("multidownloader.core.downloader.shutil.which", return_value=None):
                options = build_options(config)
        self.assertEqual(options.get("format"), "bestaudio/best")
        self.assertEqual(options.get("postprocessors", [{}])[0].get("key"), "FFmpegExtractAudio")

    def test_build_options_prefers_deno_then_node_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = DownloadConfig(mode="video", output=Path(tmp), cookies=None)
            with (
                patch("multidownloader.core.downloader._has_ffmpeg", return_value=True),
                patch("multidownloader.core.downloader.shutil.which", side_effect=["C:\\deno.exe", "C:\\node.exe"]),
            ):
                options = build_options(config)
        self.assertEqual(options.get("js_runtimes"), {"deno": {"path": "C:\\deno.exe"}})
        self.assertEqual(options.get("remote_components"), ("ejs:github",))

    def test_build_options_uses_node_runtime_when_deno_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = DownloadConfig(mode="video", output=Path(tmp), cookies=None)
            with (
                patch("multidownloader.core.downloader._has_ffmpeg", return_value=True),
                patch("multidownloader.core.downloader.shutil.which", side_effect=[None, "C:\\node.exe"]),
            ):
                options = build_options(config)
        self.assertEqual(options.get("js_runtimes"), {"node": {"path": "C:\\node.exe"}})
        self.assertEqual(options.get("remote_components"), ("ejs:github",))

    def test_download_single_runs_one_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = DownloadConfig(mode="video", output=Path(tmp), cookies=None)
            _SpyYDL.init_calls = 0
            _SpyYDL.formats_seen = []
            _SpyYDL.cookies_seen = []
            with (
                patch("multidownloader.core.downloader.yt_dlp.YoutubeDL", _SpyYDL),
                patch("multidownloader.core.downloader.shutil.which", return_value=None),
            ):
                download_single("https://example.com/video", config, logger=None)

        self.assertEqual(_SpyYDL.init_calls, 1)
        self.assertEqual(_SpyYDL.formats_seen, ["bv*+ba/b"])
        self.assertEqual(_SpyYDL.cookies_seen, [None])

    def test_download_single_youtube_auto_cookie_tries_without_cookie_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = DownloadConfig(
                mode="video",
                output=Path(tmp),
                cookies=Path("cookies.txt"),
                cookies_explicit=False,
            )
            _SpyYDL.init_calls = 0
            _SpyYDL.cookies_seen = []
            with (
                patch("multidownloader.core.downloader.yt_dlp.YoutubeDL", _SpyYDL),
                patch("multidownloader.core.downloader.shutil.which", return_value=None),
            ):
                download_single("https://www.youtube.com/watch?v=abc", config, logger=None)

        self.assertEqual(_SpyYDL.init_calls, 1)
        self.assertEqual(_SpyYDL.cookies_seen, [None])

    def test_download_single_youtube_explicit_cookie_uses_cookie_directly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = DownloadConfig(
                mode="video",
                output=Path(tmp),
                cookies=Path("cookies.txt"),
                cookies_explicit=True,
            )
            _SpyYDL.init_calls = 0
            _SpyYDL.cookies_seen = []
            with (
                patch("multidownloader.core.downloader.yt_dlp.YoutubeDL", _SpyYDL),
                patch("multidownloader.core.downloader.shutil.which", return_value=None),
            ):
                download_single("https://www.youtube.com/watch?v=abc", config, logger=None)

        self.assertEqual(_SpyYDL.init_calls, 1)
        self.assertEqual(_SpyYDL.cookies_seen, ["cookies.txt"])

    def test_download_single_youtube_auto_cookie_falls_back_to_cookie_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = DownloadConfig(
                mode="video",
                output=Path(tmp),
                cookies=Path("cookies.txt"),
                cookies_explicit=False,
            )
            _FailWithoutCookiesYDL.cookiefiles_seen = []
            with (
                patch("multidownloader.core.downloader.yt_dlp.YoutubeDL", _FailWithoutCookiesYDL),
                patch("multidownloader.core.downloader.shutil.which", return_value=None),
            ):
                download_single("https://www.youtube.com/watch?v=abc", config, logger=None)

        self.assertEqual(_FailWithoutCookiesYDL.cookiefiles_seen, [None, "cookies.txt"])


if __name__ == "__main__":
    unittest.main()
