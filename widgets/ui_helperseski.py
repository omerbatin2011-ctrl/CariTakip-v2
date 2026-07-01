"""v117: DAL ERP ortak UI bileşenleri.

Bu dosya, sonraki sürümlerde ekrandaki kart/buton/panel tekrarlarını azaltmak
ve Fluent/Windows 11 çizgisindeki görünümü tek merkezden yönetmek için başlatıldı.
Mevcut ekranlarla uyumlu kalması için bileşenler sade tutuldu.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class ERPPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelCard")


class ERPCard(QFrame):
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("MainCard")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(14, 12, 14, 12)
        self.layout.setSpacing(8)
        if title:
            lbl = QLabel(title)
            lbl.setObjectName("CardTitle")
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.layout.addWidget(lbl)


class ERPButton(QPushButton):
    def __init__(self, text: str, primary: bool = False, parent=None):
        super().__init__(text, parent)
        self.setObjectName("PrimaryButton" if primary else "DashboardActionButton")
        self.setMinimumHeight(38)


class ERPStatCard(QFrame):
    def __init__(self, title: str, value: str = "0,00", subtitle: str = "", icon: str = "", color: str = "#2563EB", parent=None):
        super().__init__(parent)
        self.setObjectName("MetricCard")
        self.setMinimumHeight(72)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(11, 9, 11, 9)
        lay.setSpacing(9)
        if icon:
            ico = QLabel(icon)
            ico.setAlignment(Qt.AlignCenter)
            ico.setFixedSize(38, 38)
            ico.setStyleSheet(f"background:{color};color:white;border-radius:12px;font-size:18px;font-weight:900;")
            lay.addWidget(ico)
        texts = QVBoxLayout()
        self.lblTitle = QLabel(title)
        self.lblTitle.setObjectName("MetricTitle")
        self.lblValue = QLabel(value)
        self.lblValue.setObjectName("MetricValue")
        self.lblSubtitle = QLabel(subtitle)
        self.lblSubtitle.setObjectName("MetricSub")
        texts.addWidget(self.lblTitle)
        texts.addWidget(self.lblValue)
        texts.addWidget(self.lblSubtitle)
        lay.addLayout(texts)
        lay.addStretch()


def action_button(text, primary=False):
    return ERPButton(text, primary=primary)


class ERPSectionHeader(QFrame):
    """Küçük başlık + sağ aksiyon alanı için ortak bölüm başlığı."""
    def __init__(self, title: str, action_text: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("SectionHeader")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        self.lblTitle = QLabel(title)
        self.lblTitle.setObjectName("SectionTitle")
        lay.addWidget(self.lblTitle, 1)
        self.btnAction = None
        if action_text:
            self.btnAction = ERPButton(action_text)
            self.btnAction.setMinimumHeight(32)
            lay.addWidget(self.btnAction)


class ERPInfoTile(QFrame):
    """Dashboard'da tablo yerine kullanılan kompakt bilgi kutusu."""
    def __init__(self, title: str, text: str = "", accent: str = "blue", parent=None):
        super().__init__(parent)
        self.setObjectName(f"InfoTile_{accent}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(5)
        self.lblTitle = QLabel(title)
        self.lblTitle.setObjectName("InfoTileTitle")
        self.lblText = QLabel(text)
        self.lblText.setWordWrap(True)
        self.lblText.setObjectName("InfoTileText")
        lay.addWidget(self.lblTitle)
        lay.addWidget(self.lblText)
