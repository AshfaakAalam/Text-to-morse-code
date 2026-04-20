import sys

from morse_code import MORSE
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLabel
from PyQt5.QtCore import QTimer



class MorseApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Morse Code Converter")
        self.setGeometry(800,300,800,300)

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
            code = MORSE.get(char, "")
            morse_text += code + "  "
        self.output_display.setText(morse_text)




app = QApplication(sys.argv)
window = MorseApp()
window.show()
sys.exit(app.exec_())
