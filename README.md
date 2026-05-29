# HEVC vs VVC Compression Dashboard

This project is a Python and Streamlit system for comparing video compression efficiency between HEVC/H.265 and VVC/H.266.

The dashboard lets users upload one or more videos, encode each video with HEVC and VVC, compute objective quality metrics, measure compression performance, visualize results, and download encoded outputs.

## Features

- Multi-video upload for MP4, MOV, AVI, and MKV files
- Video metadata extraction with FFprobe
- HEVC/H.265 encoding with FFmpeg `libx265`
- VVC/H.266 encoding with FFmpeg `libvvenc` when available
- Configurable CRF/QP, preset, output resolution, and target bitrate
- PSNR and SSIM calculation with FFmpeg filters
- Compression ratio, bitrate savings, encoded bitrate, file size, and encoding time
- Plotly charts for size, compression ratio, bitrate savings, bitrate vs PSNR, and bitrate vs SSIM
- CSV export and encoded video downloads
- Graceful error reporting for missing encoders or metric failures
- Uploaded/session files are stored under `data/work/`
- Encoded outputs are stored under `results/encoded/`
- CSV reports are stored under `results/`

## Project Structure

```text
.
├── app.py              # Streamlit dashboard
├── encoder.py          # HEVC/VVC encoding helpers
├── metrics.py          # PSNR, SSIM, and compression metrics
├── utils.py            # FFmpeg discovery, metadata, workspace, helpers
├── requirements.txt
├── README.md
├── app/
│   └── streamlit_app.py # Compatibility launcher for app.py
├── data/               # Uploaded/session working files
├── results/            # Encoded outputs and CSV reports
└── src/
```

## Installation

Create and activate a Python environment, then install dependencies:

```bash
pip install -r requirements.txt
```

## FFmpeg Requirement

Install FFmpeg with FFprobe. On Windows, one practical option is:

```powershell
winget install --id Gyan.FFmpeg -e
```

Verify:

```bash
ffmpeg -version
ffprobe -version
```

The app requires:

- `libx265` for HEVC encoding
- `libvvenc` for VVC encoding

Check encoders:

```bash
ffmpeg -hide_banner -encoders
```

Look for:

```text
libx265
libvvenc
```

If `libvvenc` is missing, HEVC will still work but VVC jobs will be skipped or reported as unavailable. Install a full FFmpeg build that includes VVenC/libvvenc.

## VVenC Notes

VVC/H.266 support is still less common than HEVC. This application uses FFmpeg's `libvvenc` encoder when it is present. Standalone VVenC tools such as `vvencapp` can also encode VVC, but this dashboard currently expects FFmpeg integration for a simpler and more consistent workflow.

## Run

From the project root:

```bash
python -m streamlit run app.py
```

Open the local Streamlit URL shown in the terminal.

If the `streamlit` command is available in your shell, this also works:

```bash
streamlit run app.py
```

## Example Workflow

1. Upload one or more MP4, MOV, AVI, or MKV videos.
2. Review metadata: resolution, duration, frame rate, file size, and bitrate.
3. Select codecs: HEVC, VVC, or both.
4. Choose CRF/QP, preset, output resolution, and optional target bitrate.
5. Click `Start encoding`.
6. Review the results table and Plotly charts.
7. Download encoded videos and the CSV report.

Encoded outputs are video-only because the dashboard uses `-an` during encoding. This keeps objective video metric calculation simpler and avoids audio stream compatibility issues.

## Metrics

Compression Ratio:

```text
Original File Size / Encoded File Size
```

Bitrate Savings:

```text
((Original Bitrate - Encoded Bitrate) / Original Bitrate) * 100
```

Quality-to-bitrate:

```text
PSNR / encoded Mbps
```

PSNR and SSIM are computed by comparing the original video against each encoded output. If output resolution differs from the source, the encoded video is scaled back to source resolution during metric calculation.

## Limitations

- VVC browser playback is limited; encoded VVC files may need VLC or another compatible player.
- Metric calculation can fail for unusual files, variable timestamps, unsupported pixel formats, or damaged streams.
- VVC encoding is computationally expensive and can be much slower than HEVC.
- Encoded outputs do not include audio.
- The dashboard stores uploaded/session files under `data/work/`.
- Encoded videos are stored under `results/encoded/`.
- CSV reports are stored under `results/`.
- VMAF is not included in this modular HEVC/VVC version; PSNR and SSIM are the supported objective metrics.
