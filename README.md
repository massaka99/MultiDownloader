# Multi-Downloader (GUI + CLI)

> Legal note: This tool is for downloading content you have rights or permission to access. Usage may be restricted by site terms, copyright law, or local regulations. You are responsible for complying with applicable rules.

Downloader built on `yt-dlp` with a GUI and a CLI.

## Features

- GUI with mode picker, theme toggle, cookies, output folder, and activity log
- GUI remembers theme, output, and cookies path between runs
- Closing the GUI exits the app (no tray behavior)
- CLI with interactive prompts (v/a/b) and auto-uses `cookies.txt` when present
- Bundled ffmpeg

## Architecture

- GUI entry: `multi_downloader.py`
- CLI entry: `multi_downloader_cli.py`
- Backend: `multidownloader/`
- GUI assets: `multidownloader/webapp/`

## Run (from source)

```powershell
python .\multi_downloader.py
python .\multi_downloader_cli.py
```

The CLI will prompt for URLs and mode when launched without arguments.

## Build Windows exe

```powershell
.\build_exe.ps1
```

The build script downloads ffmpeg, stops any running MultiDownloader exe instances, bundles `cookies.txt` (if present), and outputs:

- `dist\MultiDownloader.exe` (GUI)
- `dist\MultiDownloader-CLI.exe` (CLI)

After a successful build, it cleans up `build\` and the `.spec` files.

> Note: The build can take several minutes, especially the first time.

The exe files are not committed to git (see `.gitignore`). Anyone cloning the repo should run `build_exe.ps1` to produce their own exe files.

### Create your own executable

1. Install Python 3.11+.
2. (Optional) Place `cookies.txt` next to `build_exe.ps1` to embed it.
3. (Optional) Place `app.ico` next to `build_exe.ps1` to set the exe icon.
4. Run the build script:

```powershell
.\build_exe.ps1
```

5. Your exe files will be in `dist\`.

## Cookies

Cookies are only needed for sites that require login, age verification, or private access. If a site works without login, you can skip cookies entirely.

- The `cookies.txt` must contain cookies from the same site you are downloading from.
- Cookies expire; if downloads fail later, export a fresh file.
- If you embed `cookies.txt`, the GUI will default to it unless you pick another file.
- The CLI will always use the embedded `cookies.txt` unless you override with `-c`.
- If you update `cookies.txt`, rebuild the exe to embed the new file, or pass a path with `-c`.

### How to create cookies.txt (Chrome/Edge)

1. Install the extension `Get cookies.txt (LOCALLY)`: https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
2. Log into the site you want to download from.
3. Click the extension and export cookies for the current site to `cookies.txt`.
4. Save the file and either place it next to `build_exe.ps1` or select it in the GUI.

## FFmpeg

- The Windows exe bundles ffmpeg automatically, so you do not need it installed.
- If you run from source, install ffmpeg or drop `ffmpeg.exe` next to the script (or set `MULTIDOWNLOADER_FFMPEG` to the ffmpeg folder).

## Troubleshooting YouTube 403

If you see `HTTP Error 403: Forbidden` or a prompt to sign in, YouTube is blocking the request.

Try this:
1. Export fresh cookies for YouTube and embed them.
2. Update yt-dlp and rebuild:

```powershell
python -m pip install -U yt-dlp
.\build_exe.ps1
```

3. Avoid VPNs or rate limits (YouTube can block IPs).
