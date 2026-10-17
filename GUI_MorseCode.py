import bisect
import sys

import numpy as np
import sounddevice as sd
from PyQt5.QtCore import QElapsedTimer, Qt, QTimer
from PyQt5.QtGui import QColor, QTextCharFormat, QTextCursor
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from morse_code import MORSE  # dict like {"a": ".-", "b": "-...", ...}

SAMPLE_RATE = 44100
FREQ = 800
DASH_UNITS = 3  # standard Morse is 3. Set to 2 if you prefer your "fine tuned" sound.

STYLE = """
    QWidget {
        background-color: #121212;
        color: #E0E0E0;
        font-family: "Segoe UI", Arial;
        font-size: 14px;
    }
    QTextEdit {
        background-color: #1E1E1E;
        border: 2px solid #333;
        border-radius: 10px;
        padding: 10px;
        font-size: 15px;
    }
    QSpinBox {
        background-color: #1E1E1E;
        border: 1px solid #333;
        border-radius: 6px;
        padding: 4px;
    }
    QLabel#title {
        font-size: 24px;
        font-weight: bold;
        color: #00FFCC;
    }
    QLabel#output {
        /* card-style output box */
        background-color: #1E1E1E;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 15px;
        font-size: 18px;
    }
    QPushButton {
        border: none;
        border-radius: 10px;
        padding: 10px;
        font-weight: bold;
        color: white;
    }
    QPushButton#play { background-color: #2196F3; }
    QPushButton#play:hover { background-color: #1E88E5; }
    QPushButton#stop { background-color: #f44336; }
    QPushButton#stop:hover { background-color: #e53935; }
    QPushButton:disabled { background-color: #555; color: #999; }
"""


def tone(duration, freq=FREQ, fade=0.005):
    """Sine tone with a short fade in/out so there are no clicks."""
    n = int(SAMPLE_RATE * duration)
    t = np.arange(n) / SAMPLE_RATE
    wave = np.sin(2 * np.pi * freq * t)
    f = min(int(SAMPLE_RATE * fade), n // 2)
    if f > 0:
        ramp = np.linspace(0, 1, f)
        wave[:f] *= ramp
        wave[-f:] *= ramp[::-1]
    return wave.astype(np.float32)


def silence(duration):
    return np.zeros(int(SAMPLE_RATE * duration), dtype=np.float32)


def build_audio(text, unit):
    """
    Render the whole message to one audio buffer.

    Returns (audio, segments) where segments is a list of
    (start_sec, end_sec, char_index) for every dot/dash, used for highlighting.
    """
    chunks = []
    segments = []
    t = 0.0
    gap_before = 0  # units of silence owed before the next letter

    for idx, ch in enumerate(text):
        if ch.isspace():
            gap_before = 7
            continue

        code = MORSE.get(ch.lower())
        if not code:
            continue

        if chunks and gap_before:
            chunks.append(silence(gap_before * unit))
            t += gap_before * unit

        for i, symbol in enumerate(code):
            if i > 0:  # inter-symbol gap = 1 unit
                chunks.append(silence(unit))
                t += unit
            dur = unit if symbol == "." else unit * DASH_UNITS
            chunks.append(tone(dur))
            segments.append((t, t + dur, idx))
            t += dur

        gap_before = 3  # inter-letter gap

    audio = np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.float32)
    return audio, segments


class MorseApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Morse Code Converter")
        self.resize(800, 420)
        self.setStyleSheet(STYLE)

        self.segments = []
        self.seg_starts = []
        self.total = 0.0
        self.clock = QElapsedTimer()
        self.timer = QTimer(self)
        self.timer.setInterval(15)
        self.timer.timeout.connect(self.tick)

        title = QLabel("🔊 Morse Code Converter")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)

        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("Enter your text here...")
        self.input_box.textChanged.connect(self.convert_text)

        self.output_display = QLabel("")
        self.output_display.setObjectName("output")
        self.output_display.setWordWrap(True)
        self.output_display.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.wpm = QSpinBox()
        self.wpm.setRange(5, 40)
        self.wpm.setValue(12)
        self.wpm.setSuffix(" WPM")
        speed_row = QHBoxLayout()
        speed_row.addWidget(QLabel("Speed:"))
        speed_row.addWidget(self.wpm)
        speed_row.addStretch()

        self.play_button = QPushButton("▶ Play Morse Sound")
        self.play_button.setObjectName("play")
        self.play_button.clicked.connect(self.start_playback)

        self.stop_button = QPushButton("■ Stop")
        self.stop_button.setObjectName("stop")
        self.stop_button.clicked.connect(self.stop_playback)
        self.stop_button.setEnabled(False)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(title)
        layout.addWidget(self.input_box)
        layout.addWidget(QLabel("Morse Output:"))
        layout.addWidget(self.output_display)
        layout.addLayout(speed_row)
        layout.addWidget(self.play_button)
        layout.addWidget(self.stop_button)

    # ---------- text -> morse ----------
    def convert_text(self):
        parts = []
        for ch in self.input_box.toPlainText():
            if ch.isspace():
                parts.append("/")
            else:
                code = MORSE.get(ch.lower())
                if code:
                    parts.append(code)
        self.output_display.setText("  ".join(parts))

    # ---------- playback ----------
    def start_playback(self):
        text = self.input_box.toPlainText()
        unit = 1.2 / self.wpm.value()  # standard PARIS timing
        audio, self.segments = build_audio(text, unit)
        if audio.size == 0:
            return

        self.seg_starts = [s[0] for s in self.segments]
        self.total = audio.size / SAMPLE_RATE

        self.input_box.setReadOnly(True)
        self.wpm.setEnabled(False)
        self.play_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        sd.play(audio, SAMPLE_RATE)  # non-blocking, no extra thread needed
        self.clock.start()
        self.timer.start()

    def stop_playback(self):
        self.timer.stop()
        sd.stop()
        self.highlight(None)
        self.input_box.setReadOnly(False)
        self.wpm.setEnabled(True)
        self.play_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def tick(self):
        t = self.clock.elapsed() / 1000
        if t >= self.total:
            self.stop_playback()
            return
        i = bisect.bisect_right(self.seg_starts, t) - 1
        if i >= 0 and t < self.segments[i][1]:
            self.highlight(self.segments[i][2])
        else:
            self.highlight(None)

    def highlight(self, index):
        """Highlight one character using ExtraSelections (doesn't touch the document)."""
        if index is None:
            self.input_box.setExtraSelections([])
            return
        cursor = self.input_box.textCursor()
        cursor.setPosition(index)
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 1)

        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#00FFCC"))
        fmt.setForeground(QColor("#000000"))

        sel = QTextEdit.ExtraSelection()
        sel.cursor = cursor
        sel.format = fmt
        self.input_box.setExtraSelections([sel])

    def closeEvent(self, event):
        sd.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MorseApp()
    window.show()
    sys.exit(app.exec_())