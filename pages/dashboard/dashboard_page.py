from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from moduller.responsive import page_scroll

_MATPLOTLIB_CACHE = None

def _matplotlib_backend():
    """Matplotlib'i sadece kullanıcı grafiği açınca yükler."""
    global _MATPLOTLIB_CACHE
    if _MATPLOTLIB_CACHE is not None:
        return _MATPLOTLIB_CACHE
    try:
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.figure import Figure
        _MATPLOTLIB_CACHE = (True, FigureCanvas, Figure)
    except Exception:
        _MATPLOTLIB_CACHE = (False, None, None)
    return _MATPLOTLIB_CACHE


def _dashboard_grafik_hazirla(self, grafik_l):
    """Dashboard grafiğini ilk gösterimde oluşturur; açılışı hafifletir."""
    if hasattr(self, "dashboardCanvas") or getattr(self, "_dashboard_grafik_denendi", False):
        return hasattr(self, "dashboardCanvas")
    self._dashboard_grafik_denendi = True
    matplotlib_var, FigureCanvas, Figure = _matplotlib_backend()
    if not matplotlib_var:
        return False
    self.dashboardFigure = Figure(figsize=(6.4, 2.8), dpi=95)
    self.dashboardFigure.patch.set_facecolor("#FFFFFF")
    self.dashboardCanvas = FigureCanvas(self.dashboardFigure)
    self.dashboardCanvas.setMinimumHeight(230)
    self.dashboardCanvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    self.dashboardCanvas.setStyleSheet("background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;")
    grafik_l.addWidget(self.dashboardCanvas, 1)
    self.dashboardCanvas.setVisible(False)
    self.dashboardAx = self.dashboardFigure.add_subplot(111)
    self.dashboardAx.set_facecolor("#FFFFFF")
    for spine in ("top", "right"):
        self.dashboardAx.spines[spine].set_visible(False)
    self.dashboardAx.spines["left"].set_color("#E2E8F0")
    self.dashboardAx.spines["bottom"].set_color("#E2E8F0")
    self.dashboardAx.tick_params(colors="#64748B", labelsize=9)
    self.figSatis = self.dashboardFigure
    self.canvasSatis = self.dashboardCanvas
    return True


APP_VERSION = "v134"


def _content_width(self):
    try:
        sidebar_w = self.sidebar.width() if hasattr(self, "sidebar") else 250
        return max(360, int(self.width() - sidebar_w - 36))
    except Exception:
        return 1100


def _metric_columns(width):
    """KPI kartları için responsive kırılımlar.

    v125: kartlar artık sınırsız uzamaz
    ekran genişledikçe
    daha fazla kolon açılır, kartlar ideal genişlikte kalır.
    """
    if width >= 1640:
        return 6
    if width >= 1360:
        return 5
    if width >= 1120:
        return 4
    if width >= 860:
        return 3
    if width >= 560:
        return 2
    return 1


def _quick_columns(width):
    """Hızlı işlem butonları için responsive kırılımlar."""
    if width >= 1500:
        return 7
    if width >= 1180:
        return 4
    if width >= 760:
        return 3
    if width >= 520:
        return 2
    return 1


def _card_label(text, bg, border, color):
    lbl = QLabel(text)
    lbl.setMinimumHeight(64)
    lbl.setWordWrap(True)
    lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    lbl.setStyleSheet(
        f"background:{bg};border:1px solid {border};border-radius:12px;"
        f"padding:11px 13px;font-size:12px;font-weight:800;color:{color};"
    )
    return lbl


def _clear_grid(grid):
    while grid.count():
        item = grid.takeAt(0)
        if item and item.widget():
            item.widget().setParent(None)


def _place_grid(grid, widgets, columns):
    _clear_grid(grid)
    columns = max(1, int(columns or 1))
    for i, widget in enumerate(widgets):
        grid.addWidget(widget, i // columns, i % columns)
    # v125: KPI kartları ve hızlı işlem butonları boş alanı sınırsız doldurmasın.
    # Kolonlar içerik genişliğine göre kalsın; kalan alan sağda nefes boşluğu olarak durur.
    for c in range(max(12, columns)):
        grid.setColumnStretch(c, 0)


def _table(rows=5):
    tbl = QTableWidget()
    tbl.verticalHeader().setVisible(False)
    tbl.setEditTriggers(QTableWidget.NoEditTriggers)
    tbl.setSelectionBehavior(QTableWidget.SelectRows)
    tbl.setAlternatingRowColors(True)
    tbl.setMinimumHeight(115 if rows <= 5 else 165)
    tbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    tbl.setStyleSheet("""
        QTableWidget { background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; gridline-color:#E5E7EB; font-size:12px; alternate-background-color:#F8FAFC; }
        QTableWidget::item { padding:6px; }
        QHeaderView::section { background:#F8FAFC; color:#334155; padding:7px; border:none; font-weight:800; font-size:12px; }
    """)
    return tbl


def _section_title(text):
    lbl = QLabel(text)
    lbl.setStyleSheet("font-size:17px;font-weight:900;color:#0B1220;")
    return lbl


def _mini_list_label(text="Henüz veri yok"):
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setMinimumHeight(118)
    lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    lbl.setStyleSheet(
        "background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;"
        "padding:12px;color:#334155;font-size:12px;font-weight:700;line-height:145%;"
    )
    return lbl


def build_dashboard(self):
    """v117 dashboard: kompakt kontrol paneli, tema uyumu ve detay pencereleri."""
    content = QFrame()
    content.setObjectName("DashboardContent")
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(14, 10, 14, 8)
    content_layout.setSpacing(9)

    kullanilabilir = _content_width(self)

    # v119: Üst bar artık ana pencere kabuğunda merkezi olarak oluşturuluyor.

    self.dashboardMetricGrid = QGridLayout()
    self.dashboardMetricGrid.setSpacing(10)
    metric_defs = [
        ("lblBugunSatisKart", "₺", "Bugünkü Satış", "0,00", "Günün satış toplamı", "#2563EB", "#FFFFFF"),
        ("lblDashboardTahsilat", "✓", "Tahsilat", "0,00", "Bugünkü tahsilat", "#059669", "#FFFFFF"),
        ("lblDashboardAylikSatis", "↗", "Aylık Satış", "0,00", "Bu ay kesilen satış", "#7C3AED", "#FFFFFF"),
        ("lblDashboardBorc", "!", "Açık Alacak", "0,00", "Tahsilat bekleyen", "#F97316", "#FFFFFF"),
        ("lblDashboardKasaToplam", "₺", "Kasa", "0,00", "Nakit + kart", "#0EA5E9", "#FFFFFF"),
        ("lblKritikStokKart", "!", "Kritik Stok", "0 ürün", "Kritik seviyedeki ürün", "#DC2626", "#FFFFFF"),
    ]
    self.dashboardMetricWidgets = []
    for attr, ikon, baslik, deger, alt_metin, ikon_bg, ikon_color in metric_defs:
        lbl = self.modern_kart_olustur(self.dashboardMetricGrid, 0, 0, ikon, baslik, deger, alt_metin, ikon_bg, ikon_color)
        setattr(self, attr, lbl)
        self.dashboardMetricWidgets.append(self.dashboardMetricGrid.itemAt(self.dashboardMetricGrid.count() - 1).widget())
    _place_grid(self.dashboardMetricGrid, self.dashboardMetricWidgets, _metric_columns(kullanilabilir))
    content_layout.addLayout(self.dashboardMetricGrid)

    self.dashboardQuickGrid = QGridLayout()
    self.dashboardQuickGrid.setSpacing(8)
    self.dashboardQuickButtons = []

    def hizli_btn(text, func, primary=False):
        b = QPushButton(text)
        b.setObjectName("PrimaryButton" if primary else "DashboardActionButton")
        b.setMinimumHeight(38)
        b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        b.clicked.connect(func)
        self.dashboardQuickButtons.append(b)
        return b

    hizli_btn("+ Yeni Satış", lambda: self.sayfa_goster("satis"), True)
    hizli_btn("Tahsilat Al", lambda: self.sayfa_goster("tahsilat"))
    hizli_btn("Ürün Ekle", lambda: self.sayfa_goster("stok"))
    hizli_btn("Cari Ekle", lambda: self.sayfa_goster("cari"))
    hizli_btn("Grafik Merkezi", self.dashboard_grafik_penceresi_ac)
    hizli_btn("Rapor Merkezi", self.dashboard_rapor_penceresi_ac)
    hizli_btn("Ayarlar Merkezi", self.dashboard_ayarlar_penceresi_ac)
    _place_grid(self.dashboardQuickGrid, self.dashboardQuickButtons, _quick_columns(kullanilabilir))
    content_layout.addLayout(self.dashboardQuickGrid)

    self.dashboardMainArea = QWidget()
    self.dashboardMainLayout = QGridLayout(self.dashboardMainArea)
    self.dashboardMainLayout.setContentsMargins(0, 0, 0, 0)
    self.dashboardMainLayout.setSpacing(12)

    self.grafikKart = QFrame()
    self.grafikKart.setObjectName("MainCard")
    grafik_l = QVBoxLayout(self.grafikKart)
    grafik_l.setContentsMargins(16, 14, 16, 14)
    grafik_l.setSpacing(9)
    grafik_header = QHBoxLayout()
    grafik_header.setContentsMargins(0, 0, 0, 0)
    grafik_header.setSpacing(8)
    grafik_baslik = QLabel("Grafik")
    grafik_baslik.setStyleSheet("font-size:16px;font-weight:900;color:#0B1220;")
    self.btnDashboardGrafikToggle = QPushButton("Aç / Kapa")
    self.btnDashboardGrafikToggle.setMinimumHeight(34)
    self.btnDashboardGrafikToggle.setMaximumWidth(135)
    self.btnDashboardGrafikToggle.setStyleSheet("""
        QPushButton { background:#FFFFFF; border:1px solid #CBD5E1; border-radius:9px; padding:7px 10px; font-size:12px; font-weight:800; color:#0F172A; }
        QPushButton:hover { background:#F8FAFC; border-color:#94A3B8; }
    """)
    grafik_header.addWidget(grafik_baslik, 1)
    grafik_header.addWidget(self.btnDashboardGrafikToggle)
    grafik_l.addLayout(grafik_header)
    self.grafikKart.setMaximumHeight(62)
    self.lblSatisGrafik = QLabel("Grafiği görmek için 'Grafiği Göster' düğmesine basın.")
    self.lblSatisGrafik.setAlignment(Qt.AlignCenter)
    self.lblSatisGrafik.setMinimumHeight(230)
    self.lblSatisGrafik.setStyleSheet("background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:12px;color:#334155;font-family:Consolas, monospace;font-size:12px;font-weight:800;")
    grafik_l.addWidget(self.lblSatisGrafik, 1)
    self.lblSatisGrafik.setVisible(False)

    self.dashboardGrafikAcik = False

    def dashboard_grafik_toggle():
        self.dashboardGrafikAcik = not getattr(self, "dashboardGrafikAcik", False)
        acik = self.dashboardGrafikAcik
        if acik and not hasattr(self, "dashboardCanvas"):
            try:
                _dashboard_grafik_hazirla(self, grafik_l)
            except Exception:
                pass
        if hasattr(self, "dashboardCanvas"):
            self.dashboardCanvas.setVisible(acik)
        if hasattr(self, "lblSatisGrafik"):
            self.lblSatisGrafik.setVisible(acik and not getattr(self, "dashboardCanvas", None))
        self.grafikKart.setMaximumHeight(320 if acik else 62)
        self.btnDashboardGrafikToggle.setText("Grafiği Gizle" if acik else "Grafiği Göster")
        if hasattr(self, "dashboard_reflow"):
            try:
                self.dashboard_reflow()
            except Exception:
                pass
        if acik and hasattr(self, "satis_grafik_guncelle"):
            try:
                self.satis_grafik_guncelle()
            except Exception:
                pass

    self.btnDashboardGrafikToggle.clicked.connect(dashboard_grafik_toggle)

    self.dashboardKasaKart = QFrame()
    self.dashboardKasaKart.setObjectName("MainCard")
    kasa_l = QVBoxLayout(self.dashboardKasaKart)
    kasa_l.setContentsMargins(16, 14, 16, 14)
    kasa_l.setSpacing(9)
    kasa_baslik = QLabel("Kasa Özeti")
    kasa_baslik.setStyleSheet("font-size:16px;font-weight:900;color:#0B1220;")
    kasa_l.addWidget(kasa_baslik)
    self.lblDashboardKasaNakit = _card_label("Nakit Kasa\n0,00 ", "#FFFFFF", "#E2E8F0", "#0F172A")
    self.lblDashboardKasaKart = _card_label("Kart Tahsilat\n0,00 ", "#EFF6FF", "#BFDBFE", "#1D4ED8")
    self.lblBugunKar = _card_label("Bugünkü Kâr\n0,00 ", "#ECFDF5", "#A7F3D0", "#047857")
    self.lblToplamUrun = _card_label("Toplam Ürün\n0", "#F0F9FF", "#BAE6FD", "#0369A1")
    kasa_l.addWidget(self.lblDashboardKasaNakit)
    kasa_l.addWidget(self.lblDashboardKasaKart)
    kasa_l.addWidget(self.lblBugunKar)
    kasa_l.addWidget(self.lblToplamUrun)
    kasa_l.addStretch()


    self.dashboardBildirimKart = QFrame()
    self.dashboardBildirimKart.setObjectName("MainCard")
    bildirim_l = QVBoxLayout(self.dashboardBildirimKart)
    bildirim_l.setContentsMargins(16, 14, 16, 14)
    bildirim_l.setSpacing(9)
    bildirim_l.addWidget(_section_title("Bildirim Merkezi"))
    self.lblBildirimKritikStok = _card_label("Kritik Stok\n0 ürün", "#FEF2F2", "#FECACA", "#B91C1C")
    self.lblBildirimVade = _card_label("Açık Alacak\n0,00", "#FFF7ED", "#FED7AA", "#C2410C")
    self.lblBildirimBugunSatis = _card_label("Bugünkü Satış\n0,00", "#EFF6FF", "#BFDBFE", "#1D4ED8")
    self.lblBildirimTeklif = _card_label("Bekleyen Teklif\n0", "#F5F3FF", "#DDD6FE", "#6D28D9")
    for w in (self.lblBildirimKritikStok, self.lblBildirimVade, self.lblBildirimBugunSatis, self.lblBildirimTeklif):
        bildirim_l.addWidget(w)
    bildirim_l.addStretch()

    self.dashboardSonIslemlerKart = QFrame()
    self.dashboardSonIslemlerKart.setObjectName("MainCard")
    islem_l = QVBoxLayout(self.dashboardSonIslemlerKart)
    islem_l.setContentsMargins(16, 14, 16, 14)
    islem_l.setSpacing(8)
    islem_header = QHBoxLayout()
    islem_header.addWidget(_section_title("Son İşlemler"), 1)
    btnIslemDetay = QPushButton("Pencerede Aç")
    btnIslemDetay.setMinimumHeight(34)
    btnIslemDetay.setMaximumWidth(130)
    btnIslemDetay.clicked.connect(self.dashboard_son_islemler_penceresi_ac)
    islem_header.addWidget(btnIslemDetay)
    islem_l.addLayout(islem_header)
    self.lblSonIslemOzet = QLabel("Henüz işlem yok")
    self.lblSonIslemOzet.setWordWrap(True)
    self.lblSonIslemOzet.setStyleSheet("background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:12px;color:#334155;font-size:12px;font-weight:700;line-height:140%;")
    self.lblSonIslemOzet.setMinimumHeight(78)
    islem_l.addWidget(self.lblSonIslemOzet)
    self.tblDashboardSonIslemler = _table()
    self.tblDashboardSonIslemler.setColumnCount(4)
    self.tblDashboardSonIslemler.setHorizontalHeaderLabels(["Tarih", "İşlem", "Açıklama", "Tutar"])
    self.tblDashboardSonIslemler.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    self.tblDashboardSonIslemler.setVisible(False)
    islem_l.addWidget(self.tblDashboardSonIslemler)
    islem_l.addStretch(1)

    self.dashboardSatisKart = QFrame()
    self.dashboardSatisKart.setObjectName("MainCard")
    self.dashboardSatisKart.setMaximumHeight(150)
    satis_l = QVBoxLayout(self.dashboardSatisKart)
    satis_l.setContentsMargins(16, 14, 16, 14)
    satis_l.setSpacing(9)
    satis_header = QHBoxLayout()
    satis_header.addWidget(_section_title("Son Satışlar"), 1)
    btnSatisDetay = QPushButton("Pencerede Aç")
    btnSatisDetay.setMaximumWidth(130)
    btnSatisDetay.clicked.connect(self.dashboard_son_satislar_penceresi_ac)
    satis_header.addWidget(btnSatisDetay)
    satis_l.addLayout(satis_header)
    self.tblDashboardSonSatislar = _table()
    self.tblDashboardSonSatislar.setColumnCount(4)
    self.tblDashboardSonSatislar.setHorizontalHeaderLabels(["Tarih", "Cari", "Belge", "Toplam"])
    self.tblDashboardSonSatislar.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    self.tblDashboardSonSatislar.setVisible(False)
    self.lblSonSatislarOzet = _card_label("Son satışlar detay penceresinde gösterilir.", "#F8FAFC", "#E2E8F0", "#334155")
    self.lblSonSatislarOzet.setMinimumHeight(74)
    satis_l.addWidget(self.lblSonSatislarOzet)

    self.dashboardKritikKart = QFrame()
    self.dashboardKritikKart.setObjectName("MainCard")
    self.dashboardKritikKart.setMaximumHeight(150)
    kritik_l = QVBoxLayout(self.dashboardKritikKart)
    kritik_l.setContentsMargins(16, 14, 16, 14)
    kritik_l.setSpacing(9)
    kritik_header = QHBoxLayout()
    kritik_header.addWidget(_section_title("Kritik Stoklar"), 1)
    btnKritikDetay = QPushButton("Pencerede Aç")
    btnKritikDetay.setMaximumWidth(130)
    btnKritikDetay.clicked.connect(self.dashboard_kritik_stok_penceresi_ac)
    kritik_header.addWidget(btnKritikDetay)
    kritik_l.addLayout(kritik_header)
    self.tblDashboardKritikStok = _table()
    self.tblDashboardKritikStok.setColumnCount(3)
    self.tblDashboardKritikStok.setHorizontalHeaderLabels(["Ürün", "Stok", "Fiyat"])
    self.tblDashboardKritikStok.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    self.tblDashboardKritikStok.setVisible(False)
    self.lblKritikStokOzetPanel = _card_label("Kritik stok detayları ayrı pencerede gösterilir.", "#FEF2F2", "#FECACA", "#B91C1C")
    self.lblKritikStokOzetPanel.setMinimumHeight(74)
    kritik_l.addWidget(self.lblKritikStokOzetPanel)


    self.dashboardCokSatanKart = QFrame()
    self.dashboardCokSatanKart.setObjectName("MainCard")
    self.dashboardCokSatanKart.setMaximumHeight(150)
    cok_l = QVBoxLayout(self.dashboardCokSatanKart)
    cok_l.setContentsMargins(16, 14, 16, 14)
    cok_l.setSpacing(9)
    cok_header = QHBoxLayout()
    cok_header.addWidget(_section_title("En Çok Satanlar"), 1)
    btnCokSatanDetay = QPushButton("Pencerede Aç")
    btnCokSatanDetay.setMaximumWidth(130)
    btnCokSatanDetay.clicked.connect(self.dashboard_cok_satanlar_penceresi_ac)
    cok_header.addWidget(btnCokSatanDetay)
    cok_l.addLayout(cok_header)
    self.tblDashboardCokSatan = _table()
    self.tblDashboardCokSatan.setColumnCount(3)
    self.tblDashboardCokSatan.setHorizontalHeaderLabels(["Ürün", "Adet", "Toplam"])
    self.tblDashboardCokSatan.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    self.tblDashboardCokSatan.setVisible(False)
    self.lblCokSatanOzetPanel = _card_label("En çok satan ürünler detay penceresinde gösterilir.", "#F5F3FF", "#DDD6FE", "#6D28D9")
    self.lblCokSatanOzetPanel.setMinimumHeight(74)
    cok_l.addWidget(self.lblCokSatanOzetPanel)

    self.dashboardMusteriKart = QFrame()
    self.dashboardMusteriKart.setObjectName("MainCard")
    self.dashboardMusteriKart.setMaximumHeight(190)
    musteri_l = QVBoxLayout(self.dashboardMusteriKart)
    musteri_l.setContentsMargins(16, 14, 16, 14)
    musteri_l.setSpacing(9)
    musteri_header = QHBoxLayout()
    musteri_header.addWidget(_section_title("En İyi Müşteriler"), 1)
    btnMusteriGit = QPushButton("Carilere Git")
    btnMusteriGit.setMaximumWidth(110)
    btnMusteriGit.clicked.connect(lambda: self.sayfa_goster("cari"))
    musteri_header.addWidget(btnMusteriGit)
    musteri_l.addLayout(musteri_header)
    self.lblDashboardTopMusteriler = _mini_list_label("Henüz satış verisi yok")
    musteri_l.addWidget(self.lblDashboardTopMusteriler)

    # Eski fonksiyonlarla uyumluluk için bırakıldı.
    self.lblBugunSatis = _card_label("Bugün Satış\n0,00 ", "#FFFFFF", "#E2E8F0", "#0F172A")
    self.lblKritikStok = QPushButton("Kritik Stok\n0 ürün")
    self.lblKritikStok.clicked.connect(lambda: self.sayfa_goster("stok"))
    self.lblTahsilatAlarmi = _card_label("Tahsilat Alarmı\nBorçlu cari yok", "#FEF2F2", "#FECACA", "#991B1B")

    self.dashboardTopWidgets = [self.dashboardSonIslemlerKart, self.dashboardBildirimKart, self.dashboardKasaKart]
    self.dashboardBottomWidgets = [self.dashboardSatisKart, self.dashboardKritikKart, self.dashboardCokSatanKart, self.dashboardMusteriKart]

    def dashboard_reflow():
        width = _content_width(self)
        _place_grid(self.dashboardMetricGrid, self.dashboardMetricWidgets, _metric_columns(width))
        _place_grid(self.dashboardQuickGrid, self.dashboardQuickButtons, _quick_columns(width))
        while self.dashboardMainLayout.count():
            item = self.dashboardMainLayout.takeAt(0)
            if item and item.widget():
                item.widget().setParent(None)
        for c in range(3):
            self.dashboardMainLayout.setColumnStretch(c, 0)
        if width >= 1250:
            self.dashboardMainLayout.addWidget(self.dashboardSonIslemlerKart, 0, 0, 1, 2)
            self.dashboardMainLayout.addWidget(self.dashboardBildirimKart, 0, 2)
            self.dashboardMainLayout.addWidget(self.dashboardSatisKart, 1, 0)
            self.dashboardMainLayout.addWidget(self.dashboardKritikKart, 1, 1)
            self.dashboardMainLayout.addWidget(self.dashboardKasaKart, 1, 2)
            self.dashboardMainLayout.addWidget(self.dashboardCokSatanKart, 2, 0)
            self.dashboardMainLayout.addWidget(self.dashboardMusteriKart, 2, 1, 1, 2)
            self.dashboardMainLayout.setColumnStretch(0, 4)
            self.dashboardMainLayout.setColumnStretch(1, 4)
            self.dashboardMainLayout.setColumnStretch(2, 3)
        elif width >= 820:
            self.dashboardMainLayout.addWidget(self.dashboardSonIslemlerKart, 0, 0, 1, 2)
            self.dashboardMainLayout.addWidget(self.dashboardBildirimKart, 1, 0)
            self.dashboardMainLayout.addWidget(self.dashboardKasaKart, 1, 1)
            self.dashboardMainLayout.addWidget(self.dashboardSatisKart, 2, 0)
            self.dashboardMainLayout.addWidget(self.dashboardKritikKart, 2, 1)
            self.dashboardMainLayout.addWidget(self.dashboardCokSatanKart, 3, 0)
            self.dashboardMainLayout.addWidget(self.dashboardMusteriKart, 3, 1)
            self.dashboardMainLayout.setColumnStretch(0, 1)
            self.dashboardMainLayout.setColumnStretch(1, 1)
        else:
            siralama = [self.dashboardBildirimKart, self.dashboardKasaKart, self.dashboardSonIslemlerKart, self.dashboardSatisKart, self.dashboardKritikKart, self.dashboardCokSatanKart, self.dashboardMusteriKart]
            for i, widget in enumerate(siralama):
                self.dashboardMainLayout.addWidget(widget, i, 0)
            self.dashboardMainLayout.setColumnStretch(0, 1)

    self.dashboard_reflow = dashboard_reflow
    dashboard_reflow()
    content_layout.addWidget(self.dashboardMainArea, 1)

    self.lblToplamCari = QLabel("0")
    self.lblToplamBorc = self.lblDashboardBorc
    self.lblToplamTahsilat = self.lblDashboardTahsilat
    self.lblKalanBakiye = QLabel("0,00 ")
    if hasattr(self, "dashboard_kpi_font_ayarla"):
        self.dashboard_kpi_font_ayarla()

    # v119: Durum çubuğu artık ana pencere kabuğunda sabit durur.

    return page_scroll(content)

