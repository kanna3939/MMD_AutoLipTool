from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
import sys

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("EXE Test")
layout = QVBoxLayout()

label = QLabel("PyInstallerでexe化できるか確認中")
layout.addWidget(label)

window.setLayout(layout)
window.resize(320, 120)
window.show()

sys.exit(app.exec())