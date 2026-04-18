"""
YouTube to MP3 Converter - Flask Backend
Run with: python app.py
"""

import os
import re
import time
import threading
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, after_this_request
import yt_dlp

app = Flask(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
DOWNLOADS_DIR = Path("downloads")
DOWNLOADS_DIR.mkdir(exist_ok=True)

# Auto-delete files older than this many seconds after a download
FILE_TTL_SECONDS = 120


# ── Helpers ───────────────────────────────────────────────────────────────────

def sanitize_filename(name: str) -> str:
    """Remove characters that are unsafe in filenames."""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.strip(". ")
    return name[:200] or "audio"


def cleanup_old_files():
    """Delete downloads older than FILE_TTL_SECONDS (runs in background)."""
    now = time.time()
    for f in DOWNLOADS_DIR.glob("*.mp3"):
        if now - f.stat().st_mtime > FILE_TTL_SECONDS:
            try:
                f.unlink()
            except OSError:
                pass


def delete_file_later(path: Path, delay: int = 60):
    """Delete *path* in a background thread after *delay* seconds."""
    def _delete():
        time.sleep(delay)
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
    threading.Thread(target=_delete, daemon=True).start()


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Render the main page."""
    return render_template("index.html")


@app.route("/info", methods=["POST"])
def get_info():
    """
    Return basic metadata (title, thumbnail, duration) for a YouTube URL
    without downloading anything — used to preview before the user clicks Download.
    """
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()

    if not url:
        return jsonify({"error": "No URL provided."}), 400

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        return jsonify({"error": f"Could not fetch video info: {exc}"}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    return jsonify({
        "title":     info.get("title", "Unknown title"),
        "thumbnail": info.get("thumbnail", ""),
        "duration":  info.get("duration", 0),
        "uploader":  info.get("uploader", ""),
    })


@app.route("/download", methods=["POST"])
def download():
    """
    Download the YouTube audio, convert it to MP3 via ffmpeg,
    and stream the file back to the browser.
    """
    cleanup_old_files()   # tidy up before each new download

    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()

    if not url:
        return jsonify({"error": "No URL provided."}), 400

    # ── Step 1: resolve title so we can name the file ─────────────────────────
    ydl_meta_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    try:
        with yt_dlp.YoutubeDL(ydl_meta_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            raw_title = info.get("title", "audio")
    except Exception as exc:
        return jsonify({"error": f"Invalid URL or video unavailable: {exc}"}), 400

    safe_title = sanitize_filename(raw_title)
    output_path = DOWNLOADS_DIR / f"{safe_title}.mp3"

    # ── Step 2: download + convert ────────────────────────────────────────────
    ydl_dl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(DOWNLOADS_DIR / f"{safe_title}.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",   # 192 kbps
        }],
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_dl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as exc:
        return jsonify({"error": f"Download failed: {exc}"}), 500
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    if not output_path.exists():
        return jsonify({"error": "MP3 file was not created. Is ffmpeg installed?"}), 500

    # Schedule file deletion 60 s after response is sent
    delete_file_later(output_path, delay=60)

    # ── Step 3: send the file ─────────────────────────────────────────────────
    return send_file(
        str(output_path),
        as_attachment=True,
        download_name=f"{safe_title}.mp3",
        mimetype="audio/mpeg",
    )


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🎵  YouTube → MP3 Converter running at http://127.0.0.1:5000\n")
    app.run(debug=True, port=5000)
