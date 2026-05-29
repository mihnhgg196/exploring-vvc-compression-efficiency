from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from utils import VideoMetadata, probe_video, run_command


@dataclass
class ObjectiveMetrics:
    psnr: float | None
    ssim: float | None


@dataclass
class CompressionMetrics:
    encoded_size_bytes: int
    compression_ratio: float | None
    encoded_bitrate_bps: float
    bitrate_savings_percent: float | None
    psnr_per_mbps: float | None
    ssim_per_mbps: float | None


def _quality_filter(metric_name: str, width: int, height: int) -> str:
    return (
        f"[0:v]settb=AVTB,setpts=PTS-STARTPTS[ref];"
        f"[1:v]scale={width}:{height}:flags=bicubic,settb=AVTB,setpts=PTS-STARTPTS[dist];"
        f"[ref][dist]{metric_name}"
    )


def compute_psnr(ffmpeg_path: str, original: Path, encoded: Path, width: int, height: int) -> float | None:
    result = run_command(
        [
            ffmpeg_path,
            "-i",
            str(original),
            "-i",
            str(encoded),
            "-filter_complex",
            _quality_filter("psnr", width, height),
            "-f",
            "null",
            "-",
        ],
        "PSNR calculation",
    )

    match = re.search(r"average:([0-9.]+|inf)", result.stderr)

    if not match:
        return None

    value = match.group(1)
    return float("inf") if value == "inf" else float(value)


def compute_ssim(ffmpeg_path: str, original: Path, encoded: Path, width: int, height: int) -> float | None:
    result = run_command(
        [
            ffmpeg_path,
            "-i",
            str(original),
            "-i",
            str(encoded),
            "-filter_complex",
            _quality_filter("ssim", width, height),
            "-f",
            "null",
            "-",
        ],
        "SSIM calculation",
    )

    match = re.search(r"All:([0-9.]+)", result.stderr)
    return float(match.group(1)) if match else None


def compute_objective_metrics(
    ffmpeg_path: str,
    original: Path,
    encoded: Path,
    original_metadata: VideoMetadata,
) -> ObjectiveMetrics:
    if original_metadata.width <= 0 or original_metadata.height <= 0:
        raise ValueError("Original video metadata has invalid resolution")

    psnr = compute_psnr(
        ffmpeg_path,
        original,
        encoded,
        original_metadata.width,
        original_metadata.height,
    )
    ssim = compute_ssim(
        ffmpeg_path,
        original,
        encoded,
        original_metadata.width,
        original_metadata.height,
    )

    return ObjectiveMetrics(psnr=psnr, ssim=ssim)


def compute_compression_metrics(
    ffprobe_path: str,
    original_metadata: VideoMetadata,
    encoded_path: Path,
    quality: ObjectiveMetrics,
) -> CompressionMetrics:
    encoded_metadata = probe_video(ffprobe_path, encoded_path)
    encoded_size = encoded_path.stat().st_size
    compression_ratio = None
    bitrate_savings = None

    if encoded_size > 0:
        compression_ratio = original_metadata.file_size_bytes / encoded_size

    if original_metadata.bitrate_bps > 0:
        bitrate_savings = (
            (original_metadata.bitrate_bps - encoded_metadata.bitrate_bps)
            / original_metadata.bitrate_bps
        ) * 100

    encoded_mbps = encoded_metadata.bitrate_bps / 1_000_000
    psnr_per_mbps = quality.psnr / encoded_mbps if quality.psnr and encoded_mbps > 0 else None
    ssim_per_mbps = quality.ssim / encoded_mbps if quality.ssim and encoded_mbps > 0 else None

    return CompressionMetrics(
        encoded_size_bytes=encoded_size,
        compression_ratio=compression_ratio,
        encoded_bitrate_bps=encoded_metadata.bitrate_bps,
        bitrate_savings_percent=bitrate_savings,
        psnr_per_mbps=psnr_per_mbps,
        ssim_per_mbps=ssim_per_mbps,
    )
