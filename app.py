import sys, os, subprocess, threading, tempfile
from pathlib import Path
from PySide6.QtCore import Qt, QUrl, QObject, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import *
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

APP_NAME = "VidCraft AI"
VIDEO_FILTER = "Media (*.mp4 *.mov *.mkv *.avi *.webm *.m4v *.mp3 *.wav *.aac *.jpg *.jpeg *.png);;All files (*.*)"

def ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def call_ffmpeg(args):
    return subprocess.run([ffmpeg(), "-hide_banner", "-y", "-nostdin"] + args,
        capture_output=True, text=True, encoding="utf-8", errors="replace")

class Signals(QObject):
    done = Signal(bool, str)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VidCraft AI — Shorts Studio")
        self.resize(1250, 820)
        self.media = []
        self.audio_path = ""
        self.player = QMediaPlayer()
        self.audio_out = QAudioOutput()
        self.player.setAudioOutput(self.audio_out)
        self.preview = QVideoWidget()
        self.player.setVideoOutput(self.preview)
        self.build_ui()

    def build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        header = QHBoxLayout()
        title = QLabel("VidCraft AI")
        title.setFont(QFont("Segoe UI", 23, QFont.Bold))
        tagline = QLabel("SHORTS STUDIO  •  TikTok · Reels · YouTube Shorts")
        tagline.setStyleSheet("color:#a7b3c8;")
        header.addWidget(title); header.addWidget(tagline); header.addStretch()
        main.addLayout(header)

        splitter = QSplitter(Qt.Horizontal)
        main.addWidget(splitter, 1)
        left = QWidget(); ll = QVBoxLayout(left)
        ll.addWidget(QLabel("MEDIA"))
        self.media_list = QListWidget()
        self.media_list.itemDoubleClicked.connect(self.preview_media)
        ll.addWidget(self.media_list, 1)
        add = QPushButton("＋ Importuj pliki")
        add.clicked.connect(self.import_media)
        ll.addWidget(add)
        splitter.addWidget(left)

        center = QWidget(); cl = QVBoxLayout(center)
        cl.addWidget(QLabel("PODGLĄD"))
        cl.addWidget(self.preview, 1)
        controls = QHBoxLayout()
        play = QPushButton("▶ Odtwórz / pauza"); play.clicked.connect(self.toggle_play)
        controls.addWidget(play)
        self.current_label = QLabel("Dwuklik na pliku, aby wyświetlić podgląd")
        controls.addWidget(self.current_label, 1)
        cl.addLayout(controls)
        splitter.addWidget(center)

        right = QWidget(); rl = QVBoxLayout(right)
        rl.addWidget(QLabel("USTAWIENIA SHORTS"))
        self.ratio = QComboBox()
        self.ratio.addItem("Pionowy 9:16 — 1080 × 1920", (1080,1920))
        self.ratio.addItem("Kwadrat 1:1 — 1080 × 1080", (1080,1080))
        self.ratio.addItem("Poziomy 16:9 — 1920 × 1080", (1920,1080))
        rl.addWidget(QLabel("Format projektu")); rl.addWidget(self.ratio)
        self.quality = QComboBox()
        self.quality.addItems(["Wysoka jakość", "Zrównoważona", "Mniejszy plik"])
        rl.addWidget(QLabel("Jakość eksportu")); rl.addWidget(self.quality)
        self.output = QLineEdit(str(Path.home() / "Videos" / "vidcraft_shorts.mp4"))
        outbtn = QPushButton("Wybierz plik wynikowy…"); outbtn.clicked.connect(self.pick_output)
        rl.addWidget(QLabel("Eksport MP4")); rl.addWidget(self.output); rl.addWidget(outbtn)
        self.music_label = QLabel("Nie dodano muzyki")
        music = QPushButton("Dodaj muzykę…"); music.clicked.connect(self.pick_music)
        clear_music = QPushButton("Usuń muzykę"); clear_music.clicked.connect(self.clear_music)
        rl.addWidget(QLabel("Ścieżka muzyczna")); rl.addWidget(music); rl.addWidget(self.music_label); rl.addWidget(clear_music)
        rl.addWidget(QLabel("Muzyka będzie miksowana pod klipami; zachowaj prawa do używanych utworów."))
        rl.addStretch()
        splitter.addWidget(right)
        splitter.setSizes([250,650,300])

        timeline_box = QGroupBox("OŚ CZASU — kolejność klipów")
        tl = QVBoxLayout(timeline_box)
        self.timeline = QListWidget()
        self.timeline.setDragDropMode(QAbstractItemView.InternalMove)
        self.timeline.setDefaultDropAction(Qt.MoveAction)
        self.timeline.setToolTip("Przeciągaj elementy, aby zmienić kolejność klipów.")
        tl.addWidget(self.timeline)
        row = QHBoxLayout()
        add_timeline = QPushButton("Dodaj zaznaczone media do osi czasu")
        add_timeline.clicked.connect(self.add_to_timeline)
        remove = QPushButton("Usuń z osi czasu"); remove.clicked.connect(self.remove_from_timeline)
        up = QPushButton("↑"); up.clicked.connect(lambda: self.move_clip(-1))
        down = QPushButton("↓"); down.clicked.connect(lambda: self.move_clip(1))
        row.addWidget(add_timeline); row.addWidget(remove); row.addWidget(up); row.addWidget(down)
        tl.addLayout(row)
        main.addWidget(timeline_box, 1)

        bottom = QHBoxLayout()
        self.export_btn = QPushButton("Eksportuj film")
        self.export_btn.clicked.connect(self.export_video)
        self.ai_btn = QPushButton("Wygeneruj napisy AI (SRT)")
        self.ai_btn.clicked.connect(self.generate_subtitles)
        bottom.addWidget(self.export_btn); bottom.addWidget(self.ai_btn)
        self.progress = QProgressBar(); self.progress.setRange(0,0); self.progress.hide()
        bottom.addWidget(self.progress, 1)
        main.addLayout(bottom)
        self.log = QPlainTextEdit(); self.log.setReadOnly(True); self.log.setMaximumHeight(85)
        self.log.setPlainText("Importuj klipy, dodaj je do osi czasu, ustaw format i eksportuj.")
        main.addWidget(self.log)

        self.setStyleSheet("""
        QWidget,QMainWindow {background:#121720;color:#edf2f7;font-size:13px}
        QGroupBox {border:1px solid #354155;border-radius:8px;margin-top:8px;padding:8px;font-weight:bold}
        QGroupBox::title {subcontrol-origin:margin;left:10px;padding:0 4px}
        QLineEdit,QListWidget,QComboBox,QPlainTextEdit {background:#1c2533;border:1px solid #3b485d;border-radius:5px;padding:6px;color:#f4f7fb}
        QPushButton {background:#586df5;border:0;border-radius:6px;padding:9px;color:white;font-weight:bold}
        QPushButton:hover {background:#7183ff}
        QVideoWidget {background:#05070a;border-radius:8px}
        """)

    def logmsg(self, s): self.log.appendPlainText(s)

    def import_media(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Importuj media", "", VIDEO_FILTER)
        for path in paths:
            if path not in self.media:
                self.media.append(path)
                item = QListWidgetItem(Path(path).name)
                item.setData(Qt.UserRole, path)
                self.media_list.addItem(item)
        if paths: self.logmsg(f"Zaimportowano {len(paths)} plików.")

    def preview_media(self, item):
        path = item.data(Qt.UserRole)
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()
        self.current_label.setText(Path(path).name)

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState: self.player.pause()
        else: self.player.play()

    def add_to_timeline(self):
        selected = self.media_list.selectedItems()
        if not selected:
            QMessageBox.information(self, APP_NAME, "Zaznacz pliki w panelu MEDIA.")
            return
        for item in selected:
            path = item.data(Qt.UserRole)
            timeline_item = QListWidgetItem(Path(path).name)
            timeline_item.setData(Qt.UserRole, path)
            self.timeline.addItem(timeline_item)
        self.logmsg(f"Dodano {len(selected)} klipów do osi czasu. Przeciągaj, aby zmienić kolejność.")

    def remove_from_timeline(self):
        for item in self.timeline.selectedItems():
            self.timeline.takeItem(self.timeline.row(item))

    def move_clip(self, offset):
        row = self.timeline.currentRow()
        target = row + offset
        if row < 0 or target < 0 or target >= self.timeline.count(): return
        item = self.timeline.takeItem(row)
        self.timeline.insertItem(target, item)
        self.timeline.setCurrentRow(target)

    def pick_output(self):
        p, _ = QFileDialog.getSaveFileName(self, "Zapisz film", self.output.text(), "MP4 (*.mp4)")
        if p: self.output.setText(p if p.lower().endswith(".mp4") else p + ".mp4")

    def pick_music(self):
        p, _ = QFileDialog.getOpenFileName(self, "Wybierz muzykę", "", "Audio (*.mp3 *.wav *.aac *.m4a *.ogg)")
        if p:
            self.audio_path = p
            self.music_label.setText(Path(p).name)

    def clear_music(self):
        self.audio_path = ""
        self.music_label.setText("Nie dodano muzyki")

    def busy(self, yes):
        self.progress.setVisible(yes)
        self.export_btn.setEnabled(not yes)
        self.ai_btn.setEnabled(not yes)

    def export_video(self):
        paths = [self.timeline.item(i).data(Qt.UserRole) for i in range(self.timeline.count())]
        if not paths:
            QMessageBox.warning(self, APP_NAME, "Dodaj co najmniej jeden klip do osi czasu.")
            return
        output = self.output.text().strip()
        if not output:
            self.pick_output(); output = self.output.text().strip()
        if not output: return
        w,h = self.ratio.currentData()
        crf = ["18","23","28"][self.quality.currentIndex()]
        self.busy(True); self.logmsg("Eksportuję projekt. Przy wielu klipach może to potrwać.")
        def task():
            ok, msg = self.render(paths, output, w, h, crf)
            self.signals.done.emit(ok, msg)
        self.signals = Signals()
        self.signals.done.connect(self.finished)
        threading.Thread(target=task, daemon=True).start()

    def render(self, paths, output, w, h, crf):
        try:
            with tempfile.TemporaryDirectory(prefix="vidcraft_") as td:
                rendered = []
                for i, path in enumerate(paths):
                    target = str(Path(td) / f"clip_{i:04d}.mp4")
                    # Normalize every clip to a common frame size, frame rate, pixel format and audio stream.
                    vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1,fps=30,format=yuv420p"
                    result = call_ffmpeg(["-i", path, "-vf", vf, "-map", "0:v:0", "-map", "0:a:0?","-c:v","libx264","-preset","veryfast","-crf",crf,"-c:a","aac","-ar","48000","-ac","2","-af","apad","-shortest","-movflags","+faststart",target])
                    if result.returncode != 0:
                        # Retry for videos without audio, adding a silent audio stream.
                        result = call_ffmpeg(["-i",path,"-f","lavfi","-i","anullsrc=channel_layout=stereo:sample_rate=48000",
                            "-vf",vf,"-map","0:v:0","-map","1:a:0","-c:v","libx264","-preset","veryfast","-crf",crf,
                            "-c:a","aac","-shortest","-movflags","+faststart",target])
                    if result.returncode != 0:
                        return False, f"Błąd przy klipie {Path(path).name}:\n{result.stderr[-1800:]}"
                    rendered.append(target)
                listfile = str(Path(td) / "concat.txt")
                with open(listfile,"w",encoding="utf-8") as f:
                    for p in rendered:
                        f.write("file '" + p.replace("\\","/").replace("'","'\\''") + "'\n")
                temp_out = str(Path(td) / "joined.mp4")
                result = call_ffmpeg(["-f","concat","-safe","0","-i",listfile,"-c","copy",temp_out])
                if result.returncode != 0:
                    return False, "Nie udało się połączyć klipów:\n" + result.stderr[-1800:]
                if self.audio_path:
                    mixed = call_ffmpeg(["-i",temp_out,"-stream_loop","-1","-i",self.audio_path,
                        "-filter_complex","[1:a]volume=0.22[music];[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[a]",
                        "-map","0:v:0","-map","[a]","-c:v","copy","-c:a","aac","-shortest","-movflags","+faststart",output])
                    if mixed.returncode != 0:
                        return False, "Błąd miksowania muzyki:\n" + mixed.stderr[-1800:]
                else:
                    import shutil
                    Path(output).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(temp_out, output)
            return True, "Gotowe! Zapisano: " + output
        except Exception as e:
            return False, str(e)

    def generate_subtitles(self):
        row = self.timeline.currentRow()
        if row < 0:
            QMessageBox.information(self, APP_NAME, "Zaznacz klip na osi czasu, z którego chcesz wygenerować napisy.")
            return
        source = self.timeline.item(row).data(Qt.UserRole)
        target, _ = QFileDialog.getSaveFileName(self, "Zapisz napisy", str(Path(source).with_suffix(".srt")), "SubRip (*.srt)")
        if not target: return
        lang, ok = QInputDialog.getItem(self, "Język napisów", "Wybierz język:", ["Polski","English","Automatyczne wykrywanie"], 0, False)
        if not ok: return
        language = {"Polski":"pl","English":"en","Automatyczne wykrywanie":None}[lang]
        self.busy(True); self.logmsg("Whisper AI: generowanie napisów. Przy pierwszym uruchomieniu model może się pobrać.")
        self.signals = Signals(); self.signals.done.connect(self.finished)
        def task():
            try:
                from faster_whisper import WhisperModel
                model = WhisperModel("small", device="cpu", compute_type="int8")
                segments, info = model.transcribe(source, language=language, vad_filter=True)
                def stamp(sec):
                    ms = int(sec*1000); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
                    return f"{h:02}:{m:02}:{s:02},{ms:03}"
                with open(target,"w",encoding="utf-8") as f:
                    for n, seg in enumerate(segments,1):
                        f.write(f"{n}\\n{stamp(seg.start)} --> {stamp(seg.end)}\\n{seg.text.strip()}\\n\\n")
                self.signals.done.emit(True,"Zapisano napisy: "+target)
            except Exception as e: self.signals.done.emit(False,"Błąd AI: "+str(e))
        threading.Thread(target=task,daemon=True).start()

    def finished(self, ok, message):
        self.busy(False); self.logmsg(message)
        (QMessageBox.information if ok else QMessageBox.critical)(self, APP_NAME, message[-3000:])

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    win = MainWindow(); win.show()
    sys.exit(app.exec())

if __name__ == "__main__": main()
