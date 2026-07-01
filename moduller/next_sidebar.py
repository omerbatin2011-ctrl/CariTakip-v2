from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from moduller.yetki import yetki_var_mi

NEXT_NAV_GROUPS = [
    ("Kontrol", [("🏠  Dashboard", "dashboard")]),
    ("Ticari", [
        ("👥  Cariler", "cari"),
        ("📦  Ürünler / Stok", "stok"),
        ("🧾  Satışlar", "satis"),
        ("▥  Barkodlu Satış", "barkotlu_satis"),
        ("₺  Tahsilatlar", "tahsilat"),
        ("💰  Kasa", "kasa"),
    ]),
    ("Operasyon", [
        ("▤  Teklifler", "teklifler"),
        ("↧  Ürün Alışları", "alis"),
        ("▤  Siparişler", "siparis"),
        ("↧  Satın Alma", "satin_alma"),
    ]),
    ("Analiz", [
        ("📊  Raporlar", "raporlar"),
        ("⌁  Kâr / Zarar", "kar_zarar"),
        ("●  Bildirimler", "bildirimler"),
    ]),
    ("Sistem", [
        ("⚙  Ayarlar", "ayarlar"),
        ("◒  Yedekleme", "yedekleme"),
    ]),
]


def _sidebar_button(text, slot=None, active=False):
    button = QPushButton(text)
    button.setObjectName("SidebarActive" if active else "SidebarButton")
    button.setMinimumHeight(40)
    button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    button.setCursor(Qt.PointingHandCursor)
    if slot:
        button.clicked.connect(slot)
    return button


def build_next_sidebar(owner):
    """v120 DAL ERP Next: modern, daralabilir, modüler sol menü."""
    sidebar = QFrame()
    sidebar.setObjectName("Sidebar")
    owner.sidebar = sidebar
    owner.sidebar_collapsed = False
    sidebar.setMinimumWidth(248)
    sidebar.setMaximumWidth(268)

    sidebar_layout = QVBoxLayout(sidebar)
    sidebar_layout.setContentsMargins(10, 10, 10, 10)
    sidebar_layout.setSpacing(8)

    # V152: Görsel olarak kullanılmayan hamburger buton kaldırıldı.
    # Küçük ekranlarda otomatik daraltma altyapısı bozulmasın diye alan adı korunur.
    owner.btnSidebarToggle = None

    brand = QFrame()
    brand.setObjectName("SidebarBrand")
    brand_layout = QHBoxLayout(brand)
    brand_layout.setContentsMargins(10, 8, 10, 8)
    brand_layout.setSpacing(12)

    owner.lblSidebarLogo = QLabel("D")
    owner.lblSidebarLogo.setObjectName("SidebarLogo")
    owner.lblSidebarLogo.setAlignment(Qt.AlignCenter)
    owner.lblSidebarLogo.setFixedSize(40, 40)

    brand_text = QVBoxLayout()
    brand_text.setContentsMargins(0, 0, 0, 0)
    brand_text.setSpacing(0)
    owner.lblFirmaAdi = QLabel("DAL ERP Next")
    owner.lblFirmaAdi.setObjectName("SidebarBrandTitle")
    owner.lblFirmaAdi.setWordWrap(False)
    owner.lblFirmaAltSidebar = QLabel("Professional")
    owner.lblFirmaAltSidebar.setObjectName("SidebarBrandSubtitle")
    owner.lblFirmaAltSidebar.setWordWrap(False)
    brand_text.addWidget(owner.lblFirmaAdi)
    brand_text.addWidget(owner.lblFirmaAltSidebar)

    brand_layout.addWidget(owner.lblSidebarLogo)
    brand_layout.addLayout(brand_text, 1)
    sidebar_layout.addWidget(brand)

    nav_scroll = QScrollArea()
    nav_scroll.setObjectName("SidebarNavScroll")
    nav_scroll.setWidgetResizable(True)
    nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    nav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    nav_scroll.setFrameShape(QFrame.NoFrame)

    nav_container = QWidget()
    nav_container.setObjectName("SidebarNavContainer")
    nav_layout = QVBoxLayout(nav_container)
    nav_layout.setContentsMargins(0, 2, 0, 0)
    nav_layout.setSpacing(4)

    owner.sidebar_butonlari = []
    owner.sidebar_grup_basliklari = []
    ilk_sayfa = None

    for group_name, items in NEXT_NAV_GROUPS:
        allowed_items = [(text, page) for text, page in items if yetki_var_mi(page, "goruntule", owner.aktif_kullanici)]
        if not allowed_items:
            continue
        group_label = QLabel(group_name.upper())
        group_label.setObjectName("SidebarGroupTitle")
        group_label.setProperty("full_text", group_name.upper())
        owner.sidebar_grup_basliklari.append(group_label)
        nav_layout.addWidget(group_label)
        for text, page in allowed_items:
            if ilk_sayfa is None:
                ilk_sayfa = page
            btn = _sidebar_button(text, lambda checked=False, p=page: owner.sayfa_goster(p), active=(page == ilk_sayfa))
            btn.setProperty("full_text", text)
            btn.setToolTip("")
            owner.sidebar_butonlari.append((btn, page))
            nav_layout.addWidget(btn)
        nav_layout.addSpacing(6)

    nav_layout.addStretch()
    nav_scroll.setWidget(nav_container)
    sidebar_layout.addWidget(nav_scroll, 1)

    owner.lblSidebarFooter = QLabel("SQLite bağlı  •  v152")
    owner.lblSidebarFooter.setObjectName("SidebarFooter")
    owner.lblSidebarFooter.setAlignment(Qt.AlignCenter)
    sidebar_layout.addWidget(owner.lblSidebarFooter)

    owner.btnYardim = _sidebar_button("?  Yardım", lambda: QMessageBox.information(owner, "Yardım", "DAL ERP Next sol menüden modüller arasında tek pencerede geçiş yapar."))
    sidebar_layout.addWidget(owner.btnYardim)

    owner.btnCikis = QPushButton("←  Çıkış")
    owner.btnCikis.setObjectName("ExitButton")
    owner.btnCikis.setProperty("full_text", "←  Çıkış")
    owner.btnCikis.setCursor(Qt.PointingHandCursor)
    owner.btnCikis.clicked.connect(owner.close)
    sidebar_layout.addWidget(owner.btnCikis)

    owner.ilk_sayfa = ilk_sayfa or "dashboard"
    return sidebar
