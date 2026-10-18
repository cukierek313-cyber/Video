@echo off
setlocal
py -3.11 -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pyinstaller --noconfirm --clean --onefile --windowed --name VidCraftAI --collect-all PySide6 --collect-all imageio_ffmpeg --collect-all faster_whisper --collect-all ctranslate2 app.py
echo Build complete: dist\VidCraftAI.exe
pause
