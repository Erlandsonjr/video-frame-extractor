# Frame Extractor v2.0.0

A desktop application for extracting individual frames from video files. Select a video, configure a time range and capture interval, preview thumbnails, and export chosen frames in multiple formats.

Built with **PySide6** and **OpenCV**.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-6.5+-green?logo=qt&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Features

- **Drag-and-drop** or browse to load a video file
- **Video metadata display** — resolution, FPS, duration, and codec shown after loading
- **Time range selection** — configurable start/end times with an interval spinner
- **Background processing** — frame extraction runs on a separate thread; UI stays responsive
- **Cancel support** — stop extraction at any time
- **Thumbnail gallery** — zoomable, multi-select grid with aspect-ratio-correct thumbnails
- **Full-resolution preview** — double-click any frame to open a zoomable, pannable viewer with prev/next navigation
- **Context menu** — right-click for Preview, Select All, Clear Selection, Remove Selected
- **Export dialog** — choose format (PNG, JPEG, WebP, BMP), quality, resolution scaling, and custom filename patterns
- **Batch processing** — queue multiple videos and extract frames from all of them
- **Dark & light themes** — toggle with `Ctrl+T`; Catppuccin-inspired stylesheets
- **Persistent settings** — theme, last directory, window geometry, default interval, and export preferences are remembered across sessions
- **Keyboard shortcuts** — full set for power users

## Supported Formats

**Video input:** `.mp4` `.avi` `.mkv` `.mov` `.webm` `.flv` `.wmv` `.m4v` `.mpg` `.mpeg` `.3gp` `.ts`

**Image export:** PNG, JPEG (quality 1–100), WebP (quality 1–100), BMP

---

## Installation

### Prerequisites

- Python 3.10 or newer

### Setup

```bash
git clone https://github.com/Erlandsonjr/video-frame-extractor
cd video-frame-extractor
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+O` | Open video |
| `Ctrl+B` | Batch processing |
| `Ctrl+S` | Export selected frames |
| `Ctrl+A` | Select all frames |
| `Ctrl+Shift+A` | Clear selection |
| `Delete` | Remove selected frames from gallery |
| `Escape` | Cancel processing |
| `Ctrl+T` | Toggle dark/light theme |
| `Ctrl+=` / `Ctrl+-` | Zoom thumbnails in/out |
| `Ctrl+Q` | Quit |

**In preview dialog:**

| Shortcut | Action |
|---|---|
| `←` / `→` | Previous / next frame |
| `+` / `-` | Zoom in / out |
| `F` | Fit to window |
| `Scroll wheel` | Zoom |
| `Escape` | Close preview |

---

## Project Structure

```
frame_extractor/
├── main.py                  # Entry point
├── app.py                   # QApplication subclass, theme management
├── main_window.py           # Main window with menu bar, status bar, all UI
├── requirements.txt
│
├── widgets/                 # Custom UI components
│   ├── drop_label.py        # Drag-and-drop with file validation
│   ├── video_info_panel.py  # Video metadata bar
│   ├── gallery_widget.py    # Thumbnail grid with context menu
│   └── preview_dialog.py    # Full-resolution frame viewer
│
├── processing/              # Background workers
│   ├── video_processor.py   # Frame extraction thread
│   └── export_manager.py    # Threaded export with format options
│
├── dialogs/                 # Modal dialogs
│   ├── export_dialog.py     # Export format, quality, naming options
│   ├── settings_dialog.py   # App preferences
│   └── batch_dialog.py      # Multi-video queue
│
├── utils/                   # Shared utilities
│   ├── constants.py         # App-wide configuration values
│   └── settings.py          # QSettings wrapper for persistence
│
└── resources/
    └── styles/
        ├── dark.qss         # Dark theme stylesheet
        └── light.qss        # Light theme stylesheet
```

---

## Export Filename Patterns

When exporting, you can customize the filename using placeholders:

| Placeholder | Description | Example |
|---|---|---|
| `{video}` | Video filename (no extension) | `my_video` |
| `{time}` | Timestamp (`HH-MM-SS_s`) | `00-05-30_0` |
| `{index}` | Sequential number (zero-padded) | `0001` |

**Default pattern:** `frame_{time}_{index}` → `frame_00-05-30_0_0001.png`

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
