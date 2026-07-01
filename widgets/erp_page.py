from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class ERPPage(QWidget):
    """DAL ERP Next için standart sayfa tabanı.

    Yeni sayfalarda ortak yaşam döngüsü bu sınıf üzerinden yönetilecek.
    Mevcut ekranlar v120'de bozulmadan çalışmaya devam eder; sonraki
    sürümlerde modüller kademeli olarak ERPPage yapısına taşınacaktır.
    """

    page_key = "base"
    page_title = "DAL ERP"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(16, 16, 16, 16)
        self.root_layout.setSpacing(12)

    def load_data(self):
        pass

    def refresh(self):
        self.load_data()

    def apply_theme(self):
        pass

    def before_show(self):
        pass

    def before_close(self):
        pass


def placeholder_page(title: str, subtitle: str = "Bu ekran sonraki sürümlerde ERPPage yapısına taşınacak."):
    page = ERPPage()
    card = QFrame()
    card.setObjectName("PanelCard")
    layout = QVBoxLayout(card)
    lbl_title = QLabel(title)
    lbl_title.setObjectName("SectionTitle")
    lbl_subtitle = QLabel(subtitle)
    lbl_subtitle.setWordWrap(True)
    layout.addWidget(lbl_title)
    layout.addWidget(lbl_subtitle)
    page.root_layout.addWidget(card)
    page.root_layout.addStretch()
    return page
