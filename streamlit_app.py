import streamlit as st
import yt_dlp
import os
import re
from pathlib import Path

# ── Config ─────────────────────────────
DOWNLOADS_DIR = Path("downloads")
DOWNLOADS_DIR.mkdir(exist_ok=True)

# ── Helpers ────────────────────────────
def sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.strip(". ")
    return name[:200] or "audio"

def get_video_info(url):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

def download_mp3(url, title):
    safe_title = sanitize_filename(title)
    output_path = DOWNLOADS_DIR / f"{safe_title}.mp3"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(DOWNLOADS_DIR / f"{safe_title}.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return output_path


# ── UI ────────────────────────────────
st.set_page_config(page_title="YT → MP3", layout="centered")

st.title("🎵 YouTube → MP3 Converter")

url = st.text_input("Paste YouTube URL")

if st.button("Preview"):
    if not url:
        st.error("Paste a URL first")
    else:
        try:
            info = get_video_info(url)

            st.image(info.get("thumbnail"))
            st.subheader(info.get("title"))
            st.caption(f"By {info.get('uploader')}")

            st.session_state["title"] = info.get("title")
            st.session_state["url"] = url

        except Exception as e:
            st.error(f"Error: {e}")


if "url" in st.session_state:
    if st.button("Download MP3"):
        with st.spinner("Downloading & converting..."):
            try:
                path = download_mp3(
                    st.session_state["url"],
                    st.session_state["title"]
                )

                with open(path, "rb") as f:
                    st.download_button(
                        label="Download file",
                        data=f,
                        file_name=path.name,
                        mime="audio/mpeg"
                    )

                st.success("Done. File ready.")

            except Exception as e:
                st.error(f"Download failed: {e}")