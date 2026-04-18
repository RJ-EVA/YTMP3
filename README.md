# 🎵 YouTube → MP3 Converter

A clean, local web app that converts any YouTube video to a 192 kbps MP3 file.

```
yt2mp3/
├── app.py               ← Flask backend
├── requirements.txt     ← Python deps
├── templates/
│   └── index.html       ← Frontend (dark UI, all-in-one)
└── downloads/           ← Temp MP3 storage (auto-created)
```

---

## Quick Start

### 1 — Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2 — Install ffmpeg

| Platform | Command |
|----------|---------|
| **macOS** | `brew install ffmpeg` |
| **Ubuntu / Debian** | `sudo apt install ffmpeg` |
| **Windows** | Download from https://ffmpeg.org/download.html and add the `bin/` folder to your PATH |

Verify: `ffmpeg -version`

### 3 — Run the app

```bash
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

---

## How it works

1. **Preview** — paste a YouTube URL and click *Preview* to fetch title, thumbnail, and duration without downloading anything.  
2. **Download** — click *Download MP3*. Flask calls `yt-dlp` to pull the best available audio stream, then `ffmpeg` re-encodes it to MP3 @ 192 kbps.  
3. **File cleanup** — the server deletes the MP3 60 seconds after the request completes, and also purges any files older than 2 minutes at the start of each request.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `FileNotFoundError: ffmpeg` | Install ffmpeg and make sure it's on your PATH |
| `DownloadError: Video unavailable` | The video may be private, age-restricted, or region-blocked |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Port already in use | Change `port=5000` in `app.py` to another number |

---

## Notes

- This app is intended for **personal, local use only**.  
- Respect YouTube's Terms of Service and copyright laws.  
- `yt-dlp` may need occasional updates: `pip install -U yt-dlp`
