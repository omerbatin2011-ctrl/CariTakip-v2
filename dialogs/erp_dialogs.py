"""v117: Ortak ERP pencere/dialog bileşenleri.

Amaç: rapor, grafik, analiz ve detay pencerelerinin aynı başlık, boşluk,
renk ve buton düzenini kullanması.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class ERPDialog(QDialog):
    def __init__(self, title: str, subtitle: str = "", parent=None, width: int = 1000, height: int = 620):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(width, height)
        self.setObjectName("ERPDialog")
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(18, 16, 18, 16)
        self.root.setSpacing(12)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        self.lblTitle = QLabel(title)
        self.lblTitle.setObjectName("DialogTitle")
        self.lblSubtitle = QLabel(subtitle)
        self.lblSubtitle.setObjectName("DialogSubtitle")
        self.lblSubtitle.setVisible(bool(subtitle))
        title_box.addWidget(self.lblTitle)
        title_box.addWidget(self.lblSubtitle)
        header.addLayout(title_box, 1)

        btn_close = QPushButton("Kapat")
        btn_close.setObjectName("GreyButton")
        btn_close.setMinimumWidth(90)
        btn_close.clicked.connect(self.close)
        header.addWidget(btn_close, 0, Qt.AlignTop)
        self.root.addLayout(header)

    def set_content(self, widget: QWidget):
        self.root.addWidget(widget, 1)
        return widget
