"""
Local Desktop Server & API Backend for SaveYourStorage.
Developed by Giuseppe Antonino Cotroneo (https://ko-fi.com/cotrox)

Provides native Windows dialogs, media streaming with Range requests,
and batch processing management.
"""

import os
import sys
import json
import time
import webbrowser
import mimetypes
import threading
import subprocess
import urllib.parse
import urllib.request
import zipfile
import shutil
from pathlib import Path
from http import HTTPStatus
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

from scanner import scan_target, format_size, VIDEO_EXTENSIONS, IMAGE_EXTENSIONS
from engine import MediaEngine

# App Directory
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

WEB_DIR = BASE_DIR / "web"
ASSETS_DIR = BASE_DIR / "assets"
BIN_DIR = BASE_DIR / "bin"
MANAGED_COMPONENTS_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "SaveYourStorage" / "components"
FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"

# Engine setup
engine = MediaEngine()
engine.locate_binaries()

# Component installer state
installer_lock = threading.Lock()
installer_state = {
    "is_installing": False,
    "status": "idle",  # "idle" | "downloading" | "extracting" | "completed" | "error"
    "progress": 0.0,
    "downloaded_bytes": 0,
    "total_bytes": 0,
    "message": ""
}

def component_status():
    binaries = engine.locate_binaries()
    flag_file = MANAGED_COMPONENTS_DIR / "uninstalled.flag"
    is_uninstalled = flag_file.exists() or binaries.get("uninstalled", False)

    filename = lambda name: name + (".exe" if os.name == "nt" else "")
    managed_ffmpeg = MANAGED_COMPONENTS_DIR / filename("ffmpeg")
    managed_ffprobe = MANAGED_COMPONENTS_DIR / filename("ffprobe")
    bundled_ffmpeg = BIN_DIR / filename("ffmpeg")
    bundled_ffprobe = BIN_DIR / filename("ffprobe")

    ffmpeg_installed = binaries["ffmpeg_available"] and not is_uninstalled
    ffprobe_installed = binaries["ffprobe_available"] and not is_uninstalled
    overall_available = binaries["available"] and not is_uninstalled

    def get_source(candidate_path, managed_file, bundled_file, is_inst):
        if not is_inst or not candidate_path:
            return "missing"
        try:
            cand = Path(candidate_path).resolve()
            if managed_file.exists() and cand == managed_file.resolve():
                return "managed"
            if bundled_file.exists() and cand == bundled_file.resolve():
                return "bundled"
        except Exception:
            pass
        return "system"

    with installer_lock:
        inst_copy = dict(installer_state)

    return {
        "available": overall_available,
        "is_uninstalled": is_uninstalled,
        "ffmpeg": {
            "installed": ffmpeg_installed,
            "path": binaries["ffmpeg"] if ffmpeg_installed else "",
            "source": get_source(binaries["ffmpeg"], managed_ffmpeg, bundled_ffmpeg, ffmpeg_installed),
        },
        "ffprobe": {
            "installed": ffprobe_installed,
            "path": binaries["ffprobe"] if ffprobe_installed else "",
            "source": get_source(binaries["ffprobe"], managed_ffprobe, bundled_ffprobe, ffprobe_installed),
        },
        "can_install": True,
        "installer": inst_copy
    }

def install_worker(force_download=False):
    global installer_state
    filename = lambda name: name + (".exe" if os.name == "nt" else "")
    MANAGED_COMPONENTS_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = MANAGED_COMPONENTS_DIR / "ffmpeg_download.zip"

    with installer_lock:
        installer_state["is_installing"] = True
        installer_state["status"] = "downloading"
        installer_state["progress"] = 0.0
        installer_state["downloaded_bytes"] = 0
        installer_state["total_bytes"] = 0
        installer_state["message"] = "Inizializzazione installazione..."

    try:
        # Clear uninstalled flag
        flag_file = MANAGED_COMPONENTS_DIR / "uninstalled.flag"
        if flag_file.exists():
            flag_file.unlink(missing_ok=True)

        target_ffmpeg = MANAGED_COMPONENTS_DIR / filename("ffmpeg")
        target_ffprobe = MANAGED_COMPONENTS_DIR / filename("ffprobe")
        bundled_ffmpeg = BIN_DIR / filename("ffmpeg")
        bundled_ffprobe = BIN_DIR / filename("ffprobe")

        # Fast path: copy from bundled bin/ if present and not force_download
        if not force_download:
            if target_ffmpeg.exists() and target_ffprobe.exists():
                with installer_lock:
                    installer_state["progress"] = 100.0
                    installer_state["status"] = "completed"
                    installer_state["message"] = "Componenti già disponibili e riattivati!"
                engine.locate_binaries()
                return

            if bundled_ffmpeg.exists() and bundled_ffprobe.exists():
                with installer_lock:
                    installer_state["message"] = "Copia dei componenti integrati..."
                    installer_state["progress"] = 40.0
                shutil.copy2(bundled_ffmpeg, target_ffmpeg)
                with installer_lock:
                    installer_state["progress"] = 80.0
                shutil.copy2(bundled_ffprobe, target_ffprobe)
                with installer_lock:
                    installer_state["progress"] = 100.0
                    installer_state["status"] = "completed"
                    installer_state["message"] = "Componenti integrati configurati con successo!"
                engine.locate_binaries()
                return

        # Download from GitHub release
        with installer_lock:
            installer_state["message"] = "Connessione ai server GitHub per FFmpeg..."
            installer_state["progress"] = 5.0

        req = urllib.request.Request(
            FFMPEG_URL,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SaveYourStorage/1.0"
            }
        )

        with urllib.request.urlopen(req, timeout=30) as resp, open(archive_path, "wb") as f_out:
            total_size = int(resp.headers.get("Content-Length", 0))
            with installer_lock:
                installer_state["total_bytes"] = total_size
            downloaded = 0
            chunk_size = 65536
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f_out.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    pct = round(downloaded / total_size * 100.0, 1)
                    with installer_lock:
                        installer_state["downloaded_bytes"] = downloaded
                        installer_state["progress"] = min(90.0, pct * 0.9)
                        installer_state["message"] = f"Download: {pct:.0f}% ({format_size(downloaded)} di {format_size(total_size)})"

        with installer_lock:
            installer_state["status"] = "extracting"
            installer_state["progress"] = 92.0
            installer_state["message"] = "Estrazione ed installazione dei componenti..."

        extracted = set()
        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.infolist():
                name = Path(member.filename).name.lower()
                if name in {"ffmpeg.exe", "ffprobe.exe", "ffmpeg", "ffprobe"}:
                    destination = MANAGED_COMPONENTS_DIR / name
                    with archive.open(member) as src, open(destination, "wb") as tgt:
                        shutil.copyfileobj(src, tgt)
                    extracted.add(name)

        if archive_path.exists():
            archive_path.unlink(missing_ok=True)

        needed = {"ffmpeg.exe", "ffprobe.exe"} if os.name == 'nt' else {"ffmpeg", "ffprobe"}
        if not needed.issubset(extracted):
            raise RuntimeError("L'archivio scaricato non contiene entrambi i componenti necessari (FFmpeg e FFprobe).")

        with installer_lock:
            installer_state["progress"] = 100.0
            installer_state["status"] = "completed"
            installer_state["message"] = "Installazione completata con successo! Componenti pronti."

        engine.locate_binaries()

    except Exception as exc:
        with installer_lock:
            installer_state["status"] = "error"
            installer_state["message"] = f"Errore durante l'installazione: {exc}"
        if archive_path.exists():
            archive_path.unlink(missing_ok=True)
    finally:
        with installer_lock:
            installer_state["is_installing"] = False

def start_install_components(force_download=False):
    with installer_lock:
        if installer_state["is_installing"]:
            return False
    t = threading.Thread(target=install_worker, args=(force_download,), daemon=True)
    t.start()
    return True

def uninstall_components():
    MANAGED_COMPONENTS_DIR.mkdir(parents=True, exist_ok=True)
    flag_file = MANAGED_COMPONENTS_DIR / "uninstalled.flag"
    flag_file.touch(exist_ok=True)

    filename = lambda name: name + (".exe" if os.name == "nt" else "")
    for name in (filename("ffmpeg"), filename("ffprobe")):
        target = MANAGED_COMPONENTS_DIR / name
        if target.exists():
            try:
                target.unlink()
            except OSError as exc:
                raise RuntimeError(f"Impossibile rimuovere {name}: {exc}") from exc

    with installer_lock:
        installer_state["is_installing"] = False
        installer_state["status"] = "idle"
        installer_state["progress"] = 0.0
        installer_state["message"] = ""

    engine.locate_binaries()
    return component_status()

# Processing State Manager
class ProcessManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.is_running = False
        self.cancel_requested = False
        self.items = []
        self.output_dir = ""
        self.options = {}
        self.current_index = -1
        self.current_item_progress = 0.0
        self.current_status_text = "In attesa"
        self.total_saved_bytes = 0
        self.total_processed_original_bytes = 0
        self.total_processed_output_bytes = 0
        self.start_time = 0.0
        self.worker_thread = None

    def reset(self, items, output_dir, options):
        with self.lock:
            self.is_running = True
            self.cancel_requested = False
            self.items = items
            self.output_dir = output_dir
            self.options = options
            self.current_index = 0
            self.current_item_progress = 0.0
            self.current_status_text = "Inizializzazione..."
            self.total_saved_bytes = 0
            self.total_processed_original_bytes = 0
            self.total_processed_output_bytes = 0
            self.start_time = time.time()

    def get_status(self):
        with self.lock:
            total_items = len(self.items)
            completed_items = sum(1 for item in self.items if item.get("status") in ["done", "error"])
            overall_pct = (completed_items / total_items * 100.0) if total_items > 0 else 0.0

            overall_saved_pct = 0.0
            if self.total_processed_original_bytes > 0:
                overall_saved_pct = round(
                    (self.total_saved_bytes / self.total_processed_original_bytes) * 100.0, 1
                )

            return {
                "is_running": self.is_running,
                "current_index": self.current_index,
                "total_items": total_items,
                "completed_items": completed_items,
                "overall_progress": round(overall_pct, 1),
                "current_item_progress": round(self.current_item_progress, 1),
                "current_status_text": self.current_status_text,
                "total_saved_bytes": self.total_saved_bytes,
                "total_saved_formatted": format_size(self.total_saved_bytes),
                "total_saved_percentage": overall_saved_pct,
                "items": self.items
            }

    def cancel(self):
        with self.lock:
            self.cancel_requested = True
            self.current_status_text = "Interruzione in corso..."
        engine.cancel()

    def worker_loop(self):
        total = len(self.items)
        for idx, item in enumerate(self.items):
            if self.cancel_requested:
                break

            with self.lock:
                self.current_index = idx
                self.current_item_progress = 0.0
                self.current_status_text = f"Elaborazione ({idx + 1}/{total}): {item['name']}"
                item["status"] = "processing"

            def item_progress_cb(pct, status_text):
                with self.lock:
                    self.current_item_progress = pct
                    self.current_status_text = f"({idx + 1}/{total}) {item['name']} - {pct:.0f}%"

            try:
                result = engine.process_item(
                    item=item,
                    output_dir=self.output_dir,
                    options=self.options,
                    progress_callback=item_progress_cb
                )

                with self.lock:
                    item["status"] = "done"
                    item["output_path"] = result["output_path"]
                    item["output_size_bytes"] = result["output_size_bytes"]
                    item["output_size_formatted"] = format_size(result["output_size_bytes"])
                    item["saved_bytes"] = result["saved_bytes"]
                    item["saved_percentage"] = result["saved_percentage"]

                    self.total_saved_bytes += result["saved_bytes"]
                    self.total_processed_original_bytes += item["size_bytes"]
                    self.total_processed_output_bytes += result["output_size_bytes"]

            except Exception as e:
                with self.lock:
                    item["status"] = "error"
                    item["error_message"] = str(e)
                    self.current_status_text = f"Errore su {item['name']}: {e}"

        with self.lock:
            self.is_running = False
            if self.cancel_requested:
                self.current_status_text = "Operazione annullata dall'utente."
            else:
                self.current_status_text = "Operazioni completate con successo!"

manager = ProcessManager()

def ask_native_file():
    """Triggers native Windows open file dialog."""
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    filetypes = [
        ("File multimediali", "*.mp4;*.mov;*.mkv;*.avi;*.webm;*.flv;*.wmv;*.jpg;*.jpeg;*.png;*.webp;*.bmp;*.heic"),
        ("Tutti i video", "*.mp4;*.mov;*.mkv;*.avi;*.webm;*.flv;*.wmv;*.ts;*.3gp"),
        ("Tutte le immagini", "*.jpg;*.jpeg;*.png;*.webp;*.bmp;*.tiff;*.heic;*.gif"),
        ("Tutti i file", "*.*")
    ]
    selected = filedialog.askopenfilename(
        title="Seleziona un video o una foto da ottimizzare",
        filetypes=filetypes
    )
    root.destroy()
    return selected

def ask_native_folder():
    """Triggers native Windows open folder dialog."""
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    selected = filedialog.askdirectory(title="Seleziona la cartella con i file da elaborare")
    root.destroy()
    return selected

def ask_native_output_folder(initial_dir=""):
    """Triggers native Windows output folder selection."""
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    selected = filedialog.askdirectory(
        title="Seleziona la cartella di destinazione per i file ottimizzati",
        initialdir=initial_dir or None
    )
    root.destroy()
    return selected

def open_folder_in_explorer(folder_path):
    p = Path(folder_path).resolve()
    if p.exists():
        if os.name == 'nt':
            os.startfile(str(p))
        else:
            subprocess.run(["xdg-open", str(p)])
        return True
    return False

class SaveYourStorageHTTPHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence routine static asset logs, log only errors or important requests
        pass

    def send_json(self, data, status_code=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Range")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/api/status":
            return self.send_json(manager.get_status())

        if path == "/api/system-info" or path == "/api/install-status":
            return self.send_json(component_status())

        if path == "/media-preview":
            raw_path = query.get("path", [""])[0]
            if not raw_path:
                self.send_error(400, "Missing path parameter")
                return
            return self.handle_media_preview(raw_path)

        # Static assets
        if path == "/" or path == "/index.html":
            file_to_serve = WEB_DIR / "index.html"
        elif path.startswith("/assets/"):
            file_to_serve = ASSETS_DIR / path.removeprefix("/assets/")
        else:
            rel = path.lstrip("/")
            file_to_serve = WEB_DIR / rel

        try:
            file_to_serve = file_to_serve.resolve()
            allowed_roots = (WEB_DIR.resolve(), ASSETS_DIR.resolve())
            if not any(file_to_serve == root or root in file_to_serve.parents for root in allowed_roots):
                self.send_error(403, "Forbidden")
                return
        except OSError:
            self.send_error(400, "Invalid path")
            return

        if file_to_serve.exists() and file_to_serve.is_file():
            mime_type, _ = mimetypes.guess_type(str(file_to_serve))
            if not mime_type:
                mime_type = "application/octet-stream"
            
            try:
                with open(file_to_serve, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", f"{mime_type}; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_error(500, str(e))
        else:
            self.send_error(404, "Not Found")

    def handle_media_preview(self, media_path_str: str):
        """Streams media files with HTTP 206 Partial Content (Range) support."""
        media_file = Path(media_path_str)
        if not media_file.exists() or not media_file.is_file():
            self.send_error(404, "Media file non trovato")
            return

        file_size = media_file.stat().st_size
        mime_type, _ = mimetypes.guess_type(str(media_file))
        if not mime_type:
            mime_type = "video/mp4"

        range_header = self.headers.get("Range")
        if range_header:
            # Parse Range: bytes=start-end
            bytes_range = range_header.replace("bytes=", "").strip()
            parts = bytes_range.split("-")
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if parts[1] else file_size - 1

            if start >= file_size or end >= file_size or start > end:
                self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                self.send_header("Content-Range", f"bytes */{file_size}")
                self.end_headers()
                return

            length = end - start + 1
            self.send_response(HTTPStatus.PARTIAL_CONTENT)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.send_header("Content-Length", str(length))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()

            with open(media_file, "rb") as f:
                f.seek(start)
                bytes_to_send = length
                chunk_size = 64 * 1024
                while bytes_to_send > 0:
                    read_len = min(chunk_size, bytes_to_send)
                    chunk = f.read(read_len)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    bytes_to_send -= len(chunk)
        else:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()
            with open(media_file, "rb") as f:
                shutil_copyfileobj = getattr(os, "sendfile", None)
                if shutil_copyfileobj and hasattr(self.wfile, "fileno"):
                    try:
                        os.sendfile(self.wfile.fileno(), f.fileno(), 0, file_size)
                        return
                    except Exception:
                        pass
                chunk_size = 64 * 1024
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    self.wfile.write(chunk)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            body = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            body = {}

        if path == "/api/browse-file":
            selected = ask_native_file()
            if not selected:
                return self.send_json({"selected": False, "path": ""})
            try:
                scanned = scan_target(selected, ffprobe_bin=engine.ffprobe_bin, probe_meta=True)
                return self.send_json({"selected": True, "path": selected, "data": scanned})
            except Exception as e:
                return self.send_json({"selected": True, "path": selected, "error": str(e)}, status_code=400)

        elif path == "/api/browse-folder":
            selected = ask_native_folder()
            if not selected:
                return self.send_json({"selected": False, "path": ""})
            try:
                scanned = scan_target(selected, ffprobe_bin=engine.ffprobe_bin, probe_meta=False)
                return self.send_json({"selected": True, "path": selected, "data": scanned})
            except Exception as e:
                return self.send_json({"selected": True, "path": selected, "error": str(e)}, status_code=400)

        elif path == "/api/browse-output-folder":
            initial_dir = body.get("initial_dir", "")
            selected = ask_native_output_folder(initial_dir)
            return self.send_json({"selected": bool(selected), "path": selected})

        elif path == "/api/open-folder":
            target_path = body.get("path", "")
            success = open_folder_in_explorer(target_path)
            return self.send_json({"success": success})

        elif path == "/api/open-kofi":
            webbrowser.open("https://ko-fi.com/cotrox")
            return self.send_json({"success": True})

        elif path == "/api/install-components":
            force = body.get("force_download", False)
            started = start_install_components(force_download=force)
            return self.send_json({"started": started, "components": component_status()})

        elif path == "/api/uninstall-components":
            if manager.is_running:
                return self.send_json({"error": "Arresta l'elaborazione prima di rimuovere i componenti."}, status_code=409)
            try:
                return self.send_json({"status": "uninstalled", "components": uninstall_components()})
            except Exception as exc:
                return self.send_json({"error": f"Rimozione componenti fallita: {exc}"}, status_code=500)

        elif path == "/api/upload-stream":
            query = urllib.parse.parse_qs(parsed.query)
            filename = query.get("name", ["dropped_media"])[0]
            filename = os.path.basename(filename)
            upload_dir = BASE_DIR / "_uploads"
            upload_dir.mkdir(parents=True, exist_ok=True)
            target_file = upload_dir / filename
            
            bytes_left = content_length
            with open(target_file, "wb") as f:
                while bytes_left > 0:
                    chunk = self.rfile.read(min(65536, bytes_left))
                    if not chunk:
                        break
                    f.write(chunk)
                    bytes_left -= len(chunk)
                    
            try:
                scanned = scan_target(str(target_file), ffprobe_bin=engine.ffprobe_bin, probe_meta=True)
                return self.send_json({"success": True, "data": scanned})
            except Exception as e:
                return self.send_json({"error": str(e)}, status_code=400)

        elif path == "/api/scan":
            target_path = body.get("target_path", "")
            if not target_path:
                return self.send_json({"error": "Percorso mancante"}, status_code=400)
            try:
                scanned = scan_target(target_path, ffprobe_bin=engine.ffprobe_bin, probe_meta=True)
                return self.send_json(scanned)
            except Exception as e:
                return self.send_json({"error": str(e)}, status_code=400)

        elif path == "/api/process":
            if not component_status()["available"]:
                return self.send_json({
                    "error": "FFmpeg e FFprobe sono necessari per elaborare i file. Reinstallali dalle Impostazioni."
                }, status_code=412)
            if manager.is_running:
                return self.send_json({"error": "Un'elaborazione è già in corso"}, status_code=409)

            items = body.get("items", [])
            output_dir = body.get("output_dir", "")
            options = body.get("options", {})

            if not items:
                return self.send_json({"error": "Nessun elemento da elaborare"}, status_code=400)

            if not output_dir:
                # Default output directory: parent folder of first item + "_SaveYourStorage_Output"
                first_item_path = Path(items[0]["path"])
                output_dir = str(first_item_path.parent / "SaveYourStorage_Output")

            manager.reset(items, output_dir, options)
            thread = threading.Thread(target=manager.worker_loop, daemon=True)
            manager.worker_thread = thread
            thread.start()

            return self.send_json({"status": "started", "output_dir": output_dir})

        elif path == "/api/cancel":
            manager.cancel()
            return self.send_json({"status": "cancelling"})

        else:
            self.send_error(404, "Not Found")

def run_server(port=5678):
    server_address = ('127.0.0.1', port)
    httpd = ThreadingHTTPServer(server_address, SaveYourStorageHTTPHandler)
    print(f"[SaveYourStorage] Server desktop attivo su http://127.0.0.1:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    port = 5678
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass

    # If executed as a compiled standalone .exe, open the desktop window automatically
    if getattr(sys, 'frozen', False):
        def launch_standalone_window():
            time.sleep(1.0)
            edge_paths = [
                os.environ.get("ProgramFiles(x86)", "") + r"\Microsoft\Edge\Application\msedge.exe",
                os.environ.get("ProgramFiles", "") + r"\Microsoft\Edge\Application\msedge.exe"
            ]
            edge_bin = next((p for p in edge_paths if os.path.exists(p)), None)
            if edge_bin:
                subprocess.Popen([edge_bin, f"--app=http://127.0.0.1:{port}", "--window-size=1160,860"])
            else:
                webbrowser.open(f"http://127.0.0.1:{port}")

        threading.Thread(target=launch_standalone_window, daemon=True).start()

    run_server(port)
