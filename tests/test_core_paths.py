from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from multidownloader.core import paths


class TestCorePaths(unittest.TestCase):
    def test_find_default_cookies_from_runtime_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cookie = root / "cookies.txt"
            cookie.write_text("cookie-data", encoding="utf-8")
            with patch("multidownloader.core.paths.runtime_root", return_value=root):
                resolved = paths.find_default_cookies()
            self.assertEqual(resolved, cookie)

    def test_find_default_cookies_from_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as root_tmp, tempfile.TemporaryDirectory() as cwd_tmp:
            root = Path(root_tmp)
            cwd = Path(cwd_tmp)
            cookie = cwd / "cookies.txt"
            cookie.write_text("cookie-data", encoding="utf-8")
            old_cwd = Path.cwd()
            try:
                os.chdir(cwd)
                with patch("multidownloader.core.paths.runtime_root", return_value=root):
                    resolved = paths.find_default_cookies()
            finally:
                os.chdir(old_cwd)
            self.assertEqual(resolved, cookie)

    def test_find_ffmpeg_from_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ffmpeg = Path(tmp) / "ffmpeg.exe"
            ffmpeg.write_text("binary", encoding="utf-8")
            with patch.dict(os.environ, {"MULTIDOWNLOADER_FFMPEG": str(ffmpeg)}, clear=False):
                resolved = paths.find_ffmpeg()
            self.assertEqual(resolved, ffmpeg)

    def test_find_ffmpeg_from_runtime_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ffmpeg_name = paths._FFMPEG_BINARY_NAMES[0]
            ffmpeg = root / ffmpeg_name
            ffmpeg.write_text("binary", encoding="utf-8")
            with (
                patch.dict(os.environ, {"MULTIDOWNLOADER_FFMPEG": "", "FFMPEG_PATH": ""}, clear=False),
                patch("multidownloader.core.paths.runtime_root", return_value=root),
                patch("multidownloader.core.paths.shutil.which", return_value=None),
            ):
                resolved = paths.find_ffmpeg()
            self.assertEqual(resolved, ffmpeg)

    def test_find_ffmpeg_from_path_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ffmpeg = Path(tmp) / "ffmpeg.exe"
            ffmpeg.write_text("binary", encoding="utf-8")
            with (
                patch.dict(os.environ, {"MULTIDOWNLOADER_FFMPEG": "", "FFMPEG_PATH": ""}, clear=False),
                patch("multidownloader.core.paths.runtime_root", return_value=Path(tmp) / "missing"),
                patch("multidownloader.core.paths.shutil.which", return_value=str(ffmpeg)),
            ):
                resolved = paths.find_ffmpeg()
            self.assertEqual(resolved, ffmpeg)


if __name__ == "__main__":
    unittest.main()
