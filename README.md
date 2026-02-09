# Multi-Downloader (CLI)

> Legal note: This tool is for downloading content you have rights or permission to access. Usage may be restricted by site terms, copyright law, or local regulations. You are responsible for complying with applicable rules.

Downloader built on `yt-dlp` with a command-line interface.

## Features

- CLI supports URLs from arguments, input files, stdin, or interactive prompts.
- Download mode selection: `video`, `audio`, or `both` (also `v/a/b`).
- Optional cookies support with `-c/--cookies`, plus auto-detect of local `cookies.txt`.
- Optional concurrent worker/fragment tuning.
- Windows build script bundles ffmpeg/ffprobe into the executable.

## Architecture

- Module entry point: `python -m multidownloader`
- Script entry point: `multi_downloader_cli.py`
- CLI package: `multidownloader/cli/`
- Core download logic: `multidownloader/core/`

### Project Layout

```text
multidownloader/
  cli/
    app.py
    args.py
    interactive.py
  core/
    config.py
    downloader.py
    paths.py
    urls.py
```

## Run From Source

```powershell
python -m pip install -r requirements.txt
python -m multidownloader
python .\multi_downloader_cli.py
```

The CLI prompts for URLs and mode if started without URL arguments or input.

Example:

```powershell
python .\multi_downloader_cli.py -m audio -o .\downloads https://example.com/video
```

## Build Windows Exe

```powershell
.\build_exe.ps1
```

The build script downloads ffmpeg (unless already available), installs dependencies from `requirements.txt` and `requirements-build.txt`, bundles `cookies.txt` (if present), and outputs:

- `dist\MultiDownloader.exe` (CLI)

After a successful build, it cleans up `build\` and generated `.spec` files.

## Testing

Run the full unit test suite:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

CI (`.github/workflows/ci.yml`) runs tests plus CLI smoke checks on Windows and Linux for Python 3.11-3.13.

## Cookies

Cookies are only needed for sites that require login, age verification, or private access.

- Use `-c path\to\cookies.txt` to provide a specific cookies file.
- If `-c` is not supplied, the CLI auto-detects local `cookies.txt` when available.
- Cookies expire; refresh and export again if downloads start failing.

### Create `cookies.txt` (Chrome/Edge)

1. Install `Get cookies.txt (LOCALLY)`: https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
2. Log into the target site.
3. Export cookies for that site to `cookies.txt`.

## FFmpeg

- The Windows executable bundles ffmpeg/ffprobe automatically.
- When running from source, install ffmpeg or place `ffmpeg.exe` where `MULTIDOWNLOADER_FFMPEG` points.

## Troubleshooting YouTube 403

If you see `HTTP Error 403: Forbidden` or sign-in prompts:

1. Export fresh YouTube cookies.
2. Update `yt-dlp` and rebuild:

```powershell
python -m pip install -U yt-dlp
.\build_exe.ps1
```

3. Retry without VPN/rate-limited routes if applicable.
