"""
File and Media Scanner for SaveYourStorage.
Developed by Giuseppe Antonino Cotroneo (https://ko-fi.com/cotrox)

Scans single files or entire folders to collect media metadata.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

VIDEO_EXTENSIONS = {
    ".mp4", ".mov", ".mkv", ".avi", ".webm", ".flv",
    ".wmv", ".m4v", ".ts", ".3gp", ".m2ts", ".ogv"
}

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff",
    ".tif", ".heic", ".heif", ".gif", ".avif"
}

def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def format_duration(seconds: float) -> str:
    if not seconds or seconds < 0:
        return "00:00:00"
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hrs:02d}:{mins:02d}:{secs:02d}"

def get_media_probe(file_path: str, ffprobe_bin: str = "ffprobe") -> dict:
    """Uses ffprobe to inspect video/audio/image properties."""
    meta = {
        "duration": 0.0,
        "duration_str": "00:00:00",
        "width": 0,
        "height": 0,
        "resolution": "Unknown",
        "video_codec": "None",
        "audio_codec": "None",
        "has_audio": False,
        "fps": 0.0,
        "bitrate": 0
    }
    
    cmd = [
        ffprobe_bin,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(file_path)
    ]
    
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            startupinfo=startupinfo,
            timeout=10
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            format_info = data.get("format", {})
            try:
                meta["duration"] = float(format_info.get("duration", 0))
                meta["duration_str"] = format_duration(meta["duration"])
            except (ValueError, TypeError):
                pass
            
            try:
                meta["bitrate"] = int(format_info.get("bit_rate", 0))
            except (ValueError, TypeError):
                pass

            for s in data.get("streams", []):
                codec_type = s.get("codec_type")
                if codec_type == "video" and meta["video_codec"] == "None":
                    meta["video_codec"] = s.get("codec_name", "unknown")
                    meta["width"] = s.get("width", 0)
                    meta["height"] = s.get("height", 0)
                    if meta["width"] and meta["height"]:
                        meta["resolution"] = f"{meta['width']}x{meta['height']}"
                    
                    # Compute fps
                    r_frame_rate = s.get("r_frame_rate", "")
                    if "/" in r_frame_rate:
                        num, den = r_frame_rate.split("/")
                        try:
                            if float(den) > 0:
                                meta["fps"] = round(float(num) / float(den), 2)
                        except (ValueError, ZeroDivisionError):
                            pass
                elif codec_type == "audio":
                    meta["has_audio"] = True
                    if meta["audio_codec"] == "None":
                        meta["audio_codec"] = s.get("codec_name", "unknown")
    except Exception as e:
        # Silently fail back to defaults if probe fails
        pass

    return meta

def scan_target(target_path: str, ffprobe_bin: str = "ffprobe", probe_meta: bool = True) -> dict:
    """
    Scans a file or folder and returns itemized metadata.
    """
    p = Path(target_path)
    if not p.exists():
        raise FileNotFoundError(f"Percorso non trovato: {target_path}")

    is_dir = p.is_dir()
    files = []

    if is_dir:
        for root, _, filenames in os.walk(p):
            for fname in filenames:
                fp = Path(root) / fname
                ext = fp.suffix.lower()
                if ext in VIDEO_EXTENSIONS or ext in IMAGE_EXTENSIONS:
                    files.append(fp)
    else:
        ext = p.suffix.lower()
        if ext in VIDEO_EXTENSIONS or ext in IMAGE_EXTENSIONS:
            files.append(p)
        else:
            raise ValueError(f"Formato non supportato: {ext}")

    items = []
    total_raw_bytes = 0

    for idx, f in enumerate(files):
        stat = f.stat()
        size_bytes = stat.st_size
        total_raw_bytes += size_bytes
        ext = f.suffix.lower()
        is_video = ext in VIDEO_EXTENSIONS
        is_image = ext in IMAGE_EXTENSIONS

        item_meta = {
            "id": f"item_{idx}_{f.name}",
            "name": f.name,
            "path": str(f.resolve()),
            "extension": ext,
            "type": "video" if is_video else "image",
            "size_bytes": size_bytes,
            "size_formatted": format_size(size_bytes),
            "status": "pending",  # pending, processing, done, error
            "duration": 0.0,
            "duration_str": "00:00:00",
            "resolution": "Unknown",
            "has_audio": False,
            "video_codec": "None",
            "audio_codec": "None",
            "output_path": "",
            "output_size_bytes": 0,
            "output_size_formatted": "",
            "saved_bytes": 0,
            "saved_percentage": 0.0,
            "error_message": ""
        }

        # If it's a single file, probe deeply right away. If it's a folder, do fast probe or probe on demand.
        if probe_meta and (not is_dir or len(files) <= 10):
            probe_data = get_media_probe(str(f), ffprobe_bin)
            item_meta.update(probe_data)

        items.append(item_meta)

    return {
        "target_path": str(p.resolve()),
        "is_folder": is_dir,
        "count": len(items),
        "total_size_bytes": total_raw_bytes,
        "total_size_formatted": format_size(total_raw_bytes),
        "items": items
    }
