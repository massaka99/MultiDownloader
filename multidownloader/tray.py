"""System tray integration for Multi-Downloader."""

from __future__ import annotations

import threading
from typing import Optional

try:  # Optional at import time; required for tray to work.
    import pystray
    from PIL import Image, ImageDraw
except Exception:  # noqa: BLE001
    pystray = None
    Image = None
    ImageDraw = None


def tray_supported() -> bool:
    return pystray is not None and Image is not None and ImageDraw is not None


class TrayController:
    def __init__(self, window, title: str = "Multi-Downloader") -> None:
        if not tray_supported():
            raise RuntimeError("pystray/Pillow not available")

        self.window = window
        self.title = title
        self._allow_close = False
        self._icon: Optional[pystray.Icon] = None
        self._thread: Optional[threading.Thread] = None

        icon_image = self._build_icon()
        menu = pystray.Menu(
            pystray.MenuItem("Show", self._show_window, default=True),
            pystray.MenuItem("Hide", self._hide_window),
            pystray.MenuItem("Quit", self._quit_app),
        )
        self._icon = pystray.Icon("MultiDownloader", icon_image, self.title, menu)

    def start(self) -> None:
        if not self._icon:
            return
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if not self._icon:
            return
        try:
            self._icon.stop()
        except Exception:
            return

    def handle_closing(self, *args, **kwargs) -> bool:
        if self._allow_close:
            return True
        self._hide_window()
        return False

    def handle_closed(self, *args, **kwargs) -> None:
        self.stop()

    def _show_window(self, *args, **kwargs) -> None:
        try:
            self.window.show()
        except Exception:
            return

    def _hide_window(self, *args, **kwargs) -> None:
        try:
            self.window.hide()
        except Exception:
            return

    def _quit_app(self, *args, **kwargs) -> None:
        self._allow_close = True
        self.stop()
        self._close_window()

    def _close_window(self) -> None:
        for method_name in ("destroy", "close", "terminate"):
            method = getattr(self.window, method_name, None)
            if callable(method):
                try:
                    method()
                    return
                except Exception:
                    continue
        try:
            import webview

            destroy = getattr(webview, "destroy_window", None)
            if callable(destroy):
                destroy()
        except Exception:
            return

    def _build_icon(self):
        if Image is None or ImageDraw is None:
            raise RuntimeError("Pillow not available")
        size = 64
        image = Image.new("RGBA", (size, size), (20, 24, 32, 255))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((10, 10, 54, 54), radius=10, fill=(66, 133, 244, 255))
        draw.rounded_rectangle((22, 22, 42, 42), radius=6, fill=(230, 238, 255, 255))
        return image
