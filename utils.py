from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
WORK_ROOT = DATA_DIR / "work"
ENCODED_DIR = RESULTS_DIR / "encoded"


@dataclass
class VideoMetadata:
    filename: str
    path: Path
    width: int
    height: int
    duration: float
    frame_rate: float
    file_size_bytes: int
    bitrate_bps: float

    @property
    def file_size_mb(self) -> float:
        return self.file_size_bytes / 1024 / 1024

    @property
    def bitrate_kbps(self) -> float:
        return self.bitrate_bps / 1000

    @property
    def resolution(self) -> str:
        return f"{self.width}x{self.height}"


def ensure_directories(*directories: Path) -> None:
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def safe_filename(filename: str) -> str:
    stem = Path(filename).stem
    suffix = Path(filename).suffix.lower()
    safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", stem).strip("._")
    return f"{safe_stem or 'video'}{suffix or '.mp4'}"


def session_workdir(session_id: str) -> Path:
    directory = WORK_ROOT / session_id
    ensure_directories(directory, directory / "uploads")
    return directory


def session_outputdir(session_id: str) -> Path:
    directory = ENCODED_DIR / session_id
    ensure_directories(directory)
    return directory


def find_tool(name: str) -> str | None:
    path = shutil.which(name)

    if path:
        return path

    winget_packages = (
        Path.home()
        / "AppData"
        / "Local"
        / "Microsoft"
        / "WinGet"
        / "Packages"
    )

    if not winget_packages.exists():
        return None

    executable = f"{name}.exe"

    for root, _, files in os.walk(winget_packages):
        if executable in files and "Gyan.FFmpeg" in root:
            return str(Path(root) / executable)

    return None


def run_command(command: Iterable[str], label: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(command),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"{label} failed:\n{message}")

    return result


def parse_fraction(value: str | None) -> float:
    if not value or value == "0/0":
        return 0.0

    try:
        return float(Fraction(value))
    except (ValueError, ZeroDivisionError):
        return 0.0


def probe_video(ffprobe_path: str, path: Path, filename: str | None = None) -> VideoMetadata:
    if not path.exists():
        raise FileNotFoundError(f"Video file does not exist: {path}")

    result = run_command(
        [
            ffprobe_path,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,r_frame_rate,duration,bit_rate:format=duration,bit_rate,size",
            "-of",
            "json",
            str(path),
        ],
        "Reading video metadata",
    )

    data = json.loads(result.stdout)
    streams = data.get("streams", [])

    if not streams:
        raise ValueError(f"No video stream found in {filename or path.name}")

    stream = streams[0]
    fmt = data.get("format", {})
    file_size = int(fmt.get("size") or path.stat().st_size)
    duration = float(stream.get("duration") or fmt.get("duration") or 0)
    bitrate = float(stream.get("bit_rate") or fmt.get("bit_rate") or 0)
    width = int(stream.get("width") or 0)
    height = int(stream.get("height") or 0)

    if width <= 0 or height <= 0:
        raise ValueError(f"Invalid video resolution for {filename or path.name}")

    if bitrate <= 0 and duration > 0:
        bitrate = file_size * 8 / duration

    return VideoMetadata(
        filename=filename or path.name,
        path=path,
        width=width,
        height=height,
        duration=duration,
        frame_rate=parse_fraction(stream.get("r_frame_rate")),
        file_size_bytes=file_size,
        bitrate_bps=bitrate,
    )


def save_uploaded_file(uploaded_file, upload_dir: Path) -> Path:
    ensure_directories(upload_dir)
    output_path = upload_dir / safe_filename(uploaded_file.name)
    counter = 1

    while output_path.exists():
        output_path = upload_dir / f"{output_path.stem}_{counter}{output_path.suffix}"
        counter += 1

    with output_path.open("wb") as output:
        output.write(uploaded_file.getbuffer())

    return output_path


def list_ffmpeg_encoders(ffmpeg_path: str) -> set[str]:
    result = run_command(
        [ffmpeg_path, "-hide_banner", "-encoders"],
        "Reading FFmpeg encoders",
    )

    return {
        line.split()[1]
        for line in result.stdout.splitlines()
        if line.startswith(" ") and len(line.split()) > 1
    }


def format_bytes(size_bytes: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024 or unit == "GB":
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024

    return f"{size_bytes:.2f} GB"
