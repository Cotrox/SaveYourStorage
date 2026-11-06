"""
Ensure FFmpeg is installed or available in bin/ or system PATH.
Developed by Giuseppe Antonino Cotroneo (https://ko-fi.com/cotrox)
"""

import os
import sys
import shutil
import zipfile
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BIN_DIR = BASE_DIR / "bin"
FFMPEG_EXE = BIN_DIR / ("ffmpeg.exe" if os.name == 'nt' else "ffmpeg")
FFPROBE_EXE = BIN_DIR / ("ffprobe.exe" if os.name == 'nt' else "ffprobe")

# Direct fast static release URL for Windows 64-bit
FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"

def is_ffmpeg_available():
    if FFMPEG_EXE.exists() and FFPROBE_EXE.exists():
        return True
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return True
    return False

def download_and_extract_ffmpeg():
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = BIN_DIR / "ffmpeg_download.zip"

    print("=======================================================")
    print(" [Ctrx SaveStorage] Installazione automatica FFmpeg...")
    print("=======================================================")
    print(f"Scaricamento da: {FFMPEG_URL}")

    def progress_hook(count, block_size, total_size):
        if total_size > 0:
            percent = min(100, int(count * block_size * 100 / total_size))
            mb = (count * block_size) / (1024 * 1024)
            tot_mb = total_size / (1024 * 1024)
            sys.stdout.write(f"\rDownload: {percent}% [{mb:.1f} MB / {tot_mb:.1f} MB]")
            sys.stdout.flush()

    try:
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(FFMPEG_URL, zip_path, progress_hook)
        print("\nDownload completato! Estrazione dei file binari...")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for member in zip_ref.namelist():
                filename = os.path.basename(member)
                if filename in ["ffmpeg.exe", "ffprobe.exe", "ffmpeg", "ffprobe"]:
                    source = zip_ref.open(member)
                    target = open(BIN_DIR / filename, "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)
                    print(f" Estratto: {filename}")

        if zip_path.exists():
            zip_path.unlink()

        print("\nFFmpeg configurato correttamente!")
        return True
    except Exception as e:
        print(f"\nErrore durante il download di FFmpeg: {e}")
        if zip_path.exists():
            try:
                zip_path.unlink()
            except Exception:
                pass
        return False

if __name__ == "__main__":
    if is_ffmpeg_available():
        print("FFmpeg trovato e pronto all'uso!")
        sys.exit(0)
    else:
        success = download_and_extract_ffmpeg()
        sys.exit(0 if success else 1)
