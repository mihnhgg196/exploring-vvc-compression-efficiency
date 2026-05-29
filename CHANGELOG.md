# Changelog

## 2026-05-27

- Aligned the dashboard implementation with README scope by removing unused zoom-inspector code, fixing skipped-codec progress reporting, avoiding upload overwrite on duplicate filenames, and clarifying output storage/audio behavior in README.
- Replaced the legacy AVC/HEVC `app/streamlit_app.py` implementation with a launcher for the HEVC/VVC root dashboard to avoid showing AVC in the VVC workflow.
- Moved dashboard working files from the system temp directory to `data/work/` and encoded outputs to `results/encoded/`.
- Hardened video probing, encoder validation, resolution parsing, target bitrate checks, and PSNR parsing for infinite scores.
- Updated README run instructions to prefer `python -m streamlit run app.py` for environments where the `streamlit` command is not on PATH.
- Added a complete modular HEVC/VVC dashboard system with `app.py`, `encoder.py`, `metrics.py`, and `utils.py`, including multi-upload, metadata extraction, configurable encoding, PSNR/SSIM metrics, compression analysis, Plotly visualizations, CSV export, and encoded video downloads.
- Fixed metric card text contrast in dark theme for input information and overview sections.
- Changed Pixel Inspector 400% from manual X/Y controls to a drag-and-drop image region selector with live AVC/HEVC canvas zoom.
- Redesigned the Streamlit app for AVC vs HEVC comparison with split-screen frame slider, PSNR/SSIM/VMAF metric visualization, and a 400% pixel inspector for artifact analysis.
- Improved Streamlit UI with sidebar workflow controls, source preview, progress feedback, result tabs, styled metrics, and cleaner chart/table layouts.
- Fixed Streamlit app startup handling for missing FFmpeg.
- Added validation for required FFmpeg encoders: `libx265` and `libvvenc`.
- Added automatic detection for FFmpeg installed by Winget when PATH has not refreshed.
- Updated encoding calls to surface FFmpeg errors in the Streamlit UI.
- Switched app file paths to project-root absolute paths for reliable execution.
- Made metric formatting tolerate unavailable PSNR, SSIM, compression, or bitrate values.
