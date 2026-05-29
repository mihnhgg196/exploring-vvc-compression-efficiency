from __future__ import annotations

import uuid
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from encoder import encode_video, required_encoder
from metrics import ObjectiveMetrics, compute_compression_metrics, compute_objective_metrics
from utils import (
    DATA_DIR,
    ENCODED_DIR,
    RESULTS_DIR,
    format_bytes,
    find_tool,
    list_ffmpeg_encoders,
    probe_video,
    save_uploaded_file,
    session_outputdir,
    session_workdir,
)


SUPPORTED_EXTENSIONS = ["mp4", "mov", "avi", "mkv"]
RESOLUTION_OPTIONS = ["Original", "1920x1080", "1280x720", "854x480", "640x360"]


def format_float(value: float | None, suffix: str = "", precision: int = 2) -> str:
    if value is None:
        return "N/A"

    return f"{value:.{precision}f}{suffix}"


def results_dataframe(rows: list[dict]) -> pd.DataFrame:
    columns = [
        "video name",
        "codec",
        "status",
        "original size",
        "encoded size",
        "compression ratio",
        "original bitrate",
        "encoded bitrate",
        "bitrate savings",
        "PSNR",
        "SSIM",
        "encoding time",
        "quality-to-bitrate",
        "error",
    ]

    if not rows:
        return pd.DataFrame(columns=columns)

    return pd.DataFrame(rows, columns=columns)


def chart_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    return df[df["status"] != "error"].copy()


def style_chart(fig):
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=24, r=24, t=54, b=24),
        legend_title_text="",
        font=dict(size=13),
    )
    return fig


st.set_page_config(
    page_title="HEVC vs VVC Compression Dashboard",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2rem;
    }
    div[data-testid="stMetric"] {
        border: 1px solid #e4e7ec;
        border-radius: 8px;
        padding: 14px 16px;
        min-height: 104px;
    }
    div[data-testid="stMetricLabel"] p {
        color: #667085;
    }
    .caption {
        color: #667085;
        margin-top: -0.35rem;
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

if "results" not in st.session_state:
    st.session_state["results"] = []

if "downloads" not in st.session_state:
    st.session_state["downloads"] = []

workdir = session_workdir(st.session_state["session_id"])
upload_dir = workdir / "uploads"
output_dir = session_outputdir(st.session_state["session_id"])
DATA_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
ENCODED_DIR.mkdir(parents=True, exist_ok=True)

ffmpeg_path = find_tool("ffmpeg")
ffprobe_path = find_tool("ffprobe")

st.title("HEVC/H.265 vs VVC/H.266 Compression Dashboard")
st.markdown(
    "<p class='caption'>Upload videos, encode them with HEVC and VVC, measure compression efficiency, and inspect objective quality metrics.</p>",
    unsafe_allow_html=True,
)

if not ffmpeg_path or not ffprobe_path:
    st.error("FFmpeg and FFprobe are required. Install FFmpeg and make sure both executables are available.")
    st.stop()

try:
    encoders = list_ffmpeg_encoders(ffmpeg_path)
except RuntimeError as exc:
    st.error(str(exc))
    st.stop()

hevc_available = "libx265" in encoders
vvc_available = "libvvenc" in encoders
codec_availability = {
    "HEVC": hevc_available,
    "VVC": vvc_available,
}

with st.sidebar:
    st.header("Environment")
    st.success("FFmpeg detected")
    st.caption(ffmpeg_path)
    st.write(f"HEVC `{required_encoder('HEVC')}`: {'available' if hevc_available else 'missing'}")
    st.write(f"VVC `{required_encoder('VVC')}`: {'available' if vvc_available else 'missing'}")
    st.caption(f"Uploads: {upload_dir.relative_to(DATA_DIR.parent)}")
    st.caption(f"Outputs: {output_dir.relative_to(RESULTS_DIR.parent)}")

    st.header("Encoding Settings")
    default_codecs = ["HEVC"]
    if vvc_available:
        default_codecs.append("VVC")

    selected_codecs = st.multiselect(
        "Codecs",
        ["HEVC", "VVC"],
        default=default_codecs,
    )
    crf_qp = st.slider("CRF / QP", min_value=18, max_value=45, value=32)
    preset = st.selectbox(
        "Preset",
        ["medium", "slow", "slower", "fast", "faster"],
        index=0,
    )
    output_resolution = st.selectbox("Output resolution", RESOLUTION_OPTIONS)
    use_target_bitrate = st.checkbox("Use target bitrate instead of CRF/QP")
    target_bitrate = None
    if use_target_bitrate:
        target_bitrate = st.number_input(
            "Target bitrate (kbps)",
            min_value=100,
            max_value=100000,
            value=2000,
            step=100,
        )

uploaded_files = st.file_uploader(
    "Upload videos",
    type=SUPPORTED_EXTENSIONS,
    accept_multiple_files=True,
)

if not uploaded_files:
    st.info("Upload one or more videos to begin.")
    st.stop()

saved_videos = []
metadata_rows = []

for uploaded in uploaded_files:
    try:
        saved_path = save_uploaded_file(uploaded, upload_dir)
        metadata = probe_video(ffprobe_path, saved_path, filename=uploaded.name)
        saved_videos.append((saved_path, metadata))
        metadata_rows.append(
            {
                "filename": metadata.filename,
                "resolution": metadata.resolution,
                "duration (s)": metadata.duration,
                "frame rate": metadata.frame_rate,
                "original file size": format_bytes(metadata.file_size_bytes),
                "original bitrate (kbps)": metadata.bitrate_kbps,
            }
        )
    except Exception as exc:
        st.error(f"Could not read {uploaded.name}: {exc}")

st.subheader("A. Upload Section")

preview_col, metadata_col = st.columns([1, 2], vertical_alignment="top")

with preview_col:
    st.markdown("#### Original Preview")
    first_video = saved_videos[0][0] if saved_videos else None
    if first_video:
        st.video(str(first_video))
    st.caption("Preview uses the first uploaded video.")

with metadata_col:
    st.markdown("#### Metadata")
    metadata_df = pd.DataFrame(metadata_rows)
    st.dataframe(
        metadata_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "duration (s)": st.column_config.NumberColumn(format="%.2f"),
            "frame rate": st.column_config.NumberColumn(format="%.3f"),
            "original bitrate (kbps)": st.column_config.NumberColumn(format="%.2f"),
        },
    )

st.subheader("B. Encoding Settings")

settings_cols = st.columns(5)
settings_cols[0].metric("Selected codecs", ", ".join(selected_codecs) or "None")
settings_cols[1].metric("CRF / QP", crf_qp)
settings_cols[2].metric("Preset", preset)
settings_cols[3].metric("Resolution", output_resolution)
settings_cols[4].metric("Target bitrate", f"{target_bitrate} kbps" if target_bitrate else "Off")

can_encode = bool(saved_videos and selected_codecs)

current_run_signature = {
    "files": tuple((metadata.filename, metadata.file_size_bytes) for _, metadata in saved_videos),
    "codecs": tuple(selected_codecs),
    "crf_qp": crf_qp,
    "preset": preset,
    "output_resolution": output_resolution,
    "target_bitrate": target_bitrate,
}

if "VVC" in selected_codecs and not vvc_available:
    st.warning(
        "VVC is selected, but this FFmpeg build does not include `libvvenc`. "
        "VVC rows will be reported as unavailable."
    )

start_encoding = st.button(
    "Start encoding",
    type="primary",
    disabled=not can_encode,
)

if st.session_state.get("run_signature") != current_run_signature and not start_encoding:
    st.session_state["results"] = []
    st.session_state["downloads"] = []

if start_encoding:
    st.session_state["results"] = []
    st.session_state["downloads"] = []
    st.session_state["run_signature"] = current_run_signature

    total_jobs = len(saved_videos) * len(selected_codecs)
    completed_jobs = 0
    progress = st.progress(0, text="Preparing encoding jobs")

    for input_path, original_metadata in saved_videos:
        for codec in selected_codecs:
            if not codec_availability.get(codec, False):
                st.session_state["results"].append(
                    {
                        "video name": original_metadata.filename,
                        "codec": codec,
                        "status": "error",
                        "original size": original_metadata.file_size_mb,
                        "encoded size": None,
                        "compression ratio": None,
                        "original bitrate": original_metadata.bitrate_kbps,
                        "encoded bitrate": None,
                        "bitrate savings": None,
                        "PSNR": None,
                        "SSIM": None,
                        "encoding time": None,
                        "quality-to-bitrate": None,
                        "error": f"Missing FFmpeg encoder {required_encoder(codec)}",
                    }
                )
                completed_jobs += 1
                progress.progress(
                    completed_jobs / max(total_jobs, 1),
                    text=f"Skipped {completed_jobs}/{total_jobs} jobs",
                )
                continue

            output_name = f"{Path(input_path).stem}_{codec.lower()}.mp4"
            output_path = output_dir / output_name

            try:
                progress.progress(
                    completed_jobs / max(total_jobs, 1),
                    text=f"Encoding {original_metadata.filename} with {codec}",
                )
                encoded = encode_video(
                    ffmpeg_path=ffmpeg_path,
                    input_path=input_path,
                    output_path=output_path,
                    codec=codec,
                    crf_qp=crf_qp,
                    preset=preset,
                    resolution=output_resolution,
                    target_bitrate_kbps=target_bitrate,
                )

                metric_error = ""
                quality = None

                try:
                    quality = compute_objective_metrics(
                        ffmpeg_path=ffmpeg_path,
                        original=input_path,
                        encoded=output_path,
                        original_metadata=original_metadata,
                    )
                except Exception as exc:
                    metric_error = f"Metric calculation failed: {exc}"

                if quality is None:
                    quality = ObjectiveMetrics(psnr=None, ssim=None)

                compression = compute_compression_metrics(
                    ffprobe_path=ffprobe_path,
                    original_metadata=original_metadata,
                    encoded_path=output_path,
                    quality=quality,
                )

                st.session_state["downloads"].append(
                    {
                        "video name": original_metadata.filename,
                        "codec": codec,
                        "path": str(output_path),
                        "filename": output_path.name,
                    }
                )

                st.session_state["results"].append(
                    {
                        "video name": original_metadata.filename,
                        "codec": codec,
                        "status": "ok" if not metric_error else "metrics warning",
                        "original size": original_metadata.file_size_mb,
                        "encoded size": compression.encoded_size_bytes / 1024 / 1024,
                        "compression ratio": compression.compression_ratio,
                        "original bitrate": original_metadata.bitrate_kbps,
                        "encoded bitrate": compression.encoded_bitrate_bps / 1000,
                        "bitrate savings": compression.bitrate_savings_percent,
                        "PSNR": quality.psnr,
                        "SSIM": quality.ssim,
                        "encoding time": encoded.encoding_time_seconds,
                        "quality-to-bitrate": compression.psnr_per_mbps,
                        "error": metric_error,
                    }
                )

            except Exception as exc:
                st.session_state["results"].append(
                    {
                        "video name": original_metadata.filename,
                        "codec": codec,
                        "status": "error",
                        "original size": original_metadata.file_size_mb,
                        "encoded size": None,
                        "compression ratio": None,
                        "original bitrate": original_metadata.bitrate_kbps,
                        "encoded bitrate": None,
                        "bitrate savings": None,
                        "PSNR": None,
                        "SSIM": None,
                        "encoding time": None,
                        "quality-to-bitrate": None,
                        "error": str(exc),
                    }
                )

            completed_jobs += 1
            progress.progress(
                completed_jobs / max(total_jobs, 1),
                text=f"Completed {completed_jobs}/{total_jobs} jobs",
            )

    progress.progress(1.0, text="Encoding complete")

results_df = results_dataframe(st.session_state["results"])

st.subheader("C. Results Table")
st.dataframe(
    results_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "compression ratio": st.column_config.NumberColumn(format="%.2fx"),
        "original size": st.column_config.NumberColumn("original size (MB)", format="%.2f"),
        "encoded size": st.column_config.NumberColumn("encoded size (MB)", format="%.2f"),
        "original bitrate": st.column_config.NumberColumn("original bitrate (kbps)", format="%.2f"),
        "encoded bitrate": st.column_config.NumberColumn("encoded bitrate (kbps)", format="%.2f"),
        "bitrate savings": st.column_config.NumberColumn("bitrate savings (%)", format="%.2f"),
        "PSNR": st.column_config.NumberColumn(format="%.2f dB"),
        "SSIM": st.column_config.NumberColumn(format="%.4f"),
        "encoding time": st.column_config.NumberColumn("encoding time (s)", format="%.2f"),
        "quality-to-bitrate": st.column_config.NumberColumn("PSNR / Mbps", format="%.2f"),
    },
)

plot_df = chart_dataframe(results_df)

st.subheader("D. Visualizations")

if plot_df.empty:
    st.info("Run encoding to generate charts.")
else:
    chart_cols = st.columns(2)

    with chart_cols[0]:
        fig_size = px.bar(
            plot_df,
            x="video name",
            y="encoded size",
            color="codec",
            barmode="group",
            title="Encoded File Size by Codec",
        )
        st.plotly_chart(style_chart(fig_size), use_container_width=True)

    with chart_cols[1]:
        fig_ratio = px.bar(
            plot_df,
            x="video name",
            y="compression ratio",
            color="codec",
            barmode="group",
            title="Compression Ratio",
        )
        st.plotly_chart(style_chart(fig_ratio), use_container_width=True)

    chart_cols = st.columns(2)

    with chart_cols[0]:
        fig_savings = px.bar(
            plot_df,
            x="video name",
            y="bitrate savings",
            color="codec",
            barmode="group",
            title="Bitrate Savings (%)",
        )
        st.plotly_chart(style_chart(fig_savings), use_container_width=True)

    with chart_cols[1]:
        summary = (
            plot_df.groupby("codec", as_index=False)
            .agg(
                {
                    "compression ratio": "mean",
                    "bitrate savings": "mean",
                    "PSNR": "mean",
                    "SSIM": "mean",
                    "encoding time": "mean",
                }
            )
        )
        fig_summary = px.bar(
            summary.melt(id_vars="codec", var_name="metric", value_name="value"),
            x="metric",
            y="value",
            color="codec",
            barmode="group",
            title="Codec Comparison Summary",
        )
        st.plotly_chart(style_chart(fig_summary), use_container_width=True)

    scatter_cols = st.columns(2)

    with scatter_cols[0]:
        fig_psnr = px.scatter(
            plot_df,
            x="encoded bitrate",
            y="PSNR",
            color="codec",
            symbol="video name",
            size="compression ratio",
            hover_data=["video name", "encoded size", "bitrate savings"],
            title="Bitrate vs PSNR",
        )
        st.plotly_chart(style_chart(fig_psnr), use_container_width=True)

    with scatter_cols[1]:
        fig_ssim = px.scatter(
            plot_df,
            x="encoded bitrate",
            y="SSIM",
            color="codec",
            symbol="video name",
            size="compression ratio",
            hover_data=["video name", "encoded size", "bitrate savings"],
            title="Bitrate vs SSIM",
        )
        st.plotly_chart(style_chart(fig_ssim), use_container_width=True)

st.subheader("E. Downloads")

csv_path = RESULTS_DIR / "hevc_vvc_results.csv"
results_df.to_csv(csv_path, index=False)

with csv_path.open("rb") as csv_file:
    st.download_button(
        "Download results CSV",
        data=csv_file,
        file_name="hevc_vvc_results.csv",
        mime="text/csv",
        use_container_width=True,
    )

download_rows = st.session_state["downloads"]

if not download_rows:
    st.info("Encoded videos will appear here after a successful run.")
else:
    for item in download_rows:
        path = Path(item["path"])
        if not path.exists():
            continue

        with path.open("rb") as video_file:
            st.download_button(
                f"Download {item['codec']} - {item['video name']}",
                data=video_file,
                file_name=item["filename"],
                mime="video/mp4",
                use_container_width=True,
            )
