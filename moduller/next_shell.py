from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from moduller.erp_utils import turkce_tarih_yazi

PAGE_TITLES = {
    'dashboard': 'Dashboard',
    'cari': 'Cari Kartları',
    'stok': 'Ürünler / Stok',
    'tahsilat': 'Tahsilatlar',
    'raporlar': 'Genel Raporlar',
    'satis': 'Satışlar',
    'barkotlu_satis': 'Barkodlu Satış',
    'kasa': 'Kasa',
    'teklifler': 'Teklifler',
    'alis': 'Ürün Alışları',
    'siparis': 'Siparişler',
    'satin_alma': 'Satın Alma',
    'kar_zarar': 'Kâr / Zarar',
    'bildirimler': 'Bildirimler',
    'ayarlar': 'Ayarlar',
    'yedekleme': 'Yedekleme',
}


def build_next_topbar(owner):
    """v119 DAL ERP Next: tüm sayfalarda görünen modern üst bar."""
    topbar = QFrame()
    topbar.setObjectName('NextTopBar')
    topbar.setMinimumHeight(58)
    layout = QHBoxLayout(topbar)
    layout.setContentsMargins(14, 6, 14, 6)
    layout.setSpacing(8)

    title_box = QVBoxLayout()
    title_box.setSpacing(1)
    owner.lblDashboardBaslik = QLabel('Dashboard')
    owner.lblDashboardBaslik.setObjectName('NextPageTitle')
    firma_adi = ''
    try:
        firma_adi = owner.firma.get('firma_adi', '') if isinstance(owner.firma, dict) else ''
    except Exception:
        firma_adi = ''
    owner.lblFirmaAltBilgi = QLabel(f"{firma_adi or 'DAL ERP Professional'}    •    {turkce_tarih_yazi()}")
    owner.lblFirmaAltBilgi.setObjectName('NextPageSubtitle')
    title_box.addWidget(owner.lblDashboardBaslik)
    title_box.addWidget(owner.lblFirmaAltBilgi)
    layout.addLayout(title_box, 1)

    owner.txtGlobalArama = QLineEdit()
    owner.txtGlobalArama.setObjectName('GlobalSearch')
    owner.txtGlobalArama.setPlaceholderText('Cari / ürün ara...        Ctrl + K')
    owner.txtGlobalArama.setMinimumWidth(210)
    owner.txtGlobalArama.setMaximumWidth(320)
    try:
        owner.txtGlobalArama.returnPressed.connect(owner.global_arama_yap)
    except Exception:
        pass
    layout.addWidget(owner.txtGlobalArama)

    owner.btnTemaToggle = QPushButton('🌙')
    owner.btnTemaToggle.setObjectName('ThemeToggleButton')
    owner.btnTemaToggle.setMinimumHeight(42)
    owner.btnTemaToggle.setMaximumWidth(58)
    owner.btnTemaToggle.setToolTip('Tema değiştir')
    try:
        owner.btnTemaToggle.clicked.connect(owner.tema_toggle)
    except Exception:
        pass
    layout.addWidget(owner.btnTemaToggle)

    owner.lblNextUser = QLabel('👤')
    owner.lblNextUser.setObjectName('NextUserBadge')
    owner.lblNextUser.setAlignment(Qt.AlignCenter)
    owner.lblNextUser.setMinimumWidth(50)
    owner.lblNextUser.setToolTip('Aktif kullanıcı: Admin')
    layout.addWidget(owner.lblNextUser)
    return topbar


def build_next_statusbar(owner):
    """v119: tüm sayfalarda görünen tek durum çubuğu."""
    status = QFrame()
    status.setObjectName('NextStatusBar')
    status.setMinimumHeight(28)
    layout = QHBoxLayout(status)
    layout.setContentsMargins(18, 2, 18, 4)
    owner.lblDurumCubugu = QLabel('DAL ERP Next v140    Tema: Açık Tema    Veritabanı: Bağlı    Son yedek: kontrol ediliyor    Kullanıcı: admin')
    owner.lblDurumCubugu.setObjectName('NextStatusLabel')
    layout.addWidget(owner.lblDurumCubugu, 1)
    return status


def set_page_title(owner, page_name):
    """Aktif sayfa başlığını merkezi üst barda günceller."""
    try:
        title = PAGE_TITLES.get(page_name, 'DAL ERP Next')
        owner.lblDashboardBaslik.setText(title)
    except Exception:
        pass
