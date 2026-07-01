import sys
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.config import PROGRAM_SERI_NO, RESET_KODU_GECERLILIK_DAKIKA, YETKILI_RESET_SERI_NO
from moduller.reset_kodu import reset_kodu_uret, seri_no_temizle


class ResetKoduUretici(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("001 Yetkili Reset Kodu Üretici")
        self.resize(440, 260)
        self.setStyleSheet("""
            QWidget { background: #F8FAFC; font-family: Segoe UI; }
            QLabel#Title { font-size: 22px; font-weight: 900; color: #0F172A; }
            QLabel { color: #475569; font-size: 13px; }
            QLineEdit { background: white; border: 1px solid #CBD5E1; border-radius: 12px; padding: 12px; font-size: 15px; }
            QPushButton { background: #4F46E5; color: white; border: none; border-radius: 12px; padding: 12px; font-weight: 900; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        title = QLabel("001 Reset Kodu Üretici")
        title.setObjectName("Title")
        layout.addWidget(title)
        layout.addWidget(QLabel(f"Bu araç yetkili seri no için hazırlanmıştır: {YETKILI_RESET_SERI_NO}"))
        self.txt = QLineEdit()
        self.txt.setPlaceholderText("Müşteri program seri no yazın, örn: 2026060145")
        layout.addWidget(self.txt)
        btn = QPushButton("Reset Kodu Üret")
        btn.clicked.connect(self.uret)
        layout.addWidget(btn)
        self.lbl = QLabel("Kod üretildikten sonra müşteriye verilir. Kod kısa süreli ve tek kullanımlıktır.")
        self.lbl.setWordWrap(True)
        self.lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl)

    def uret(self):
        if str(PROGRAM_SERI_NO) != str(YETKILI_RESET_SERI_NO):
            QMessageBox.critical(self, "Yetkisiz", "Bu araç yalnızca 001 seri nolu yetkili programda kullanılmalıdır.")
            return
        try:
            seri = seri_no_temizle(self.txt.text())
            kod = reset_kodu_uret(seri)
        except Exception as hata:
            QMessageBox.warning(self, "Hata", str(hata))
            return
        self.lbl.setText(f"Seri No: {seri}\nReset Kodu: {kod}\nGeçerlilik: yaklaşık {RESET_KODU_GECERLILIK_DAKIKA} dakika\nÜretim: {datetime.now().strftime('%d.%m.%Y %H:%M')}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ResetKoduUretici()
    w.show()
    sys.exit(app.exec())
