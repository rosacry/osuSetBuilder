"""
osu! Set Builder - A tool for creating and managing osu! beatmap sets.

This application allows users to:
- Combine multiple .osu difficulty files into a single beatmap set
- Edit metadata (title, artist, creator, source, tags) across all difficulties
- Set a common background image for the entire set
- Preview and set the audio preview point
- Export as .osz files or open directly in osu!

Author: osuBuilder
License: MIT
Version: 1.0.0
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# ---------------------------------------------------------------------------
# Application Constants
# ---------------------------------------------------------------------------
APP_NAME = "osu! Set Builder"
APP_VERSION = "1.0.0"
WINDOW_MIN_WIDTH = 900
WINDOW_MIN_HEIGHT = 720

# ---------------------------------------------------------------------------
# Regex Patterns for .osu File Parsing
# ---------------------------------------------------------------------------
META_KEYS = {
    "Title": "title",
    "Artist": "artist",
    "Creator": "creator",
    "Source": "source",
    "Tags": "tags",
}
META_RE = re.compile(r"^(?P<key>\w+):(?P<value>.*)$")
DIFF_RE = re.compile(r"^Version:(?P<value>.*)$")
AUDIO_RE = re.compile(r"^AudioFilename:(?P<value>.*)$")
BG_RE = re.compile(r"^0,0,\"(?P<bg>[^\"]+)\".*$")

# Standard osu! filename format: "Artist - Title (Creator) [Difficulty].osu"
FILENAME_FMT_RE = re.compile(r".+ - .+ \(.+\) \[.+]\.osu$", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Modern Dark Theme Stylesheet (osu! inspired pink accent)
# ---------------------------------------------------------------------------
DARK_THEME = """
QWidget {
    background-color: #1a1a2e;
    color: #eaeaea;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 10pt;
}

QPushButton {
    background-color: #ff66ab;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #ff85be;
}

QPushButton:pressed {
    background-color: #e55a9b;
}

QPushButton:disabled {
    background-color: #555555;
    color: #888888;
}

QPushButton#primaryButton {
    background-color: #ff66ab;
    font-size: 11pt;
    padding: 10px 20px;
}

QPushButton#secondaryButton {
    background-color: #16213e;
    border: 2px solid #ff66ab;
    color: #ff66ab;
}

QPushButton#secondaryButton:hover {
    background-color: #1f3460;
}

QPushButton#dangerButton {
    background-color: #e74c3c;
}

QPushButton#dangerButton:hover {
    background-color: #ff6b5b;
}

QLineEdit {
    background-color: #16213e;
    border: 2px solid #0f3460;
    border-radius: 6px;
    padding: 8px 12px;
    color: #eaeaea;
    selection-background-color: #ff66ab;
}

QLineEdit:focus {
    border: 2px solid #ff66ab;
}

QTableWidget {
    background-color: #16213e;
    alternate-background-color: #1a2744;
    border: 2px solid #0f3460;
    border-radius: 8px;
    gridline-color: #0f3460;
    selection-background-color: #ff66ab;
}

QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #0f3460;
}

QTableWidget::item:selected {
    background-color: #ff66ab;
    color: white;
}

QHeaderView::section {
    background-color: #0f3460;
    color: #ff66ab;
    padding: 10px;
    border: none;
    font-weight: bold;
}

QLabel#titleLabel {
    font-size: 24pt;
    font-weight: bold;
    color: #ff66ab;
}

QLabel#subtitleLabel {
    font-size: 10pt;
    color: #888888;
}

QLabel#sectionLabel {
    font-size: 11pt;
    font-weight: bold;
    color: #ff66ab;
    padding: 4px 0px;
}

QGroupBox {
    font-weight: bold;
    border: 2px solid #0f3460;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 8px;
    color: #ff66ab;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
}

QSlider::groove:horizontal {
    background: #0f3460;
    height: 8px;
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background: #ff66ab;
    width: 18px;
    height: 18px;
    margin: -5px 0;
    border-radius: 9px;
}

QSlider::handle:horizontal:hover {
    background: #ff85be;
}

QSlider::sub-page:horizontal {
    background: #ff66ab;
    border-radius: 4px;
}

QSpinBox, QComboBox {
    background-color: #16213e;
    border: 2px solid #0f3460;
    border-radius: 6px;
    padding: 6px;
    color: #eaeaea;
}

QSpinBox:focus, QComboBox:focus {
    border: 2px solid #ff66ab;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #ff66ab;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #16213e;
    border: 2px solid #0f3460;
    selection-background-color: #ff66ab;
}

QScrollBar:vertical {
    background: #16213e;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background: #0f3460;
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #ff66ab;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QToolTip {
    background-color: #0f3460;
    color: #eaeaea;
    border: 1px solid #ff66ab;
    border-radius: 4px;
    padding: 6px;
}

QFrame#separator {
    background-color: #0f3460;
}

QFrame#bgPreviewFrame {
    background-color: #16213e;
    border: 2px solid #0f3460;
    border-radius: 8px;
}
"""


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------


def resource_path(rel_path: str) -> str:
    """
    Return an absolute path to a resource file.

    Works both when running as a script and as a PyInstaller bundle.

    Args:
        rel_path: Relative path to the resource file.

    Returns:
        Absolute path to the resource.
    """
    if getattr(sys, "frozen", False):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        return os.path.join(sys._MEIPASS, rel_path)
    return os.path.join(Path(__file__).parent, rel_path)


def sanitize_filename(name: str) -> str:
    """
    Remove or replace characters that are invalid in filenames.

    Args:
        name: The filename to sanitize.

    Returns:
        A sanitized filename safe for all operating systems.
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, "_")
    return name.strip(" .")


def format_time(ms: int) -> str:
    """
    Format milliseconds as MM:SS.

    Args:
        ms: Time in milliseconds.

    Returns:
        Formatted time string.
    """
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


# ---------------------------------------------------------------------------
# .osu File Parsing and Writing
# ---------------------------------------------------------------------------


def read_osu(path: Path) -> dict:
    """
    Parse a .osu beatmap file and extract metadata.

    Args:
        path: Path to the .osu file.

    Returns:
        Dictionary containing parsed data including path, lines, meta,
        difficulty name, audio filename, and background filename.
    """
    try:
        lines = path.read_text("utf-8", errors="ignore").splitlines()
    except Exception:
        lines = path.read_text("latin-1", errors="ignore").splitlines()

    meta: Dict[str, str] = {}
    diff = ""
    audio = ""
    bg = ""
    in_meta = in_events = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("[Metadata]"):
            in_meta, in_events = True, False
            continue
        if stripped.startswith("[Events]"):
            in_meta, in_events = False, True
            continue
        if stripped.startswith("[") and (in_meta or in_events):
            in_meta = in_events = False

        if in_meta:
            m = META_RE.match(line)
            if m and m.group("key") in META_KEYS:
                meta[m.group("key")] = m.group("value").strip()
            elif DIFF_RE.match(line):
                diff = DIFF_RE.match(line).group("value").strip()
        elif not audio and AUDIO_RE.match(line):
            audio = AUDIO_RE.match(line).group("value").strip()
        elif in_events and not bg:
            m = BG_RE.match(line)
            if m:
                bg = m.group("bg")

    return {
        "path": path,
        "lines": lines,
        "meta": meta,
        "difficulty": diff or path.stem,
        "audio": audio,
        "bg": bg,
    }


def rewrite_osu(
    data: dict,
    out_path: Path,
    common_meta: dict,
    difficulty: str,
    audio_name: str,
    bg_name: str,
    preview_ms: Optional[int] = None,
) -> None:
    """
    Rewrite a .osu file with updated metadata and media references.

    Args:
        data: Parsed .osu data from read_osu().
        out_path: Path for the output file.
        common_meta: Dictionary with title, artist, creator, source, tags.
        difficulty: New difficulty name.
        audio_name: Filename for the audio file.
        bg_name: Filename for the background image.
        preview_ms: Preview time in milliseconds (optional).
    """
    new_lines: List[str] = []
    in_meta = in_events = in_general = False
    bg_written = False
    preview_written = False

    for line in data["lines"]:
        stripped = line.strip()

        # Section detection
        if stripped.startswith("[General]"):
            in_general, in_meta, in_events = True, False, False
            new_lines.append(line)
            continue
        if stripped.startswith("[Metadata]"):
            in_meta, in_general, in_events = True, False, False
            new_lines.append(line)
            continue
        if stripped.startswith("[Events]"):
            in_events, in_meta, in_general = True, False, False
            new_lines.append(line)
            continue
        if stripped.startswith("[") and (in_general or in_meta or in_events):
            if in_general and preview_ms is not None and not preview_written:
                new_lines.append(f"PreviewTime: {preview_ms}")
            if in_events and not bg_written and bg_name:
                new_lines.append(f'0,0,"{bg_name}",0,0')
                bg_written = True
            in_general = in_meta = in_events = False

        # [General] section
        if in_general:
            if stripped.startswith("PreviewTime:"):
                preview_written = True
                if preview_ms is not None:
                    new_lines.append(f"PreviewTime: {preview_ms}")
                else:
                    new_lines.append(line)
            elif stripped.startswith("AudioFilename:"):
                new_lines.append(f"AudioFilename: {audio_name}")
            else:
                new_lines.append(line)
            continue

        # [Metadata] section
        if in_meta:
            if stripped.startswith("Version:"):
                new_lines.append(f"Version: {difficulty}")
            elif stripped.startswith("BeatmapID:"):
                new_lines.append("BeatmapID: 0")
            elif stripped.startswith("BeatmapSetID:"):
                new_lines.append("BeatmapSetID: -1")
            else:
                m = META_RE.match(line)
                if m and m.group("key") in META_KEYS:
                    key = m.group("key")
                    new_lines.append(f"{key}: {common_meta[META_KEYS[key]]}")
                else:
                    new_lines.append(line)
            continue

        # [Events] section
        if in_events:
            if BG_RE.match(line):
                if not bg_written:
                    new_lines.append(f'0,0,"{bg_name}",0,0')
                    bg_written = True
            else:
                new_lines.append(line)
            continue

        # Everything else
        if stripped.startswith("AudioFilename:"):
            new_lines.append(f"AudioFilename: {audio_name}")
        else:
            new_lines.append(line)

    # Ensure background is written
    if not bg_written and bg_name:
        events_idx = None
        for i, line in enumerate(new_lines):
            if line.strip().startswith("[Events]"):
                events_idx = i
                break

        if events_idx is not None:
            new_lines.insert(events_idx + 1, f'0,0,"{bg_name}",0,0')
        else:
            new_lines.extend(["", "[Events]", f'0,0,"{bg_name}",0,0'])

    out_path.write_text("\n".join(new_lines), "utf-8")


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------


@dataclass
class DifficultyRow:
    """Represents a beatmap difficulty in the table."""

    data: dict
    row: int
    formatted: bool = False


# ---------------------------------------------------------------------------
# Preview Point Picker Dialog
# ---------------------------------------------------------------------------


class PreviewPickerDialog(QDialog):
    """Dialog for selecting the audio preview point."""

    def __init__(
        self, parent: QWidget, audio_path: Path, current_ms: Optional[int] = None
    ):
        super().__init__(parent)
        self.setWindowTitle("Pick Preview Point")
        self.setMinimumWidth(700)
        self.setMinimumHeight(300)

        self.selected_ms: Optional[int] = current_ms
        self._setup_ui(audio_path, current_ms)

    def _setup_ui(self, audio_path: Path, current_ms: Optional[int]) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Audio player
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.setSource(QUrl.fromLocalFile(str(audio_path)))

        self.setAttribute(Qt.WA_DeleteOnClose)
        self.finished.connect(lambda _: self.player.stop())

        # Speed selector
        speed_row = QHBoxLayout()
        speed_row.addWidget(QLabel("Playback Speed:"))
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["25%", "50%", "75%", "100%"])
        self.speed_combo.setCurrentIndex(3)
        self.speed_combo.currentIndexChanged.connect(self._on_speed_changed)
        speed_row.addWidget(self.speed_combo)
        speed_row.addStretch()
        layout.addLayout(speed_row)

        # Timeline
        self.timeline = QSlider(Qt.Horizontal)
        self.timeline.setFixedHeight(30)
        self.timeline.setRange(0, 0)
        layout.addWidget(self.timeline)

        # Time display
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)

        # Manual input
        input_row = QHBoxLayout()
        input_row.addWidget(QLabel("Jump to:"))
        self.ms_spin = QSpinBox()
        self.ms_spin.setSuffix(" ms")
        self.ms_spin.setSingleStep(100)
        self.ms_spin.setMinimumWidth(120)
        input_row.addWidget(self.ms_spin)
        self.sec_spin = QSpinBox()
        self.sec_spin.setSuffix(" s")
        self.sec_spin.setSingleStep(1)
        self.sec_spin.setMinimumWidth(100)
        input_row.addWidget(self.sec_spin)
        input_row.addStretch()
        layout.addLayout(input_row)

        # Volume
        vol_row = QHBoxLayout()
        vol_row.addWidget(QLabel("Volume:"))
        self.volume = QSlider(Qt.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(50)
        self.volume.setMaximumWidth(200)
        self.audio_output.setVolume(0.5)
        vol_row.addWidget(self.volume)
        vol_row.addStretch()
        layout.addLayout(vol_row)

        # Buttons
        btn_row = QHBoxLayout()
        self.play_btn = QPushButton("Play")
        self.play_btn.setMinimumWidth(100)
        btn_row.addWidget(self.play_btn)
        btn_row.addStretch()
        self.use_btn = QPushButton("Use This Point")
        self.use_btn.setObjectName("primaryButton")
        self.use_btn.setMinimumWidth(150)
        btn_row.addWidget(self.use_btn)
        layout.addLayout(btn_row)

        # Connect signals
        self.timeline.sliderMoved.connect(self._seek)
        self.timeline.sliderReleased.connect(lambda: self._seek(self.timeline.value()))
        self.ms_spin.valueChanged.connect(self._seek)
        self.sec_spin.valueChanged.connect(lambda s: self._seek(s * 1000))
        self.player.positionChanged.connect(self._on_position)
        self.player.durationChanged.connect(self._on_duration)
        self.play_btn.clicked.connect(self._toggle_play)
        self.volume.valueChanged.connect(
            lambda v: self.audio_output.setVolume(v / 100.0)
        )
        self.use_btn.clicked.connect(self._accept)

        if current_ms:
            self.player.setPosition(current_ms)

    def _on_speed_changed(self, idx: int) -> None:
        self.player.setPlaybackRate([0.25, 0.5, 0.75, 1.0][idx])

    def _seek(self, pos: int) -> None:
        self.player.setPosition(pos)
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.play()

    def _on_position(self, pos: int) -> None:
        if not self.timeline.isSliderDown():
            self.timeline.blockSignals(True)
            self.timeline.setValue(pos)
            self.timeline.blockSignals(False)

        self.ms_spin.blockSignals(True)
        self.ms_spin.setValue(pos)
        self.ms_spin.blockSignals(False)

        self.sec_spin.blockSignals(True)
        self.sec_spin.setValue(pos // 1000)
        self.sec_spin.blockSignals(False)

        if self.player.duration():
            self.time_label.setText(
                f"{format_time(pos)} / {format_time(self.player.duration())}"
            )

    def _on_duration(self, dur: int) -> None:
        self.timeline.setRange(0, dur)
        self.ms_spin.setRange(0, dur)
        self.sec_spin.setRange(0, (dur + 999) // 1000)

    def _toggle_play(self) -> None:
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_btn.setText("Play")
        else:
            self.player.play()
            self.play_btn.setText("Pause")

    def _accept(self) -> None:
        self.selected_ms = self.timeline.value()
        self.player.stop()
        self.accept()


# ---------------------------------------------------------------------------
# Main Application Window
# ---------------------------------------------------------------------------


class MainWindow(QWidget):
    """Main window for osu! Set Builder application."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(1100, 750)

        self.songs_dir = self._detect_songs_dir()
        self.global_bg: Optional[Path] = None
        self.diffs: List[DifficultyRow] = []
        self.preview_ms: Optional[int] = None

        self._setup_ui()
        self.setStyleSheet(DARK_THEME)

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(20, 20, 20, 20)

        # Header
        self._create_header(root)
        self._add_separator(root)

        # Toolbar
        self._create_toolbar(root)

        # Metadata
        self._create_metadata_section(root)

        # Media preview
        self._create_media_section(root)

        # Table
        self._create_difficulty_table(root)

        # Export bar
        self._create_export_bar(root)

    def _create_header(self, layout: QVBoxLayout) -> None:
        header = QVBoxLayout()
        header.setSpacing(4)

        title = QLabel(APP_NAME)
        title.setObjectName("titleLabel")
        header.addWidget(title)

        subtitle = QLabel("Create and manage osu! beatmap sets with ease")
        subtitle.setObjectName("subtitleLabel")
        header.addWidget(subtitle)

        layout.addLayout(header)

    def _add_separator(self, layout: QVBoxLayout) -> None:
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(2)
        layout.addWidget(sep)

    def _create_toolbar(self, layout: QVBoxLayout) -> None:
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        folder_btn = QPushButton("Songs Folder")
        folder_btn.setToolTip("Set the osu! Songs folder location")
        folder_btn.setObjectName("secondaryButton")
        folder_btn.clicked.connect(self._set_songs_dir)
        toolbar.addWidget(folder_btn)

        toolbar.addSpacing(20)

        add_btn = QPushButton("Add .osu Files")
        add_btn.setToolTip("Add beatmap difficulty files")
        add_btn.clicked.connect(self._add_osu)
        toolbar.addWidget(add_btn)

        bg_btn = QPushButton("Background")
        bg_btn.setToolTip("Choose a background image")
        bg_btn.clicked.connect(self._choose_global_bg)
        toolbar.addWidget(bg_btn)

        preview_btn = QPushButton("Preview Point")
        preview_btn.setToolTip("Set the audio preview point")
        preview_btn.clicked.connect(self._set_preview)
        toolbar.addWidget(preview_btn)

        toolbar.addStretch()

        clear_btn = QPushButton("Clear All")
        clear_btn.setToolTip("Clear all difficulties and reset")
        clear_btn.setObjectName("dangerButton")
        clear_btn.clicked.connect(self._clear)
        toolbar.addWidget(clear_btn)

        layout.addLayout(toolbar)

    def _create_metadata_section(self, layout: QVBoxLayout) -> None:
        group = QGroupBox("Beatmap Metadata")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(12)

        row1 = QHBoxLayout()
        self.title_edit = self._labeled_input(row1, "Title", "Song title")
        self.artist_edit = self._labeled_input(row1, "Artist", "Song artist")
        group_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.creator_edit = self._labeled_input(row2, "Creator", "Beatmap creator")
        self.source_edit = self._labeled_input(
            row2, "Source", "Source (anime, game, etc.)"
        )
        group_layout.addLayout(row2)

        row3 = QHBoxLayout()
        self.tags_edit = self._labeled_input(
            row3, "Tags", "Space-separated tags", stretch=True
        )
        group_layout.addLayout(row3)

        layout.addWidget(group)

    def _labeled_input(
        self,
        layout: QHBoxLayout,
        label: str,
        placeholder: str = "",
        stretch: bool = False,
    ) -> QLineEdit:
        container = QVBoxLayout()
        container.setSpacing(4)

        lbl = QLabel(label)
        lbl.setObjectName("sectionLabel")
        container.addWidget(lbl)

        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        container.addWidget(edit)

        if stretch:
            layout.addLayout(container, 1)
        else:
            layout.addLayout(container)

        return edit

    def _create_media_section(self, layout: QVBoxLayout) -> None:
        media = QHBoxLayout()
        media.setSpacing(20)

        # Background preview
        bg_group = QGroupBox("Background Preview")
        bg_layout = QVBoxLayout(bg_group)

        self.bg_preview = QLabel("No background selected")
        self.bg_preview.setObjectName("bgPreviewFrame")
        self.bg_preview.setAlignment(Qt.AlignCenter)
        self.bg_preview.setFixedSize(320, 180)
        bg_layout.addWidget(self.bg_preview, alignment=Qt.AlignCenter)

        media.addWidget(bg_group)

        # Preview info
        preview_group = QGroupBox("Audio Preview")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_label = QLabel("Preview point not set")
        self.preview_label.setWordWrap(True)
        preview_layout.addWidget(self.preview_label)
        preview_layout.addStretch()

        info = QLabel(
            "The preview point determines where\naudio starts in song select."
        )
        info.setObjectName("subtitleLabel")
        preview_layout.addWidget(info)

        media.addWidget(preview_group, 1)

        layout.addLayout(media)

    def _create_difficulty_table(self, layout: QVBoxLayout) -> None:
        group = QGroupBox("Difficulties")
        group_layout = QVBoxLayout(group)

        toolbar = QHBoxLayout()

        number_btn = QPushButton("Auto-Number")
        number_btn.setToolTip("Rename to 1, 2, 3...")
        number_btn.setObjectName("secondaryButton")
        number_btn.clicked.connect(self._default_diffs)
        toolbar.addWidget(number_btn)

        remove_btn = QPushButton("Remove Selected")
        remove_btn.setToolTip("Remove selected difficulty")
        remove_btn.setObjectName("secondaryButton")
        remove_btn.clicked.connect(self._remove_selected)
        toolbar.addWidget(remove_btn)

        toolbar.addStretch()

        self.diff_count = QLabel("0 difficulties")
        self.diff_count.setObjectName("subtitleLabel")
        toolbar.addWidget(self.diff_count)

        group_layout.addLayout(toolbar)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(
            ["Source File", "Difficulty Name", "Audio"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        group_layout.addWidget(self.table)

        layout.addWidget(group, 1)

    def _create_export_bar(self, layout: QVBoxLayout) -> None:
        export = QHBoxLayout()
        export.setSpacing(10)

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("subtitleLabel")
        export.addWidget(self.status_label)

        export.addStretch()

        save_btn = QPushButton("Save .osz")
        save_btn.setToolTip("Save the beatmap set to a file")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._export_save)
        export.addWidget(save_btn)

        open_btn = QPushButton("Open in osu!")
        open_btn.setToolTip("Open directly in osu!")
        open_btn.setObjectName("primaryButton")
        open_btn.clicked.connect(self._export_open)
        export.addWidget(open_btn)

        layout.addLayout(export)

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _detect_songs_dir(self) -> Path:
        """Detect the osu! Songs folder."""
        if sys.platform == "win32":
            cand = Path(os.getenv("LOCALAPPDATA", "")) / "osu!" / "Songs"
            if cand.exists():
                return cand
        return Path.home()

    def _show_bg(self, path: Optional[Path]) -> None:
        """Show background preview."""
        if path and path.exists():
            pix = QPixmap(str(path)).scaled(
                self.bg_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.bg_preview.setPixmap(pix)
        else:
            self.bg_preview.clear()
            self.bg_preview.setText("No background selected")

    def _update_bg_preview(self) -> None:
        """Update background preview from loaded difficulties."""
        bgs = {
            (d.data["path"].parent / d.data["bg"]).resolve()
            for d in self.diffs
            if d.data["bg"]
        }
        if len(bgs) == 1:
            self._show_bg(next(iter(bgs)))
        elif not self.global_bg:
            self._show_bg(None)

    def _update_diff_count(self) -> None:
        """Update the difficulty count label."""
        count = len(self.diffs)
        self.diff_count.setText(f"{count} difficult{'y' if count == 1 else 'ies'}")

    def _seed_metadata(self, info: dict) -> None:
        """Seed metadata fields from a formatted .osu file."""
        if not self.title_edit.text():
            self.title_edit.setText(info["meta"].get("Title", ""))
        if not self.artist_edit.text():
            self.artist_edit.setText(info["meta"].get("Artist", ""))
        if not self.creator_edit.text():
            self.creator_edit.setText(info["meta"].get("Creator", ""))
        if not self.source_edit.text():
            self.source_edit.setText(info["meta"].get("Source", ""))
        if not self.tags_edit.text():
            self.tags_edit.setText(info["meta"].get("Tags", ""))

    def _common_meta(self) -> Dict[str, str]:
        """Get the current metadata values."""
        return {
            "title": self.title_edit.text().strip(),
            "artist": self.artist_edit.text().strip(),
            "creator": self.creator_edit.text().strip(),
            "source": self.source_edit.text().strip(),
            "tags": self.tags_edit.text().strip(),
        }

    # -------------------------------------------------------------------------
    # UI Actions
    # -------------------------------------------------------------------------

    def _set_songs_dir(self) -> None:
        """Set the Songs folder location."""
        d = QFileDialog.getExistingDirectory(
            self, "Select osu! Songs folder", str(self.songs_dir)
        )
        if d:
            self.songs_dir = Path(d)
            self.status_label.setText(f"Songs folder: {self.songs_dir}")

    def _add_osu(self) -> None:
        """Add .osu files to the difficulty list."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Add .osu files", str(self.songs_dir), "osu files (*.osu)"
        )

        for f in map(Path, files):
            # Check for duplicates
            if any(d.data["path"] == f for d in self.diffs):
                continue

            info = read_osu(f)
            formatted = bool(FILENAME_FMT_RE.fullmatch(f.name))

            if formatted:
                self._seed_metadata(info)

            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)

            # Filename (non-editable)
            fn_item = QTableWidgetItem(f.name)
            fn_item.setFlags(fn_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 0, fn_item)

            # Difficulty name (editable)
            diff_item = QTableWidgetItem(info["difficulty"])
            self.table.setItem(row_idx, 1, diff_item)

            # Audio file (non-editable)
            audio_item = QTableWidgetItem(info["audio"])
            audio_item.setFlags(audio_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 2, audio_item)

            self.diffs.append(
                DifficultyRow(data=info, row=row_idx, formatted=formatted)
            )
            self.songs_dir = f.parent

        self._update_bg_preview()
        self._update_diff_count()
        self.status_label.setText(f"Added {len(files)} file(s)")

    def _choose_global_bg(self) -> None:
        """Choose a global background image."""
        f, _ = QFileDialog.getOpenFileName(
            self,
            "Choose background image",
            str(self.songs_dir),
            "Images (*.png *.jpg *.jpeg)",
        )
        if f:
            self.global_bg = Path(f)
            self._show_bg(self.global_bg)
            self.status_label.setText(f"Background: {self.global_bg.name}")

    def _set_preview(self) -> None:
        """Open the preview point picker dialog."""
        if not self.diffs:
            QMessageBox.warning(
                self, "No Beatmaps", "Add at least one .osu file first."
            )
            return

        audio_path = self.diffs[0].data["path"].parent / self.diffs[0].data["audio"]
        if not audio_path.exists():
            QMessageBox.warning(self, "Missing Audio", f"Could not find: {audio_path}")
            return

        dlg = PreviewPickerDialog(self, audio_path, self.preview_ms)
        if dlg.exec() == QDialog.Accepted and dlg.selected_ms is not None:
            self.preview_ms = dlg.selected_ms
            self.preview_label.setText(
                f"Preview: {format_time(self.preview_ms)} ({self.preview_ms} ms)"
            )
            self.status_label.setText(f"Preview point set to {self.preview_ms} ms")

    def _default_diffs(self) -> None:
        """Rename difficulties to 1, 2, 3..."""
        for i in range(self.table.rowCount()):
            self.table.item(i, 1).setText(str(i + 1))
        self.status_label.setText("Difficulties renamed to numbers")

    def _remove_selected(self) -> None:
        """Remove the selected difficulty."""
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            # Update diffs list
            self.diffs = [d for d in self.diffs if d.row != row]
            # Update row indices
            for d in self.diffs:
                if d.row > row:
                    d.row -= 1
            self._update_diff_count()
            self._update_bg_preview()
            self.status_label.setText("Removed difficulty")

    def _clear(self) -> None:
        """Clear all data and reset the form."""
        self.table.setRowCount(0)
        self.diffs.clear()
        self.global_bg = None
        self.preview_ms = None
        self.preview_label.setText("Preview point not set")

        for edit in (
            self.title_edit,
            self.artist_edit,
            self.creator_edit,
            self.source_edit,
            self.tags_edit,
        ):
            edit.clear()

        self._show_bg(None)
        self._update_diff_count()
        self.status_label.setText("Cleared all data")

    # -------------------------------------------------------------------------
    # Export Methods
    # -------------------------------------------------------------------------

    def _build_osz(self, target: Path) -> None:
        """Build an .osz file from the current configuration."""
        if not self.diffs:
            raise RuntimeError("No difficulties added.")

        common = self._common_meta()
        if not common["title"] or not common["artist"]:
            raise RuntimeError(
                "Title and Artist are required.\n"
                "Import a formatted .osu or enter them manually."
            )

        # Check for duplicate difficulty names
        diff_names = [self.table.item(d.row, 1).text().strip() for d in self.diffs]
        if len(diff_names) != len(set(diff_names)):
            raise RuntimeError(
                "Duplicate difficulty names detected.\n"
                "Give each row a unique name or use Auto-Number."
            )

        if self.global_bg is None:
            raise RuntimeError("Choose a background image before exporting.")

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)

            # Copy audio files
            audio_files: Dict[str, Path] = {}
            for d in self.diffs:
                audio_src = d.data["path"].parent / d.data["audio"]
                if audio_src.exists():
                    audio_files.setdefault(audio_src.name, audio_src)

            for name, src in audio_files.items():
                shutil.copy2(src, tmp / name)

            # Copy background
            bg_name = sanitize_filename(self.global_bg.name)
            shutil.copy2(self.global_bg, tmp / bg_name)

            # Write .osu files
            for d in self.diffs:
                diff_text = self.table.item(d.row, 1).text().strip()
                out_name = sanitize_filename(
                    f"{common['artist']} - {common['title']} "
                    f"({common['creator']}) [{diff_text}].osu"
                )
                rewrite_osu(
                    d.data,
                    tmp / out_name,
                    common_meta=common,
                    difficulty=diff_text,
                    audio_name=Path(d.data["audio"]).name,
                    bg_name=bg_name,
                    preview_ms=self.preview_ms,
                )

            # Create .osz
            with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for f in tmp.iterdir():
                    zf.write(f, arcname=f.name)

    def _export_save(self) -> None:
        """Save as .osz file."""
        try:
            default_name = sanitize_filename(
                f"{self.artist_edit.text()} - {self.title_edit.text()}.osz"
            )
            dest, _ = QFileDialog.getSaveFileName(
                self,
                "Save .osz",
                str(self.songs_dir / default_name),
                "osu! beatmap set (*.osz)",
            )
            if not dest:
                return

            self._build_osz(Path(dest))
            self.status_label.setText(f"Saved: {Path(dest).name}")
            QMessageBox.information(self, "Success", f"Saved to:\n{dest}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))

    def _export_open(self) -> None:
        """Create .osz and open in osu!."""
        try:
            tmp_name = sanitize_filename(
                f"{self.artist_edit.text()} - {self.title_edit.text()}.osz"
            )
            tmp_osz = Path(tempfile.gettempdir()) / tmp_name
            self._build_osz(tmp_osz)

            if sys.platform == "win32":
                os.startfile(tmp_osz)
                self.status_label.setText("Opened in osu!")
            else:
                QMessageBox.information(
                    self,
                    "Done",
                    f"Saved to:\n{tmp_osz}\n\nOpen it with osu! to import.",
                )
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))


# ---------------------------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------------------------


def main() -> None:
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    # Set application icon
    icon_path = resource_path("icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
