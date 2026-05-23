import streamlit as st
import pandas as pd
import plotly.express as px
import subprocess
import time
import sys
import os

# =====================
# Import quality metrics
# =====================

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "src"
        )
    )
)

from quality_metrics import evaluate_video

# =====================
# Page Config
# =====================

st.set_page_config(
    page_title="VVC vs HEVC Compression Comparison",
    layout="wide"
)

st.title("VVC vs HEVC Compression Comparison")

# =====================
# Upload
# =====================

uploaded = st.file_uploader(
    "Upload Video",
    type=["mp4"]
)

if uploaded:

    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/hevc", exist_ok=True)
    os.makedirs("data/vvc", exist_ok=True)
    os.makedirs("results", exist_ok=True)

    input_path = "data/raw/input.mp4"

    with open(input_path, "wb") as f:
        f.write(uploaded.read())

    st.success("Video uploaded successfully")

    st.video(input_path)

    # =====================
    # Settings
    # =====================

    st.subheader("Encoding Settings")

    qp = st.slider(
        "QP Value",
        min_value=20,
        max_value=40,
        value=32
    )

    # =====================
    # Encode
    # =====================

    if st.button("Encode Video"):

        hevc_path = "data/hevc/output_hevc.mp4"
        vvc_path = "data/vvc/output_vvc.mp4"

        with st.spinner("Encoding HEVC and VVC..."):

            # HEVC

            start = time.time()

            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    input_path,
                    "-c:v",
                    "libx265",
                    "-crf",
                    str(qp),
                    hevc_path
                ]
            )

            hevc_time = time.time() - start

            # VVC

            start = time.time()

            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    input_path,
                    "-c:v",
                    "libvvenc",
                    "-qp",
                    str(qp),
                    vvc_path
                ]
            )

            vvc_time = time.time() - start

        st.success("Encoding completed!")

        # =====================
        # Metrics
        # =====================

        result = evaluate_video(
            input_path,
            hevc_path,
            vvc_path
        )

        # =====================
        # KPI Dashboard
        # =====================

        st.subheader("Quality Metrics")

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "HEVC PSNR",
                f"{result['hevc_psnr']:.2f} dB"
            )

            st.metric(
                "HEVC SSIM",
                f"{result['hevc_ssim']:.4f}"
            )

            st.metric(
                "HEVC Compression Ratio",
                f"{result['hevc_cr']:.2f}x"
            )

            st.metric(
                "HEVC Encoding Time",
                f"{hevc_time:.2f}s"
            )

        with col2:

            st.metric(
                "VVC PSNR",
                f"{result['vvc_psnr']:.2f} dB"
            )

            st.metric(
                "VVC SSIM",
                f"{result['vvc_ssim']:.4f}"
            )

            st.metric(
                "VVC Compression Ratio",
                f"{result['vvc_cr']:.2f}x"
            )

            st.metric(
                "VVC Encoding Time",
                f"{vvc_time:.2f}s"
            )

        # =====================
        # Extra Metrics
        # =====================

        colA, colB, colC = st.columns(3)

        with colA:

            st.metric(
                "Bitrate Saving",
                f"{result['bitrate_saving']:.2f}%"
            )

        with colB:

            st.metric(
                "HEVC Size",
                f"{os.path.getsize(hevc_path)/1024/1024:.2f} MB"
            )

        with colC:

            st.metric(
                "VVC Size",
                f"{os.path.getsize(vvc_path)/1024/1024:.2f} MB"
            )

        # =====================
        # Data Table
        # =====================

        df = pd.DataFrame(
            {
                "Codec": ["HEVC", "VVC"],
                "PSNR": [
                    result["hevc_psnr"],
                    result["vvc_psnr"]
                ],
                "SSIM": [
                    result["hevc_ssim"],
                    result["vvc_ssim"]
                ],
                "Compression Ratio": [
                    result["hevc_cr"],
                    result["vvc_cr"]
                ],
                "Encoding Time (s)": [
                    hevc_time,
                    vvc_time
                ],
                "File Size (MB)": [
                    os.path.getsize(hevc_path)/1024/1024,
                    os.path.getsize(vvc_path)/1024/1024
                ]
            }
        )

        st.subheader("Comparison Table")

        st.dataframe(
            df,
            use_container_width=True
        )

        # =====================
        # Charts
        # =====================

        st.subheader("Performance Dashboard")

        left, right = st.columns(2)

        with left:

            fig_psnr = px.bar(
                df,
                x="Codec",
                y="PSNR",
                color="Codec",
                text="PSNR",
                title="PSNR Comparison"
            )

            fig_psnr.update_traces(
                texttemplate="%{text:.2f}",
                textposition="outside"
            )

            st.plotly_chart(
                fig_psnr,
                use_container_width=True
            )

        with right:

            fig_cr = px.bar(
                df,
                x="Codec",
                y="Compression Ratio",
                color="Codec",
                text="Compression Ratio",
                title="Compression Ratio Comparison"
            )

            fig_cr.update_traces(
                texttemplate="%{text:.2f}",
                textposition="outside"
            )

            st.plotly_chart(
                fig_cr,
                use_container_width=True
            )

        fig_size = px.bar(
            df,
            x="Codec",
            y="File Size (MB)",
            color="Codec",
            text="File Size (MB)",
            title="Compressed File Size Comparison"
        )

        fig_size.update_traces(
            texttemplate="%{text:.2f}",
            textposition="outside"
        )

        st.plotly_chart(
            fig_size,
            use_container_width=True
        )

        # =====================
        # Conclusion
        # =====================

        st.subheader("Conclusion")

        if result["bitrate_saving"] > 0:

            st.success(
                f"""
VVC achieved {result['bitrate_saving']:.2f}% bitrate savings compared with HEVC.

Compression Ratio improved from {result['hevc_cr']:.2f}x to {result['vvc_cr']:.2f}x.

PSNR changed from {result['hevc_psnr']:.2f} dB to {result['vvc_psnr']:.2f} dB.
"""
            )

        else:

            st.warning(
                "VVC did not provide bitrate savings for this configuration."
            )

        # =====================
        # Export CSV
        # =====================

        csv_path = "results/results.csv"

        df.to_csv(
            csv_path,
            index=False
        )

        with open(csv_path, "rb") as f:

            st.download_button(
                "Download Results CSV",
                data=f,
                file_name="results.csv",
                mime="text/csv"
            )

        # =====================
        # Encoded Videos
        # =====================

        st.subheader("Encoded Videos")

        video_col1, video_col2 = st.columns(2)

        with video_col1:

            st.write("HEVC Output")

            st.video(hevc_path)

            with open(hevc_path, "rb") as f:

                st.download_button(
                    "Download HEVC Video",
                    data=f,
                    file_name="hevc_output.mp4"
                )

        with video_col2:

            st.write("VVC Output")

            st.warning(
                "Most browsers do not support VVC playback. Download and open with VLC."
            )

            with open(vvc_path, "rb") as f:

                st.download_button(
                    "Download VVC Video",
                    data=f,
                    file_name="vvc_output.mp4"
                )