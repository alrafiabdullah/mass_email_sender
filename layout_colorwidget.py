from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout


class Color(QWidget):
    def __init__(self, color, position=None):
        super().__init__()
        self.color = color
        self.position = position
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)

        # add text in the widget
        text_widget = QLabel(color if self.position is None else self.position)
        text_widget.setStyleSheet(
            f"color: {'white' if self.position is None else 'black'}; font-weight: bold;"
        )
        # center the text
        text_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create layout to center the widget
        layout = QVBoxLayout()
        layout.addWidget(text_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
