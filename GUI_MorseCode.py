import sys
import numpy as np
import simpleaudio as sa
from morse_code import MORSE
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLabel
from PyQt5.QtCore import QTimer
import threading


def generate_tone(freq=800, duration=0.2, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = np.sin(freq * t * 2 * np.pi)
    audio = (wave * 32767).astype(np.int16)
    return audio

def play_sound(duration):
    audio = generate_tone(duration=duration)
    sa.play_buffer(audio, 1, 2, 44100)

class MorseApp(QWidget):
    def __init__(self):
        super().__init__()

        self.last_text = ""
        self.setWindowTitle("Morse Code Converter")
        self.setGeometry(800,800,800,300)

        layout = QVBoxLayout()
        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("Enter your Text Here...")
        self.input_box.textChanged.connect(self.convert_text)

        self.output_label = QLabel("Morse Output:")
        self.output_display = QLabel("")
        self.output_display.setStyleSheet("font-size: 18px;")

        layout.addWidget(self.input_box)
        layout.addWidget(self.output_label)
        layout.addWidget(self.output_display)

        self.setLayout(layout)

    def convert_text(self):
        text = self.input_box.toPlainText().lower()

        morse_text = ""
        for char in text:
            morse_text += MORSE.get(char, "") + " "

        self.output_display.setText(morse_text)

        # Only play new characters
        new_part = text[len(self.last_text):]

        if new_part:
            new_morse = " ".join(MORSE.get(c, "") for c in new_part)
            threading.Thread(target=self.play_morse, args=(new_morse,), daemon=True).start()

        self.last_text = text

    def play_morse(self, morse_text):
        UNIT = 0.15

        for symbol in morse_text:
            if symbol == ".":
                play_sound(UNIT)
            elif symbol == "-":
                play_sound(UNIT * 3)

            sa.sleep(int(UNIT * 1000))

app = QApplication(sys.argv)
window = MorseApp()
window.show()
sys.exit(app.exec_())
