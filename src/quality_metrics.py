import subprocess
import re
import os
import shutil


def find_ffmpeg():
    path_ffmpeg = shutil.which("ffmpeg")

    if path_ffmpeg:
        return path_ffmpeg

    winget_packages = os.path.join(
        os.path.expanduser("~"),
        "AppData",
        "Local",
        "Microsoft",
        "WinGet",
        "Packages"
    )

    if not os.path.isdir(winget_packages):
        return "ffmpeg"

    for root, _, files in os.walk(winget_packages):
        if "ffmpeg.exe" in files and "Gyan.FFmpeg" in root:
            return os.path.join(root, "ffmpeg.exe")

    return "ffmpeg"


def calculate_psnr(original, compressed, ffmpeg_executable=None):
    ffmpeg_executable = ffmpeg_executable or find_ffmpeg()

    cmd = [
        ffmpeg_executable,
        "-i", original,
        "-i", compressed,
        "-lavfi", "psnr",
        "-f", "null",
        "-"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    output = result.stderr

    match = re.search(
        r"average:([0-9.]+)",
        output
    )

    if match:
        return float(match.group(1))

    return None


def calculate_ssim(original, compressed, ffmpeg_executable=None):
    ffmpeg_executable = ffmpeg_executable or find_ffmpeg()

    cmd = [
        ffmpeg_executable,
        "-i", original,
        "-i", compressed,
        "-lavfi", "ssim",
        "-f", "null",
        "-"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    output = result.stderr

    match = re.search(
        r"All:([0-9.]+)",
        output
    )

    if match:
        return float(match.group(1))

    return None


def get_file_size(path):

    return os.path.getsize(path)


def compression_ratio(original, compressed):

    original_size = get_file_size(original)
    compressed_size = get_file_size(compressed)

    return original_size / compressed_size


def bitrate_saving(hevc_file, vvc_file):

    hevc_size = get_file_size(hevc_file)
    vvc_size = get_file_size(vvc_file)

    return (
        (hevc_size - vvc_size)
        / hevc_size
    ) * 100


def evaluate_video(
    original,
    hevc_file,
    vvc_file,
    ffmpeg_executable=None
):
    ffmpeg_executable = ffmpeg_executable or find_ffmpeg()

    results = {

        "hevc_psnr":
            calculate_psnr(
                original,
                hevc_file,
                ffmpeg_executable
            ),

        "vvc_psnr":
            calculate_psnr(
                original,
                vvc_file,
                ffmpeg_executable
            ),

        "hevc_ssim":
            calculate_ssim(
                original,
                hevc_file,
                ffmpeg_executable
            ),

        "vvc_ssim":
            calculate_ssim(
                original,
                vvc_file,
                ffmpeg_executable
            ),

        "hevc_cr":
            compression_ratio(
                original,
                hevc_file
            ),

        "vvc_cr":
            compression_ratio(
                original,
                vvc_file
            ),

        "bitrate_saving":
            bitrate_saving(
                hevc_file,
                vvc_file
            )

    }

    return results
