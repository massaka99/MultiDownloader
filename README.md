# MultiDownloader

Dette projekt er et Python-baseret program til at downloade videoer og lyd fra forskellige kilder, såsom YouTube, ved hjælp af `yt-dlp` og en grafisk brugergrænseflade oprettet med PyQt5.

## Filer

- **ffmpeg-master-latest-win64-gpl/**: Mappen indeholder FFmpeg, som bruges til at konvertere mediefiler, f.eks. til MP3 eller MP4 format.
  
- **cookies.txt**: Indeholder cookies, der er nødvendige for at kunne downloade indhold fra kilder, der kræver login eller autentificering, efter eget ønske.
  
- **Downloader.py**: Hovedscriptet, der indeholder koden til MultiDownloader-programmet. Det inkluderer GUI, downloadlogik og brug af `yt-dlp`.

- **MultiDownloader.exe**: Den eksekverbare version af programmet, genereret ved hjælp af `PyInstaller`, som gør det muligt at køre programmet uden behov for Python installation.

- **pyinstaller kommando.txt**: En tekstfil, der indeholder kommandoen til at generere den eksekverbare fil med `PyInstaller`.

- **python tips.txt**: En tekstfil med forskellige tips og noter relateret til Python.

- **requirements.txt**: En liste over de Python-pakker, der er nødvendige for at køre dette projekt. Disse kan installeres ved at køre:
  pip install -r requirements.txt

## Installation

- **Download** ffmpeg-master-latest-win64-gpl og placer den i samme mappe som Downloader.py.
  Den kræver desuden en manuel opsættelse ved at target **ffmpeg.exe** filen i miljøvariablerne.
  
- **Installer** de nødvendige Python-pakker:
  
- **Kør** Downloader.py for at starte programmet, eller brug MultiDownloader.exe for at køre det uden Python.
  

## Divserse

- **cookies.txt**: Denne fil kan oprettes med følgende browser extension (https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) og placeres i samme DIR som resterende filer.

- **MultiDownloader.exe** Filen blev ikke vedlagt i repo'en pga. den store filstørrelse.
