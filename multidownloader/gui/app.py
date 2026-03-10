"""Simple Tkinter GUI for MultiDownloader."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from typing import Callable

from ..core import (
    DEFAULT_FRAGMENTS,
    DEFAULT_OUTPUT,
    DEFAULT_WORKERS,
    DownloadConfig,
    Mode,
    parse_urls,
    resolve_cookies,
    resolve_ffmpeg,
    resolve_output_path,
    run_batch,
    unique_urls,
)

_BG = "#f3f7ff"
_CARD_BG = "#ffffff"
_BORDER = "#d8e3ff"
_TEXT = "#12263a"
_MUTED = "#52657a"
_PRIMARY = "#2563eb"
_PRIMARY_ACTIVE = "#1d4ed8"
_SUCCESS = "#1f9d55"
_WARN = "#d97706"
_ERROR = "#dc2626"


class MultiDownloaderGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("MultiDownloader")
        self.root.geometry("920x700")
        self.root.minsize(760, 620)
        self.root.configure(bg=_BG)

        self.mode_var = tk.StringVar(value="video")
        self.output_var = tk.StringVar(value=str(DEFAULT_OUTPUT))
        self.cookies_var = tk.StringVar()
        self.workers_var = tk.IntVar(value=DEFAULT_WORKERS)
        self.fragments_var = tk.IntVar(value=DEFAULT_FRAGMENTS)
        self.status_var = tk.StringVar(value="Ready")

        self._events: queue.Queue[tuple[str, object]] = queue.Queue()
        self._running = False

        self._build_ui()
        self.root.after(100, self._poll_events)

    def _build_ui(self) -> None:
        self.header = tk.Canvas(self.root, height=96, highlightthickness=0, bd=0)
        self.header.pack(fill="x")
        self.header.bind("<Configure>", self._draw_header)

        body = tk.Frame(self.root, bg=_BG, padx=16, pady=16)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(2, weight=1)

        urls_frame = self._create_card(body, "Links", 0)
        controls_frame = self._create_card(body, "Settings", 1)
        logs_frame = self._create_card(body, "Live Log", 2)

        helper = tk.Label(
            urls_frame,
            text="Paste one or more links (one per line)",
            bg=_CARD_BG,
            fg=_MUTED,
            font=("Segoe UI", 10),
        )
        helper.pack(anchor="w", pady=(0, 6))

        self.url_text = tk.Text(
            urls_frame,
            height=6,
            wrap="word",
            bg="#f8fbff",
            fg=_TEXT,
            insertbackground=_TEXT,
            relief="solid",
            bd=1,
            highlightthickness=0,
            font=("Segoe UI", 11),
        )
        self.url_text.pack(fill="x")

        mode_row = tk.Frame(controls_frame, bg=_CARD_BG)
        mode_row.pack(fill="x", pady=(2, 10))
        tk.Label(
            mode_row,
            text="Mode",
            bg=_CARD_BG,
            fg=_TEXT,
            width=12,
            anchor="w",
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left")

        mode_buttons = tk.Frame(mode_row, bg=_CARD_BG)
        mode_buttons.pack(side="left")
        self._mode_button(mode_buttons, "Video", "video", "#2563eb").pack(side="left", padx=(0, 6))
        self._mode_button(mode_buttons, "Audio", "audio", "#059669").pack(side="left", padx=6)
        self._mode_button(mode_buttons, "Both", "both", "#ea580c").pack(side="left", padx=(6, 0))

        self._path_row(
            controls_frame,
            label="Output",
            variable=self.output_var,
            browse_command=self._browse_output,
            row_pad=6,
        )
        self._path_row(
            controls_frame,
            label="Cookies",
            variable=self.cookies_var,
            browse_command=self._browse_cookies,
            row_pad=6,
        )

        numbers = tk.Frame(controls_frame, bg=_CARD_BG)
        numbers.pack(fill="x", pady=(2, 6))
        tk.Label(
            numbers,
            text="Workers",
            bg=_CARD_BG,
            fg=_TEXT,
            width=12,
            anchor="w",
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left")
        tk.Spinbox(
            numbers,
            from_=1,
            to=32,
            textvariable=self.workers_var,
            width=6,
            bg="#f8fbff",
            relief="solid",
            bd=1,
        ).pack(side="left", padx=(0, 14))
        tk.Label(
            numbers,
            text="Fragments",
            bg=_CARD_BG,
            fg=_TEXT,
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left", padx=(0, 8))
        tk.Spinbox(
            numbers,
            from_=1,
            to=64,
            textvariable=self.fragments_var,
            width=6,
            bg="#f8fbff",
            relief="solid",
            bd=1,
        ).pack(side="left")

        action_row = tk.Frame(controls_frame, bg=_CARD_BG)
        action_row.pack(fill="x", pady=(12, 2))

        self.start_btn = tk.Button(
            action_row,
            text="Start Download",
            command=self._start_download,
            bg=_PRIMARY,
            fg="white",
            activebackground=_PRIMARY_ACTIVE,
            activeforeground="white",
            relief="flat",
            padx=18,
            pady=8,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
        )
        self.start_btn.pack(side="left")

        clear_btn = tk.Button(
            action_row,
            text="Clear Log",
            command=self._clear_log,
            bg="#e6eefc",
            fg=_TEXT,
            activebackground="#d4e2ff",
            relief="flat",
            padx=14,
            pady=8,
            font=("Segoe UI", 10),
            cursor="hand2",
        )
        clear_btn.pack(side="left", padx=(10, 0))

        self.progress = tk.Label(
            action_row,
            text="Idle",
            bg=_CARD_BG,
            fg=_MUTED,
            font=("Segoe UI", 10, "bold"),
        )
        self.progress.pack(side="right")

        status = tk.Label(
            controls_frame,
            textvariable=self.status_var,
            bg=_CARD_BG,
            fg=_MUTED,
            anchor="w",
            font=("Segoe UI", 10),
        )
        status.pack(fill="x", pady=(4, 0))

        self.log_text = ScrolledText(
            logs_frame,
            height=15,
            bg="#0f1b2d",
            fg="#d6e4ff",
            insertbackground="#d6e4ff",
            relief="solid",
            bd=1,
            highlightthickness=0,
            font=("Consolas", 10),
        )
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")

    def _create_card(self, parent: tk.Widget, title: str, row: int) -> tk.Frame:
        card = tk.Frame(parent, bg=_CARD_BG, highlightbackground=_BORDER, highlightthickness=1)
        card.grid(row=row, column=0, sticky="nsew", pady=(0, 12 if row < 2 else 0))
        card.grid_columnconfigure(0, weight=1)

        title_label = tk.Label(
            card,
            text=title,
            bg=_CARD_BG,
            fg=_TEXT,
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        title_label.pack(fill="x", padx=12, pady=(10, 2))

        content = tk.Frame(card, bg=_CARD_BG)
        content.pack(fill="both", expand=True, padx=12, pady=(2, 12))
        return content

    def _mode_button(self, parent: tk.Widget, text: str, value: str, color: str) -> tk.Radiobutton:
        return tk.Radiobutton(
            parent,
            text=text,
            value=value,
            variable=self.mode_var,
            indicatoron=False,
            selectcolor=color,
            bg="#edf4ff",
            activebackground="#dbe8ff",
            fg=_TEXT,
            relief="flat",
            padx=10,
            pady=4,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
        )

    def _path_row(
        self,
        parent: tk.Widget,
        label: str,
        variable: tk.StringVar,
        browse_command: Callable[[], None],
        row_pad: int,
    ) -> None:
        row = tk.Frame(parent, bg=_CARD_BG)
        row.pack(fill="x", pady=(0, row_pad))
        tk.Label(
            row,
            text=label,
            bg=_CARD_BG,
            fg=_TEXT,
            width=12,
            anchor="w",
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left")
        entry = tk.Entry(
            row,
            textvariable=variable,
            bg="#f8fbff",
            fg=_TEXT,
            relief="solid",
            bd=1,
            font=("Segoe UI", 10),
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Button(
            row,
            text="Browse",
            command=browse_command,
            bg="#e6eefc",
            fg=_TEXT,
            activebackground="#d4e2ff",
            relief="flat",
            padx=10,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
        ).pack(side="left")

    def _draw_header(self, _event: tk.Event | None = None) -> None:
        width = max(self.header.winfo_width(), 1)
        height = max(self.header.winfo_height(), 1)
        self.header.delete("all")

        start = (37, 99, 235)
        end = (236, 72, 153)
        for x in range(0, width, 2):
            ratio = x / max(width - 1, 1)
            red = int(start[0] + (end[0] - start[0]) * ratio)
            green = int(start[1] + (end[1] - start[1]) * ratio)
            blue = int(start[2] + (end[2] - start[2]) * ratio)
            color = f"#{red:02x}{green:02x}{blue:02x}"
            self.header.create_line(x, 0, x, height, fill=color)

        self.header.create_text(
            18,
            32,
            anchor="w",
            text="MultiDownloader",
            fill="white",
            font=("Segoe UI", 22, "bold"),
        )
        self.header.create_text(
            20,
            66,
            anchor="w",
            text="Drop links, pick mode, press start",
            fill="#e7eeff",
            font=("Segoe UI", 11),
        )

    def _browse_output(self) -> None:
        path = filedialog.askdirectory(initialdir=self.output_var.get() or str(DEFAULT_OUTPUT))
        if path:
            self.output_var.set(path)

    def _browse_cookies(self) -> None:
        path = filedialog.askopenfilename(
            title="Select cookies.txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            self.cookies_var.set(path)

    def _start_download(self) -> None:
        if self._running:
            return

        urls = unique_urls(parse_urls(self.url_text.get("1.0", "end")))
        if not urls:
            messagebox.showerror("No links", "Please add at least one valid URL.")
            return

        try:
            workers = int(self.workers_var.get())
            fragments = int(self.fragments_var.get())
            if workers < 1 or fragments < 1:
                raise ValueError
        except (ValueError, tk.TclError):
            messagebox.showerror("Invalid number", "Workers and fragments must be positive numbers.")
            return

        output_text = self.output_var.get().strip() or str(DEFAULT_OUTPUT)
        cookies_text = self.cookies_var.get().strip()

        try:
            output = resolve_output_path(output_text)
            cookies = resolve_cookies(cookies_text or None)
        except FileNotFoundError as exc:
            messagebox.showerror("Missing file", str(exc))
            return
        except OSError as exc:
            messagebox.showerror("Path error", str(exc))
            return

        config = DownloadConfig(
            mode=self._selected_mode(),
            output=output,
            cookies=cookies,
            cookies_explicit=bool(cookies_text),
            workers=workers,
            fragments=fragments,
            ffmpeg_location=resolve_ffmpeg(),
        )

        self._clear_log()
        self._append_log(f"Queued {len(urls)} URL(s).")
        if not config.ffmpeg_location:
            self._append_log("[warn] ffmpeg not found. Some formats may fail.")

        self._running = True
        self.start_btn.configure(state="disabled", text="Downloading...")
        self.progress.configure(text="Running", fg=_PRIMARY)
        self.status_var.set(f"Downloading {len(urls)} item(s)...")

        worker = threading.Thread(target=self._run_downloads, args=(urls, config), daemon=True)
        worker.start()

    def _run_downloads(self, urls: list[str], config: DownloadConfig) -> None:
        try:
            errors = run_batch(urls, config, logger=self._queue_log)
            self._events.put(("done", errors))
        except Exception as exc:  # noqa: BLE001
            self._events.put(("fatal", str(exc)))

    def _queue_log(self, message: str) -> None:
        self._events.put(("log", message))

    def _poll_events(self) -> None:
        while True:
            try:
                event, payload = self._events.get_nowait()
            except queue.Empty:
                break

            if event == "log":
                self._append_log(str(payload))
            elif event == "fatal":
                self._finish_with_error(str(payload))
            elif event == "done":
                self._finish_with_result(payload if isinstance(payload, list) else [])

        self.root.after(120, self._poll_events)

    def _finish_with_result(self, errors: list[str]) -> None:
        self._running = False
        self.start_btn.configure(state="normal", text="Start Download")

        if errors:
            self.progress.configure(text="Completed with errors", fg=_WARN)
            self.status_var.set(f"Completed with errors ({len(errors)} failed)")
            self._append_log(f"{len(errors)} download(s) failed.")
            preview = "\n".join(errors[:3])
            messagebox.showwarning("Completed with errors", preview if preview else "Some downloads failed.")
            return

        self.progress.configure(text="Success", fg=_SUCCESS)
        self.status_var.set("All downloads completed successfully.")
        self._append_log("All downloads completed successfully.")

    def _finish_with_error(self, message: str) -> None:
        self._running = False
        self.start_btn.configure(state="normal", text="Start Download")
        self.progress.configure(text="Failed", fg=_ERROR)
        self.status_var.set("Download failed.")
        self._append_log(f"[fatal] {message}")
        messagebox.showerror("Download failed", message)

    def _append_log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message.rstrip()}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_log(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _selected_mode(self) -> Mode:
        selected = self.mode_var.get()
        if selected in {"video", "audio", "both"}:
            return selected
        return "video"


def main() -> int:
    root = tk.Tk()
    MultiDownloaderGUI(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
