import subprocess
import re
import os


def calculate_psnr(original, compressed):

    cmd = [
        "ffmpeg",
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


def calculate_ssim(original, compressed):

    cmd = [
        "ffmpeg",
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
    vvc_file
):

    results = {

        "hevc_psnr":
            calculate_psnr(
                original,
                hevc_file
            ),

        "vvc_psnr":
            calculate_psnr(
                original,
                vvc_file
            ),

        "hevc_ssim":
            calculate_ssim(
                original,
                hevc_file
            ),

        "vvc_ssim":
            calculate_ssim(
                original,
                vvc_file
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