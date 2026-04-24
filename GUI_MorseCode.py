import sys
import numpy as np
import sounddevice as sd
from morse_code import MORSE
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLabel, QPushButton
from PyQt5.QtCore import Qt
import threading


def generate_tone(freq=800, duration=0.2, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = np.sin(freq * t * 2 * np.pi)
    return wave.astype(np.float32)


class MorseApp(QWidget):


    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: #E0E0E0;
                font-family: Segoe UI, Arial;
                font-size: 14px;
            }

            QTextEdit {
                background-color: #1E1E1E;
                border: 2px solid #333;
                border-radius: 10px;
                padding: 10px;
                font-size: 15px;
            }

            QLabel {
                font-size: 16px;
            }

            QPushButton {
                background-color: #4CAF50;
                border: none;
                border-radius: 10px;
                padding: 10px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #45A049;
            }

            QPushButton:pressed {
                background-color: #3e8e41;
            }

            QPushButton:disabled {
                background-color: #555;
                color: #999;
            }
        """)
        self.title_label = QLabel("🔊 Morse Code Converter")
        self.title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #00FFCC;
        """)
        self.title_label.setAlignment(Qt.AlignCenter)

        self.UNIT = 0.5

        self.play_thread = None
        self.stop_event = threading.Event()

        self.setWindowTitle("Morse Code Converter")
        self.setGeometry(800, 300, 800, 300)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(self.title_label)

        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("Enter your text here...")
        self.input_box.textChanged.connect(self.convert_text)

        self.output_label = QLabel("Morse Output:")
        self.output_display = QLabel("")

        self.output_display.setStyleSheet("""
            background-color: #1E1E1E;
            border-radius: 10px;                            # Makes cards for output
            padding: 15px;
            font-size: 18px;
            border: 1px solid #333;
        """)

        self.output_display.setWordWrap(True)

        self.play_button = QPushButton("▶ Play Morse Sound")
        self.play_button.clicked.connect(self.start_playback)

        self.stop_button = QPushButton("■ Stop")
        self.stop_button.clicked.connect(self.stop_playback)
        self.stop_button.setEnabled(False)

        self.play_button.setStyleSheet("""
            background-color: #2196F3;
            color: white;
            border-radius: 10px;
            padding: 10px;
            font-weight: bold;
        """)

        self.stop_button.setStyleSheet("""
            background-color: #f44336;
            color: white;
            border-radius: 10px;
            padding: 10px;
            font-weight: bold;
        """)

        layout.addWidget(self.input_box)
        layout.addWidget(self.output_label)
        layout.addWidget(self.output_display)
        layout.addWidget(self.play_button)
        layout.addWidget(self.stop_button)
        self.setLayout(layout)

    def convert_text(self):
        text = self.input_box.toPlainText().lower()
        morse_parts = []
        for char in text:
            if char == " ":
                morse_parts.append("/")
            else:
                morse_parts.append(MORSE.get(char, ""))
        self.output_display.setText("  ".join(morse_parts))



    def play_dot(self):

        audio = generate_tone(duration=self.UNIT)
        sd.play(audio, samplerate=44100)
        sd.wait()

    def play_dash(self):

        audio = generate_tone(duration=self.UNIT * 2)  #fine tuned the dash to be
                                                        #  2 times the dot
                                                         #   WHY? Bcz it sounds better"""
        sd.play(audio, samplerate=44100)
        sd.wait()

    def start_playback(self):
        text = self.input_box.toPlainText().lower()
        if not text.strip():
            return

        self.stop_event.clear()
        self.play_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self.play_thread = threading.Thread(
            target=self.play_morse_text,
            args=(text,),
            daemon=True,
        )
        self.play_thread.start()

    def stop_playback(self):
        self.stop_event.set()
        sd.stop()
        self.play_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def play_morse_text(self, text):
        first_char = True

        for char in text:
            if self.stop_event.is_set():
                sd.stop()
                break

            if char == " ":
                # word gap is 7 units
                if self.stop_event.wait(timeout=self.UNIT * 7):
                    sd.stop()
                    break
                first_char = True
                continue

            code = MORSE.get(char, "")
            if not code:
                continue

            # inter-character gap = 3 units
            if not first_char:
                if self.stop_event.wait(timeout=(self.UNIT) * 3):
                    sd.stop()
                    break
            first_char = False

            for i, symbol in enumerate(code):
                if self.stop_event.is_set():
                    sd.stop()
                    return

                if symbol == ".":
                    self.play_dot()
                elif symbol == "-":
                    self.play_dash()

                # inter-symbol gap is 1 unit
                if self.stop_event.wait(timeout=(self.UNIT)/1000000):  # fine tuned the inter-symbol
                                                                        # gap to sound natural
                    sd.stop()
                    return

            self.play_button.setEnabled(True)
            self.stop_button.setEnabled(False)


app = QApplication(sys.argv)
window = MorseApp()
window.show()
sys.exit(app.exec_())