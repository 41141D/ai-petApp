from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor,QPen

class Renderering:
    def __init__(self,window):
        super().__init__()
        self.window = window
    def backgrounddrawing(self, painter):
        if self.window.mood == "normal":
            painter.fillRect(self.window.rect(), QColor("#31616b"))
        elif self.window.mood == "thinking":
            painter.fillRect(self.window.rect(), QColor("#1a3a4b"))
        elif self.window.mood == "error":
            painter.fillRect(self.window.rect(), QColor("red"))
        elif self.window.mood == "blink":
            painter.fillRect(self.window.rect(), QColor("#31616b"))
    def lals_body(self, painter):
        y = int(47 + self.window.breath_count)
        if self.window.mood == "normal":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#0b2330"))
            painter.drawEllipse(25, y, 200, 200)
        elif self.window.mood == "error":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("black"))
            painter.drawEllipse(25, y, 200, 200)
        elif self.window.mood == "thinking":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#0b2330"))
            painter.drawEllipse(25, 47, 200, 200)
        elif self.window.mood == "blink":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#0b2330"))
            painter.drawEllipse(25, 47, 200, 200)

    def normal_eyes(self, painter):
        y = int(112 + self.window.eye_count_up)
        x_pup = int(123 + self.window.eye_count_up)
        up_down = int(x_pup + self.window.up_down)
        right_right = int(self.window.right_left + 154)
        left_left = int(self.window.right_left + 83)
        # I USED PYQT6  FOR THE DESIGNING
        if self.window.mood == "normal":
            # eyes
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("black"))
            painter.drawEllipse(65, y, 45, 35)
            painter.drawEllipse(137, y, 45, 32)
            # pupil
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("white"))
            painter.drawEllipse(left_left, up_down, 10, 10)
            painter.drawEllipse(right_right, up_down, 10, 10)
        elif self.window.mood == "thinking":
            # eyes
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("black"))
            painter.drawEllipse(65, 109, 45, 35)
            painter.drawEllipse(137, 109, 45, 32)
            # pupil
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("white"))
            painter.drawEllipse(83, 112, 10, 10)
            painter.drawEllipse(154, 112, 10, 10)
        elif self.window.mood == "error":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(176, 45, 12))
            painter.drawEllipse(65, x_pup, 45, 35)
            painter.drawEllipse(137, x_pup, 45, 32)
        elif self.window.mood == "blink":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setPen(QPen(QColor("white"), 3))
            painter.drawLine(65, 125, 110, 125)
            painter.drawLine(137, 125, 182, 125)
    def mouth(self, painter):
        y = int(self.window.breath_count + 180)
        if self.window.mood == "normal":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("white"))
            painter.drawEllipse(97, y, 55, 15)
        elif self.window.mood == "error":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("red"))
            painter.drawEllipse(100, y, 45, 25)
        elif self.window.mood == "thinking":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("black"))
            painter.drawEllipse(100, 180, 45, 25)
        elif self.window.mood == "blink":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setPen(QPen(QColor("white"), 3))
            painter.drawEllipse(100, 180, 45, 25)
