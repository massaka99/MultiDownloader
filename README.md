# MultiDownloader

Et enkelt cli-værktøj til at hente video eller lyd fra f.eks. YouTube, X m.fl.  
Bygget på `yt-dlp`.

## Hurtig start

```powershell
python -m pip install -r requirements.txt
python .\multi_downloader_cli.py "URL_HER"
```

Interaktiv brug i terminalen:

```powershell
python .\multi_downloader_cli.py
```

## GUI (nem og farverig)

Start en simpel grafisk version:

```powershell
python .\multi_downloader_gui.py
```

Alternativt:

```powershell
python -m multidownloader.gui
```

I GUI'en kan du:
- indsætte links (en pr. linje)
- vælge `video`, `audio` eller `both`
- vælge output-mappe og valgfri `cookies.txt`
- starte download og følge live-log i vinduet

Eksempel (kun lyd):

```powershell
python .\multi_downloader_cli.py -m audio "https://www.youtube.com/watch?v=..."
```

## Byg Windows .exe

```powershell
.\build_exe.ps1
```

Færdig fil ligger her:

`dist\MultiDownloader.exe`

GUI-versionen bliver også bygget:

`dist\MultiDownloaderGUI.exe`

## Cookies (valgfrit)

Hvis en side kræver login, så brug `cookies.txt`.

- Læg filen som `cookies.txt` i projektmappen, eller
- brug `-c sti\til\cookies.txt`

Ved build bliver `cookies.txt` pakket ind i `.exe`, hvis filen findes.

### Sådan laver du din egen `cookies.txt`

Du skal selv eksportere dine egne cookies fra den browser, hvor du er logget ind.

1. Installer en browser-udvidelse der kan eksportere cookies til Netscape-format (`cookies.txt`).
2. Log ind på den side du vil hente fra (fx YouTube).
3. Eksportér cookies og gem filen som `cookies.txt`.

Del aldrig din cookie-fil med andre...

## Kort note

Brug kun værktøjet til indhold, du har lov til at hente...
