from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


def _rapor_sayfasi(baslik, aciklama, kolonlar):
    page = QFrame()
    page.setObjectName("MainCard")
    lay = QVBoxLayout(page)
    lay.setContentsMargins(14, 12, 14, 12)
    lay.setSpacing(10)
    head = QHBoxLayout()
    lbl = QLabel(baslik)
    lbl.setObjectName("CardTitle")
    btnExcel = QPushButton("Excel'e Aktar")
    btnExcel.setObjectName("DashboardActionButton")
    btnPdf = QPushButton("PDF Al")
    btnPdf.setObjectName("DashboardActionButton")
    head.addWidget(lbl, 1)
    head.addWidget(btnExcel)
    head.addWidget(btnPdf)
    lay.addLayout(head)
    desc = QLabel(aciklama)
    desc.setWordWrap(True)
    desc.setObjectName("DialogSubtitle")
    lay.addWidget(desc)
    tbl = QTableWidget(0, len(kolonlar))
    tbl.setHorizontalHeaderLabels(kolonlar)
    tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    tbl.setAlternatingRowColors(True)
    tbl.setMinimumHeight(280)
    lay.addWidget(tbl, 1)
    return page


def build_report_center(parent_app=None):
    root = QWidget()
    lay = QVBoxLayout(root)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(10)

    tabs = QTabWidget()
    tabs.addTab(_rapor_sayfasi("Satış Raporları", "Tarih aralığına göre satış, kâr ve belge raporları burada toplanacak.", ["Tarih", "Cari", "Belge", "Toplam", "Kâr"]), "Satış")
    tabs.addTab(_rapor_sayfasi("Cari Raporları", "Cari bakiye, borç/alacak ve ekstre raporları tek merkezden yönetilecek.", ["Cari", "Borç", "Alacak", "Bakiye", "Durum"]), "Cari")
    tabs.addTab(_rapor_sayfasi("Stok Raporları", "Kritik stok, stok değeri ve ürün hareketleri burada izlenecek.", ["Ürün", "Stok", "Min.", "Değer", "Durum"]), "Stok")
    tabs.addTab(_rapor_sayfasi("Kasa Raporları", "Nakit, kart, banka ve tahsilat hareketleri bu ekranda raporlanacak.", ["Tarih", "Kasa", "İşlem", "Tutar", "Açıklama"]), "Kasa")
    lay.addWidget(tabs, 1)
    return root


def build_report_center_placeholder(parent_app=None):
    return build_report_center(parent_app)
