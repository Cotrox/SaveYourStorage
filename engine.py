"""
FFmpeg Conversion & Optimization Engine for SaveYourStorage.
Developed by Giuseppe Antonino Cotroneo (https://ko-fi.com/cotrox)

Handles video speedup, trimming, format conversion, compression, and upscaling.
"""

import os
import sys
import re
import shutil
import threading
import subprocess
from pathlib import Path
from typing import Callable, Optional

# File extensions
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".flv", ".wmv", ".m4v", ".ts", ".3gp"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif", ".heic", ".heif", ".gif", ".avif"}

def build_atempo_filter(speed: float) -> str:
    """
    FFmpeg's atempo filter only supports values between 0.5 and 2.0.
    For speeds > 2.0, multiple atempo filters must be chained.
    Example: 8.0x -> atempo=2.0,atempo=2.0,atempo=2.0
    """
    filters = []
    current = float(speed)
    
    while current > 2.0:
        filters.append("atempo=2.0")
        current /= 2.0
    
    while current < 0.5:
        filters.append("atempo=0.5")
        current /= 0.5
        
    filters.append(f"atempo={current:.4f}")
    return ",".join(filters)

class MediaEngine:
    def __init__(self, ffmpeg_bin: str = "ffmpeg", ffprobe_bin: str = "ffprobe"):
        self.ffmpeg_bin = ffmpeg_bin
        self.ffprobe_bin = ffprobe_bin
        self.active_process = None
        self.cancel_requested = False

    def locate_binaries(self):
        """Finds FFmpeg and FFprobe from managed, bundled, or system locations."""
        filename = lambda name: name + (".exe" if os.name == "nt" else "")
        managed_dir = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "SaveYourStorage" / "components"
        
        # If components have been explicitly uninstalled/deactivated by user
        flag_file = managed_dir / "uninstalled.flag"
        if flag_file.exists():
            self.ffmpeg_bin = ""
            self.ffprobe_bin = ""
            return {
                "ffmpeg": "",
                "ffprobe": "",
                "ffmpeg_available": False,
                "ffprobe_available": False,
                "available": False,
                "uninstalled": True
            }

        if getattr(sys, 'frozen', False):
            base_dir = Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
            exe_dir = Path(sys.executable).resolve().parent
            locations = (
                managed_dir,
                base_dir / "bin",
                exe_dir / "bin",
                exe_dir / "_internal" / "bin",
                Path(__file__).resolve().parent / "bin"
            )
        else:
            base_dir = Path(__file__).resolve().parent
            locations = (managed_dir, base_dir / "bin")

        for directory in locations:
            candidate = directory / filename("ffmpeg")
            if candidate.exists():
                self.ffmpeg_bin = str(candidate)
                break
        else:
            self.ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"

        for directory in locations:
            candidate = directory / filename("ffprobe")
            if candidate.exists():
                self.ffprobe_bin = str(candidate)
                break
        else:
            self.ffprobe_bin = shutil.which("ffprobe") or "ffprobe"

        ffmpeg_ok = bool((Path(self.ffmpeg_bin).is_file()) or (self.ffmpeg_bin != "ffmpeg" and shutil.which(self.ffmpeg_bin)))
        ffprobe_ok = bool((Path(self.ffprobe_bin).is_file()) or (self.ffprobe_bin != "ffprobe" and shutil.which(self.ffprobe_bin)))

        return {
            "ffmpeg": self.ffmpeg_bin if ffmpeg_ok else "",
            "ffprobe": self.ffprobe_bin if ffprobe_ok else "",
            "ffmpeg_available": ffmpeg_ok,
            "ffprobe_available": ffprobe_ok,
            "available": bool(ffmpeg_ok and ffprobe_ok),
            "uninstalled": False
        }

    def cancel(self):
        self.cancel_requested = True
        if self.active_process:
            try:
                self.active_process.terminate()
            except Exception:
                try:
                    self.active_process.kill()
                except Exception:
                    pass

    def process_item(
        self,
        item: dict,
        output_dir: str,
        options: dict,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> dict:
        """
        Executes safe media optimization/conversion according to options.
        Options dictionary schema:
        {
            "format": "original" | "mp4" | "mov" | "mkv" | "webm" | "webp" | "jpg" | "png",
            "speed": 1.0 | 1.25 | 1.5 | 2.0 | 3.0 | 5.0 | 8.0,
            "audio_mode": "keep_speed" | "remove_audio" | "keep_normal",
            "quality_preset": "visually_lossless" | "balanced" | "high_compression" | "lossless" | "custom",
            "custom_crf": 26,
            "codec": "h264" | "h265" | "vp9" | "auto",
            "scale_mode": "original" | "720p" | "1080p" | "25%" | "50%" | "75%" | "upscale_2x",
            "trim_enabled": bool,
            "trim_start": float (seconds),
            "trim_end": float (seconds),
            "normal_speed_ranges": [{"start": float, "end": float}]
        }
        """
        self.cancel_requested = False
        input_path = Path(item["path"])
        if not input_path.exists():
            raise FileNotFoundError(f"Input file non trovato: {input_path}")

        out_dir_path = Path(output_dir)
        out_dir_path.mkdir(parents=True, exist_ok=True)

        is_video = item.get("type") == "video"
        is_image = item.get("type") == "image"

        target_ext = options.get("format", "original").lower()
        if target_ext == "original" or not target_ext:
            target_ext = input_path.suffix.lstrip(".").lower()

        # Build output filename safely
        base_stem = input_path.stem
        # Add modifier suffixes if sped up or trimmed
        speed = float(options.get("speed", 1.0))
        tag_parts = []
        if speed != 1.0:
            tag_parts.append(f"{speed}x")
        if options.get("audio_mode") == "remove_audio" and is_video:
            tag_parts.append("muted")
        
        aspect_mode = options.get("aspect_mode", "original")
        if is_video and aspect_mode != "original":
            tag_parts.append(aspect_mode.replace(":", "x"))

        if options.get("scale_mode") == "upscale_2x":
            tag_parts.append("2x_upscaled")
        elif options.get("scale_mode") in ["720p", "1080p", "25%", "50%", "75%"]:
            tag_parts.append(options.get("scale_mode"))
        if is_video and options.get("trim_enabled"):
            tag_parts.append("trimmed")

        tag_str = f"_{'_'.join(tag_parts)}" if tag_parts else "_optimized"
        out_filename = f"{base_stem}{tag_str}.{target_ext}"
        out_file_path = out_dir_path / out_filename

        # If file already exists, don't overwrite blindly - find unique name
        counter = 1
        while out_file_path.exists():
            out_filename = f"{base_stem}{tag_str}_{counter}.{target_ext}"
            out_file_path = out_dir_path / out_filename
            counter += 1

        cmd = [self.ffmpeg_bin, "-y", "-nostats", "-loglevel", "warning"]

        # Trimming start (fast seek input)
        trim_enabled = is_video and options.get("trim_enabled", False)
        trim_start = float(options.get("trim_start", 0.0) or 0.0)
        trim_end = float(options.get("trim_end", 0.0) or 0.0)
        total_duration = float(item.get("duration", 0.0) or 0.0)

        effective_duration = total_duration
        if trim_enabled and trim_end > trim_start:
            effective_duration = trim_end - trim_start
        source_duration = max(0.0, effective_duration)

        # Ranges use source-timeline coordinates and are converted to the
        # selected clip's local timeline for the filter graph.
        normal_ranges = []
        if is_video and speed != 1.0:
            clip_start = trim_start if trim_enabled else 0.0
            clip_duration = source_duration
            for raw_range in options.get("normal_speed_ranges", []):
                try:
                    range_start = max(0.0, float(raw_range.get("start", 0.0)) - clip_start)
                    range_end = min(clip_duration, float(raw_range.get("end", 0.0)) - clip_start)
                except (AttributeError, TypeError, ValueError):
                    continue
                if range_end - range_start >= 0.05:
                    normal_ranges.append((range_start, range_end))
            normal_ranges.sort()

            merged_ranges = []
            for range_start, range_end in normal_ranges:
                if merged_ranges and range_start <= merged_ranges[-1][1]:
                    merged_ranges[-1] = (merged_ranges[-1][0], max(merged_ranges[-1][1], range_end))
                else:
                    merged_ranges.append((range_start, range_end))
            normal_ranges = merged_ranges

        normal_duration = sum(end - start for start, end in normal_ranges)
        if speed > 0:
            effective_duration = normal_duration + max(0.0, effective_duration - normal_duration) / speed

        if trim_enabled and trim_start > 0:
            cmd.extend(["-ss", f"{trim_start:.3f}"])

        cmd.extend(["-i", str(input_path)])

        if trim_enabled and trim_end > trim_start:
            cmd.extend(["-t", f"{trim_end - trim_start:.3f}"])

        video_filters = []
        audio_filters = []

        # Video Speedup filter
        has_segment_timing = bool(normal_ranges)
        if is_video and speed != 1.0 and not has_segment_timing:
            video_filters.append(f"setpts={1.0 / speed:.6f}*PTS")

        # Aspect Ratio, Orientation & Crop/Reframing filters
        if is_video and aspect_mode != "original":
            fit_mode = options.get("aspect_fit", "crop_fill")
            offset_pct = max(0.0, min(100.0, float(options.get("crop_offset", 50)))) / 100.0

            if aspect_mode == "9:16":
                if fit_mode == "crop_fill":
                    video_filters.append(
                        f"crop=w='trunc(if(gt(a,9/16),ih*9/16,iw)/2)*2':"
                        f"h='trunc(if(gt(a,9/16),ih,iw*16/9)/2)*2':"
                        f"x='(in_w-out_w)*{offset_pct:.4f}':"
                        f"y='(in_h-out_h)*{offset_pct:.4f}'"
                    )
                else:  # black_pad
                    video_filters.append(
                        f"pad=w='trunc(if(gt(a,9/16),iw,ih*9/16)/2)*2':"
                        f"h='trunc(if(gt(a,9/16),iw*16/9,ih)/2)*2':"
                        f"x='(ow-iw)/2':y='(oh-ih)/2':color=black"
                    )
            elif aspect_mode == "16:9":
                if fit_mode == "crop_fill":
                    video_filters.append(
                        f"crop=w='trunc(if(gt(a,16/9),ih*16/9,iw)/2)*2':"
                        f"h='trunc(if(gt(a,16/9),ih,iw*9/16)/2)*2':"
                        f"x='(in_w-out_w)*{offset_pct:.4f}':"
                        f"y='(in_h-out_h)*{offset_pct:.4f}'"
                    )
                else:  # black_pad
                    video_filters.append(
                        f"pad=w='trunc(if(gt(a,16/9),iw,ih*16/9)/2)*2':"
                        f"h='trunc(if(gt(a,16/9),iw*9/16,ih)/2)*2':"
                        f"x='(ow-iw)/2':y='(oh-ih)/2':color=black"
                    )
            elif aspect_mode == "1:1":
                if fit_mode == "crop_fill":
                    video_filters.append(
                        f"crop=w='trunc(min(iw,ih)/2)*2':"
                        f"h='trunc(min(iw,ih)/2)*2':"
                        f"x='(in_w-out_w)*{offset_pct:.4f}':"
                        f"y='(in_h-out_h)*{offset_pct:.4f}'"
                    )
                else:
                    video_filters.append(
                        f"pad=w='trunc(max(iw,ih)/2)*2':"
                        f"h='trunc(max(iw,ih)/2)*2':"
                        f"x='(ow-iw)/2':y='(oh-ih)/2':color=black"
                    )
            elif aspect_mode == "4:5":
                if fit_mode == "crop_fill":
                    video_filters.append(
                        f"crop=w='trunc(if(gt(a,4/5),ih*4/5,iw)/2)*2':"
                        f"h='trunc(if(gt(a,4/5),ih,iw*5/4)/2)*2':"
                        f"x='(in_w-out_w)*{offset_pct:.4f}':"
                        f"y='(in_h-out_h)*{offset_pct:.4f}'"
                    )
                else:
                    video_filters.append(
                        f"pad=w='trunc(if(gt(a,4/5),iw,ih*4/5)/2)*2':"
                        f"h='trunc(if(gt(a,4/5),iw*5/4,ih)/2)*2':"
                        f"x='(ow-iw)/2':y='(oh-ih)/2':color=black"
                    )
            elif aspect_mode == "custom":
                cw_pct = max(10.0, min(100.0, float(options.get("custom_crop_w", 100)))) / 100.0
                ch_pct = max(10.0, min(100.0, float(options.get("custom_crop_h", 100)))) / 100.0
                cx_pct = max(0.0, min(90.0, float(options.get("custom_crop_x", 0)))) / 100.0
                cy_pct = max(0.0, min(90.0, float(options.get("custom_crop_y", 0)))) / 100.0
                video_filters.append(
                    f"crop=w='trunc(iw*{cw_pct:.4f}/2)*2':"
                    f"h='trunc(ih*{ch_pct:.4f}/2)*2':"
                    f"x='trunc(iw*{cx_pct:.4f}/2)*2':"
                    f"y='trunc(ih*{cy_pct:.4f}/2)*2'"
                )

        # Scaling / Upscaling filters (Orientation-aware)
        scale_mode = options.get("scale_mode", "original")
        if scale_mode == "720p":
            video_filters.append("scale='if(gte(iw,ih),-2,720)':'if(gte(iw,ih),720,-2)'")
        elif scale_mode == "1080p":
            video_filters.append("scale='if(gte(iw,ih),-2,1080)':'if(gte(iw,ih),1080,-2)'")
        elif scale_mode == "25%":
            video_filters.append("scale=trunc(iw*0.25/2)*2:trunc(ih*0.25/2)*2")
        elif scale_mode == "50%":
            video_filters.append("scale=trunc(iw*0.5/2)*2:trunc(ih*0.5/2)*2")
        elif scale_mode == "75%":
            video_filters.append("scale=trunc(iw*0.75/2)*2:trunc(ih*0.75/2)*2")
        elif scale_mode == "upscale_2x":
            # High-grade Lanczos upscaling with slight unsharp enhancement
            video_filters.append("scale=iw*2:ih*2:flags=lanczos")
            video_filters.append("unsharp=5:5:0.5:5:5:0.0")

        # Audio handling
        audio_mode = options.get("audio_mode", "keep_speed")
        if is_video:
            if audio_mode == "remove_audio" or not item.get("has_audio", False):
                cmd.append("-an")
            elif audio_mode == "keep_speed" and not has_segment_timing:
                if speed != 1.0:
                    audio_filters.append(build_atempo_filter(speed))
            # "keep_normal" leaves audio untouched or normal
        
        # Apply filters. Segment timing uses one concat graph so each normal
        # interval keeps its original duration while other intervals speed up.
        if has_segment_timing:
            segments = [(0.0, normal_ranges[0][0], False)]
            for index, (normal_start, normal_end) in enumerate(normal_ranges):
                segments.append((normal_start, normal_end, True))
                next_start = normal_ranges[index + 1][0] if index + 1 < len(normal_ranges) else source_duration
                if normal_end < next_start:
                    segments.append((normal_end, next_start, False))
            segments = [(start, end, normal) for start, end, normal in segments if end - start >= 0.05]

            graph = []
            video_labels = []
            audio_labels = []
            has_timed_audio = is_video and item.get("has_audio", False) and audio_mode == "keep_speed"
            for index, (segment_start, segment_end, is_normal) in enumerate(segments):
                video_label = f"vseg{index}"
                video_chain = f"[0:v]trim=start={segment_start:.3f}:end={segment_end:.3f},setpts=PTS-STARTPTS"
                if not is_normal:
                    video_chain += f",setpts={1.0 / speed:.6f}*PTS"
                graph.append(f"{video_chain}[{video_label}]")
                video_labels.append(f"[{video_label}]")

                if has_timed_audio:
                    audio_label = f"aseg{index}"
                    audio_chain = f"[0:a]atrim=start={segment_start:.3f}:end={segment_end:.3f},asetpts=PTS-STARTPTS"
                    if not is_normal:
                        audio_chain += f",{build_atempo_filter(speed)}"
                    graph.append(f"{audio_chain}[{audio_label}]")
                    audio_labels.append(f"[{audio_label}]")

            graph.append("".join(video_labels) + f"concat=n={len(video_labels)}:v=1:a=0[vbase]")
            video_output = "vbase"
            if video_filters:
                graph.append(f"[vbase]{','.join(video_filters)}[vout]")
                video_output = "vout"

            cmd.extend(["-filter_complex", ";".join(graph), "-map", f"[{video_output}]"])
            if has_timed_audio:
                graph_audio = "".join(audio_labels) + f"concat=n={len(audio_labels)}:v=0:a=1[aout]"
                cmd[cmd.index("-filter_complex") + 1] += ";" + graph_audio
                cmd.extend(["-map", "[aout]"])
            elif audio_mode == "remove_audio" or not item.get("has_audio", False):
                cmd.append("-an")
            else:
                cmd.extend(["-map", "0:a?"])
        else:
            if video_filters:
                cmd.extend(["-vf", ",".join(video_filters)])
            if audio_filters:
                cmd.extend(["-af", ",".join(audio_filters)])

        # Codec & Quality encoding parameters
        if is_video:
            codec_choice = options.get("codec", "auto")
            preset_choice = options.get("quality_preset", "balanced")
            
            # Choose video encoder
            if target_ext == "webm":
                cmd.extend(["-c:v", "libvpx-vp9"])
            elif codec_choice == "h265" or (codec_choice == "auto" and preset_choice in ["balanced", "high_compression"]):
                cmd.extend(["-c:v", "libx265", "-tag:v", "hvc1"])
            else:
                cmd.extend(["-c:v", "libx264"])

            # CRF / Quality setting
            if preset_choice == "lossless":
                if target_ext == "webm":
                    cmd.extend(["-lossless", "1"])
                else:
                    cmd.extend(["-crf", "0"])
            elif preset_choice == "visually_lossless":
                # CRF 18-20 is visually indistinguishable from source but removes redundant bits
                crf = "21" if "libx265" in cmd else "18"
                cmd.extend(["-crf", crf, "-preset", "medium"])
            elif preset_choice == "balanced":
                # CRF 26 with H.265 produces huge storage savings with very high fidelity
                crf = "26" if "libx265" in cmd else "23"
                cmd.extend(["-crf", crf, "-preset", "medium"])
            elif preset_choice == "high_compression":
                # Maximum storage savings
                crf = "32" if "libx265" in cmd else "28"
                cmd.extend(["-crf", crf, "-preset", "fast"])
            elif preset_choice == "custom":
                custom_crf = str(options.get("custom_crf", 24))
                cmd.extend(["-crf", custom_crf, "-preset", "medium"])

            # Audio codec
            if "-an" not in cmd and item.get("has_audio", False):
                if target_ext == "webm":
                    cmd.extend(["-c:a", "libopus", "-b:a", "128k"])
                else:
                    cmd.extend(["-c:a", "aac", "-b:a", "128k"])

            # Web optimization: move metadata header to start of file
            if target_ext in ["mp4", "mov", "m4v"]:
                cmd.extend(["-movflags", "+faststart"])

        elif is_image:
            # Image encoding
            quality_preset = options.get("quality_preset", "balanced")
            cmd.extend(["-frames:v", "1"])
            if target_ext == "webp":
                if quality_preset == "lossless":
                    cmd.extend(["-lossless", "1"])
                elif quality_preset == "visually_lossless":
                    cmd.extend(["-quality", "92"])
                elif quality_preset == "balanced":
                    cmd.extend(["-quality", "80"])
                else:
                    cmd.extend(["-quality", "65"])
            elif target_ext in ["jpg", "jpeg"]:
                q_val = "2" if quality_preset in ["lossless", "visually_lossless"] else "4"
                cmd.extend(["-q:v", q_val])

        # Report progress through pipe
        cmd.extend(["-progress", "pipe:1", str(out_file_path)])

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            startupinfo=startupinfo
        )
        self.active_process = process

        stderr_lines = []
        def drain_stderr(pipe):
            try:
                for l in pipe:
                    stderr_lines.append(l)
            except Exception:
                pass

        stderr_thread = threading.Thread(target=drain_stderr, args=(process.stderr,), daemon=True)
        stderr_thread.start()

        time_pattern = re.compile(r"out_time_ms=(\d+)")

        try:
            for line in process.stdout:
                if self.cancel_requested:
                    process.terminate()
                    break
                line = line.strip()
                match = time_pattern.search(line)
                if match and effective_duration > 0 and progress_callback:
                    out_ms = int(match.group(1))
                    out_sec = out_ms / 1_000_000.0
                    pct = min(99.0, max(0.0, (out_sec / effective_duration) * 100.0))
                    progress_callback(pct, f"Elaborazione: {pct:.1f}%")

            process.wait()
            stderr_thread.join(timeout=1.0)
        except Exception as e:
            if not self.cancel_requested:
                raise e
        finally:
            self.active_process = None

        if self.cancel_requested:
            if out_file_path.exists():
                try:
                    out_file_path.unlink()
                except Exception:
                    pass
            raise InterruptedError("Operazione interrotta dall'utente.")

        if process.returncode != 0:
            err_msg = "".join(stderr_lines)[-500:]
            raise RuntimeError(f"FFmpeg error ({process.returncode}): {err_msg}")

        # Gather output stats
        out_stat = out_file_path.stat()
        out_size = out_stat.st_size
        in_size = item["size_bytes"]
        saved_bytes = in_size - out_size
        saved_pct = (saved_bytes / in_size * 100.0) if in_size > 0 else 0.0

        if progress_callback:
            progress_callback(100.0, "Completato con successo!")

        return {
            "output_path": str(out_file_path.resolve()),
            "output_filename": out_filename,
            "output_size_bytes": out_size,
            "saved_bytes": saved_bytes,
            "saved_percentage": round(saved_pct, 1)
        }
