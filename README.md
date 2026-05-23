# exploring-vvc-compression# Exploring VVC Compression Efficiency

## Overview

This project compares HEVC (H.265) and VVC (H.266) video compression efficiency using FFmpeg.

The system:

- Encodes uploaded videos using HEVC and VVC
- Computes quality metrics (PSNR, SSIM)
- Measures compression ratio
- Calculates bitrate savings
- Visualizes results through an interactive Streamlit dashboard

---

## Features

- Video upload
- HEVC encoding (libx265)
- VVC encoding (libvvenc)
- PSNR calculation
- SSIM calculation
- Compression ratio analysis
- Bitrate saving analysis
- Interactive dashboard
- CSV export
- Encoded video download

---

## Project Structure

```
exploring-vvc-compression-efficiency/

├── app/
│   └── streamlit_app.py

├── src/
│   ├── hevc_encoder.py
│   ├── vvc_encoder.py
│   └── quality_metrics.py

├── data/
│   ├── raw/
│   ├── hevc/
│   └── vvc/

├── results/

├── requirements.txt

└── README.md
```

---

## Installation

### 1. Clone repository

```bash
git clone <repository-url>
cd exploring-vvc-compression-efficiency
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Install FFmpeg

Download FFmpeg and ensure it is added to PATH.

Verify:

```bash
ffmpeg -version
```

---

## Run Application

```bash
streamlit run app/streamlit_app.py
```

---

## Usage

1. Upload an MP4 video
2. Select QP value
3. Click Encode Video
4. Compare HEVC and VVC results
5. Download CSV report
6. Download encoded videos

---

## Evaluation Metrics

- PSNR
- SSIM
- Compression Ratio
- Bitrate Saving
- File Size
- Encoding Time

---

## Example Results

Typical results:

| Metric | HEVC | VVC |
|----------|----------|----------|
| PSNR | 36.28 dB | 32.98 dB |
| SSIM | 0.9599 | 0.9289 |
| Compression Ratio | 2.31x | 4.04x |
| File Size | 0.16 MB | 0.09 MB |
| Bitrate Saving | - | 42.74% |

---

## Authors

HUST Multimedia Data Compression Project

2026-efficiency