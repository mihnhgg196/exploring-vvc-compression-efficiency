from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from utils import run_command


VVC_PRESET_MAP = {
    "faster": "0",
    "veryfast": "0",
    "fast": "1",
    "medium": "2",
    "slow": "3",
    "slower": "4",
}


CODEC_ENCODERS = {
    "HEVC": "libx265",
    "VVC": "libvvenc",
}


@dataclass
class EncodingResult:
    codec: str
    output_path: Path
    encoding_time_seconds: float


def scale_filter(resolution: str) -> list[str]:
    if resolution == "Original":
        return []

    try:
        width, height = resolution.lower().split("x", maxsplit=1)
        width_int = int(width)
        height_int = int(height)
    except ValueError as exc:
        raise ValueError(f"Invalid output resolution: {resolution}") from exc

    if width_int <= 0 or height_int <= 0:
        raise ValueError(f"Invalid output resolution: {resolution}")

    return ["-vf", f"scale={width_int}:{height_int}:flags=bicubic"]


def required_encoder(codec: str) -> str:
    try:
        return CODEC_ENCODERS[codec]
    except KeyError as exc:
        raise ValueError(f"Unsupported codec: {codec}") from exc


def build_encode_command(
    ffmpeg_path: str,
    input_path: Path,
    output_path: Path,
    codec: str,
    crf_qp: int,
    preset: str,
    resolution: str,
    target_bitrate_kbps: int | None,
) -> list[str]:
    video_encoder = required_encoder(codec)

    if codec == "HEVC":
        quality_args = ["-b:v", f"{target_bitrate_kbps}k"] if target_bitrate_kbps else ["-crf", str(crf_qp)]
        preset_value = preset
    elif codec == "VVC":
        quality_args = ["-b:v", f"{target_bitrate_kbps}k"] if target_bitrate_kbps else ["-qp", str(crf_qp)]
        preset_value = VVC_PRESET_MAP.get(preset, "2")

    if target_bitrate_kbps is not None and target_bitrate_kbps <= 0:
        raise ValueError("Target bitrate must be greater than 0 kbps")

    command = [
        ffmpeg_path,
        "-y",
        "-i",
        str(input_path),
        *scale_filter(resolution),
        "-c:v",
        video_encoder,
        *quality_args,
        "-preset",
        preset_value,
        "-pix_fmt",
        "yuv420p",
        "-an",
        str(output_path),
    ]

    return command


def encode_video(
    ffmpeg_path: str,
    input_path: Path,
    output_path: Path,
    codec: str,
    crf_qp: int,
    preset: str,
    resolution: str,
    target_bitrate_kbps: int | None,
) -> EncodingResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = build_encode_command(
        ffmpeg_path=ffmpeg_path,
        input_path=input_path,
        output_path=output_path,
        codec=codec,
        crf_qp=crf_qp,
        preset=preset,
        resolution=resolution,
        target_bitrate_kbps=target_bitrate_kbps,
    )

    start = time.time()
    run_command(command, f"{codec} encoding")
    elapsed = time.time() - start

    return EncodingResult(
        codec=codec,
        output_path=output_path,
        encoding_time_seconds=elapsed,
    )
