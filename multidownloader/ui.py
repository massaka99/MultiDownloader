"""PyWebView GUI for Multi-Downloader."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Dict, Optional

import webview

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
from .paths import app_root, find_default_cookies
from .settings import load_settings, save_settings


class AppAPI:
    def __init__(self) -> None:
        self.window: Optional[webview.Window] = None
        self._lock = threading.Lock()
        self._running = False

    def set_window(self, window: webview.Window) -> None:
        self.window = window

    def get_defaults(self) -> Dict[str, Any]:
        stored = load_settings()
        stored_output = stored.get("output") or str(DEFAULT_OUTPUT)
        stored_cookies = stored.get("cookies") or ""
        stored_theme = stored.get("theme") or ""
        cookies = find_default_cookies()

        cookies_value = ""
        if stored_cookies:
            path = Path(stored_cookies).expanduser()
            if path.is_file():
                cookies_value = stored_cookies
        if not cookies_value and cookies:
            cookies_value = str(cookies)

        return {
            "output": stored_output,
            "cookies": cookies_value,
            "theme": stored_theme,
        }

    def save_settings(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            save_settings(payload)
            return {"ok": True}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}

    def select_output_dir(self) -> Optional[str]:
        if not self.window:
            return None
        selection = self.window.create_file_dialog(webview.FOLDER_DIALOG)
        if selection:
            return selection[0]
        return None

    def select_cookies_file(self) -> Optional[str]:
        if not self.window:
            return None
        selection = self.window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=("Cookies (*.txt)", "All files (*.*)"),
        )
        if selection:
            return selection[0]
        return None

    def start_download(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            if self._running:
                return {"ok": False, "error": "busy"}
            self._running = True

        urls_text = (payload.get("urls") or "").strip()
        urls = load_urls_from_text(urls_text)
        if not urls:
            self._running = False
            return {"ok": False, "error": "no_urls"}

        mode = payload.get("mode") or "both"
        output = (payload.get("output") or str(DEFAULT_OUTPUT)).strip()
        cookies = (payload.get("cookies") or "").strip()

        thread = threading.Thread(
            target=self._run_worker,
            args=(urls, mode, output, cookies),
            daemon=True,
        )
        thread.start()
        return {"ok": True}

    def _run_worker(self, urls: list[str], mode: str, output: str, cookies: str) -> None:
        self._emit({"type": "status", "status": "running"})
        try:
            try:
                cookies_path = resolve_cookies(cookies or None)
            except FileNotFoundError as exc:
                self._emit({"type": "done", "ok": False, "errors": [str(exc)]})
                return

            output_path = resolve_output_path(output)
            ffmpeg_path = resolve_ffmpeg()

            config = DownloadConfig(
                download_type=mode,
                output=output_path,
                cookies=cookies_path,
                format_selector=None,
                continue_dl=True,
                workers=DEFAULT_WORKERS,
                fragments=DEFAULT_FRAGMENTS,
                ffmpeg_location=ffmpeg_path,
            )

            def logger(message: str) -> None:
                self._emit({"type": "log", "message": message})

            if config.cookies:
                logger(f"[info] cookies: {config.cookies}")
            if not config.ffmpeg_location:
                logger("[warn] ffmpeg.exe not found. Some formats may fail.")

            errors = run_batch(urls, config, logger=logger)
            if errors:
                self._emit({"type": "done", "ok": False, "errors": errors})
            else:
                self._emit({"type": "done", "ok": True, "errors": []})
        except Exception as exc:  # noqa: BLE001
            self._emit({"type": "done", "ok": False, "errors": [str(exc)]})
        finally:
            with self._lock:
                self._running = False

    def _emit(self, payload: Dict[str, Any]) -> None:
        if not self.window:
            return
        data = json.dumps(payload)
        script = (
            "window.dispatchEvent(new CustomEvent('md-event', { detail: "
            + data
            + " }));"
        )
        self.window.evaluate_js(script)


def main() -> None:
    assets_dir = app_root() / "multidownloader" / "webapp"
    index_path = assets_dir / "index.html"
    stored = load_settings()
    stored_theme = stored.get("theme", "")
    start_url = index_path.as_uri()
    if stored_theme in ("light", "dark"):
        start_url = f"{start_url}#theme={stored_theme}"
    background_color = "#0b0f14"
    if stored_theme == "light":
        background_color = "#f5f6f8"

    api = AppAPI()
    window = webview.create_window(
        "Downloader",
        url=start_url,
        width=1100,
        height=760,
        min_size=(940, 640),
        background_color=background_color,
        js_api=api,
    )
    api.set_window(window)

    webview.start(debug=False)


if __name__ == "__main__":
    main()
