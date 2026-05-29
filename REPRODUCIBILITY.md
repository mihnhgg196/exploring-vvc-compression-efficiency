# Reproducibility Guide

## Installation

pip install -r requirements.txt

## Run Dashboard

streamlit run app.py

## Experimental Configuration

HEVC:
- Codec: libx265
- Preset: Medium
- CRF: 32

VVC:
- Codec: VVenC
- Preset: Medium
- QP: 32

## Dataset

data/raw/testvid_assignment2.mp4

## Reproduce Results

1. Launch dashboard
2. Upload dataset
3. Run HEVC encoding
4. Run VVC encoding
5. Export CSV
6. Compare metrics
