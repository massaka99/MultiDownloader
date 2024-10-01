import os
import re
import sys
import webbrowser
from yt_dlp import YoutubeDL
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel, QLineEdit, QPushButton, 
    QRadioButton, QVBoxLayout, QHBoxLayout, QProgressBar, QButtonGroup, QMessageBox, QListWidget, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

class DownloadThread(QThread):
    progress = pyqtSignal(float)
    error = pyqtSignal(str)

    def __init__(self, url, options):
        super().__init__()
        self.url = url
        self.options = options

    # Kører download i en separat thread
    def run(self):
        try:
            with YoutubeDL(self.options) as ydl:
                ydl.download([self.url])
        except Exception as e:
            self.error.emit(f"Download error: {str(e)}")

    # Opdaterer download status
    def hook(self, d):
        if d['status'] == 'downloading':
            if 'downloaded_bytes' in d and 'total_bytes' in d:
                progress = d['downloaded_bytes'] / d['total_bytes'] * 100
                self.progress.emit(progress)
            elif 'downloaded_bytes' in d and 'total_bytes_estimate' in d:
                progress = d['downloaded_bytes'] / d['total_bytes_estimate'] * 100
                self.progress.emit(progress)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    # Initialiserer GUI
    def initUI(self):
        self.setWindowTitle("Multi Downloader")
        self.setGeometry(100, 100, 800, 450)
        self.setWindowIcon(QIcon("icon.png"))

        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)

        layout = QVBoxLayout(self.centralWidget)
        layout.setContentsMargins(20, 20, 20, 20)

        titleLabel = QLabel()
        titleFont = QFont("Arial", 24, QFont.Bold)
        titleLabel.setFont(titleFont)
        titleLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(titleLabel)

        self.urlLabel = QLabel("Indsæt URL:")
        self.urlLabel.setFont(QFont("Arial", 12))
        layout.addWidget(self.urlLabel)

        self.urlEntry = QLineEdit()
        self.urlEntry.setFont(QFont("Arial", 12))
        layout.addWidget(self.urlEntry)

        self.downloadTypeLabel = QLabel("Vælg downloadtype:")
        self.downloadTypeLabel.setFont(QFont("Arial", 12))
        layout.addWidget(self.downloadTypeLabel)

        self.videoRadio = QRadioButton("Video")
        self.audioRadio = QRadioButton("Lyd")
        self.bothRadio = QRadioButton("Begge")
        self.videoRadio.setChecked(True)

        self.radioGroup = QButtonGroup()
        self.radioGroup.addButton(self.videoRadio)
        self.radioGroup.addButton(self.audioRadio)
        self.radioGroup.addButton(self.bothRadio)

        radioLayout = QHBoxLayout()
        radioLayout.addWidget(self.videoRadio)
        radioLayout.addWidget(self.audioRadio)
        radioLayout.addWidget(self.bothRadio)
        layout.addLayout(radioLayout)

        self.progressBar = QProgressBar()
        self.progressBar.setStyleSheet(
            """
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
                height: 30px;
            }
            QProgressBar::chunk {
                background-color: #61afef;
                width: 20px;
            }
            """
        )
        layout.addWidget(self.progressBar)

        buttonLayout = QHBoxLayout()

        self.downloadButton = QPushButton("Start Download")
        self.downloadButton.setFont(QFont("Arial", 12, QFont.Bold))
        self.downloadButton.setStyleSheet(
            """
            QPushButton {
                background-color: #61afef;
                color: white;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #48a9e6;
            }
            """
        )
        self.downloadButton.clicked.connect(self.start_download)
        buttonLayout.addWidget(self.downloadButton)

        self.clearButton = QPushButton("Ryd")
        self.clearButton.setFont(QFont("Arial", 12, QFont.Bold))
        self.clearButton.setStyleSheet(
            """
            QPushButton {
                background-color: #d9534f;
                color: white;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #c9302c;
            }
            """
        )
        self.clearButton.clicked.connect(self.clear_url)
        buttonLayout.addWidget(self.clearButton)

        self.openFolderButton = QPushButton("Åbn Download Mappe")
        self.openFolderButton.setFont(QFont("Arial", 12, QFont.Bold))
        self.openFolderButton.setStyleSheet(
            """
            QPushButton {
                background-color: #5cb85c;
                color: white;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #4cae4c;
            }
            """
        )
        self.openFolderButton.clicked.connect(self.open_download_folder)
        buttonLayout.addWidget(self.openFolderButton)

        layout.addLayout(buttonLayout)

        self.historyLabel = QLabel("Download Historik:")
        self.historyLabel.setFont(QFont("Arial", 12))
        layout.addWidget(self.historyLabel)

        self.historyList = QListWidget()
        layout.addWidget(self.historyList)

        # Aktiver mørk tilstand
        self.setStyleSheet(
            """
            QWidget {
                background-color: #2e2e2e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit, QListWidget {
                background-color: #404040;
                border: 1px solid #5c5c5c;
                color: #ffffff;
            }
            QRadioButton {
                color: #ffffff;
            }
            QPushButton {
                background-color: #61afef;
                color: white;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #48a9e6;
            }
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
                height: 30px;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #61afef;
                width: 20px;
            }
            QMessageBox {
                background-color: #2e2e2e;
                color: #ffffff;
            }
            """
        )

    # Start downloadprocessen
    def start_download(self):
        media_url = self.urlEntry.text()
        choice = self.get_choice()

        if not media_url:
            QMessageBox.warning(self, "Inputfejl", "Indsæt venligst en URL")
            return

        if not re.match(r'^https?://', media_url):
            QMessageBox.warning(self, "Inputfejl", "Indsæt en gyldig URL")
            return

        download_path = os.path.join(os.path.expanduser('~'), 'Downloads')

        self.downloadThread = DownloadThread(media_url, {})
        options = self.build_options(download_path, choice, self.downloadThread.hook)
        if options:
            self.downloadThread.options = options
            self.downloadThread.progress.connect(self.update_progress)
            self.downloadThread.error.connect(self.show_error)
            self.downloadThread.finished.connect(lambda: self.add_to_history(media_url))
            self.downloadThread.start()
        else:
            QMessageBox.critical(self, "Fejl", "En fejl opstod ved bygning af kommandoen. Tjek venligst filstier og prøv igen.")

    # Få downloadvalg (Video, Lyd, eller Begge)
    def get_choice(self):
        if self.videoRadio.isChecked():
            return 'V'
        elif self.audioRadio.isChecked():
            return 'L'
        elif self.bothRadio.isChecked():
            return 'B'
        return None

    # Bygger download indstillinger
    def build_options(self, download_path, choice, hook):
        cookies_path = os.path.join(os.path.abspath("."), 'cookies.txt')
        ffmpeg_path = os.path.join(os.path.abspath("."), 'ffmpeg-master-latest-win64-gpl', 'bin', 'ffmpeg.exe')

        if not os.path.isfile(cookies_path):
            self.show_error(f"Cookies-fil ikke fundet: {cookies_path}")
            return None
        if not os.path.isfile(ffmpeg_path):
            self.show_error(f"FFmpeg ikke fundet: {ffmpeg_path}")
            return None

        options = {
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'progress_hooks': [hook],
            'ffmpeg_location': ffmpeg_path,
        }

        if choice == 'V':
            options['format'] = 'bestvideo+bestaudio/best'
        elif choice == 'L':
            options['format'] = 'bestaudio/best'
            options['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        elif choice == 'B':
            options['format'] = 'bestvideo+bestaudio/best'
            options['postprocessors'] = [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                },
                {
                    'key': 'FFmpegVideoConvertor',
                    'preferredformat': 'mp4',
                }
            ]
            
        # Authentifikationsindstillinger kan tilføjes her, hvis nødvendigt.
        options['cookiefile'] = cookies_path  
        options['username'] = 'XXXXXXXXXXXX'  
        options['password'] = 'XXXXXXXXXXXX'

        return options

    def update_progress(self, progress):
        self.progressBar.setValue(int(progress))

    def show_error(self, error_message):
        QMessageBox.critical(self, "Fejl", f"En fejl opstod: {error_message}")

    def clear_url(self):
        self.urlEntry.clear()

    def open_download_folder(self):
        download_path = os.path.join(os.path.expanduser('~'), 'Downloads')
        webbrowser.open(download_path)

    def add_to_history(self, url):
        self.historyList.addItem(url)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
