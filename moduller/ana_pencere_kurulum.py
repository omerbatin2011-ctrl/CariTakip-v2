"""AnaPencere kurulum ve sayfa kayıt işlemleri.

v134 ile AnaPencere sınıfının __init__ gövdesi buraya taşındı.
Amaç: ana pencere sınıfını koordinatör haline getirmek ve sayfa/shell
kurulumunu ayrı, test edilebilir fonksiyonlara bölmek.
"""

from __future__ import annotations

import time

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QStackedWidget, QVBoxLayout

from core.config import OTURUM_KONTROL_MS
from moduller.db import urun_tablolari_olustur, veritabani_indeksleri_olustur
from moduller.next_shell import build_next_statusbar, build_next_topbar, set_page_title
from moduller.next_sidebar import build_next_sidebar
from moduller.sistem import firma_bilgisi_getir
from moduller.ui_theme import apply_theme
from moduller.yetki import aktif_kullanici_getir
from pages.dashboard.dashboard_page import build_dashboard

SAYFA_SIRASI = (
    "dashboard",
    "cari",
    "stok",
    "tahsilat",
    "raporlar",
    "satis",
    "barkotlu_satis",
    "kasa",
    "teklifler",
    "alis",
    "siparis",
    "satin_alma",
    "kar_zarar",
    "bildirimler",
    "ayarlar",
    "yedekleme",
)


def pencere_boyutlarini_ayarla(pencere) -> None:
    """Ana pencerenin responsive başlangıç boyutlarını ayarlar."""
    pencere.setWindowTitle("DAL ERP Next v152 Professional")
    pencere.setWindowFlags(Qt.Window)
    try:
        ekran = QApplication.primaryScreen().availableGeometry()
        genislik = max(1180, int(ekran.width() * 0.94))
        yukseklik = max(720, int(ekran.height() * 0.90))
        pencere.resize(genislik, yukseklik)
    except Exception:
        pencere.resize(1280, 760)
    pencere.setMinimumSize(900, 600)


def tema_ve_firma_bilgilerini_yukle(pencere) -> None:
    """Tema, firma ve aktif kullanıcı başlangıç değerlerini yükler."""
    pencere.aktif_kullanici = aktif_kullanici_getir()
    pencere._arka_plan_isleri = []
    pencere.koyu_tema_aktif = bool(
        QSettings("DAL", "DAL ERP").value("tema/koyu", False, type=bool)
    )
    apply_theme(pencere, pencere.koyu_tema_aktif)
    pencere.firma = firma_bilgisi_getir()


def sayfalari_olustur(pencere) -> dict:
    """Ana ekranda kullanılacak sayfaları oluşturur.

    v147 performans: Açılışta bütün modülleri tek tek üretmek programı
    belirgin yavaşlatıyordu. Artık sadece dashboard hemen kurulur; diğer
    sayfalar ilk tıklamada tembel/lazy olarak oluşturulur ve sonra cache'ten
    kullanılır.
    """
    dashboard = build_dashboard(pencere)
    pencere.tema_degistir(pencere.koyu_tema_aktif)

    pencere.sayfa_fabrikalari = {
        "cari": pencere.cari_sayfasi_olustur,
        "stok": pencere.stok_sayfasi_olustur,
        "tahsilat": pencere.tahsilat_sayfasi_olustur,
        "raporlar": pencere.raporlar_sayfasi_olustur,
        "satis": lambda: pencere.urun_satis_penceresi(embedded=True),
        "barkotlu_satis": pencere.barkotlu_satis_sayfasi_olustur,
        "kasa": pencere.kasa_sayfasi_olustur,
        "teklifler": pencere.teklifler_sayfasi_olustur,
        "alis": pencere.alis_sayfasi_olustur,
        "siparis": pencere.siparis_sayfasi_olustur,
        "satin_alma": pencere.satin_alma_sayfasi_olustur,
        "kar_zarar": pencere.kar_zarar_sayfasi_olustur,
        "bildirimler": pencere.bildirim_sayfasi_olustur,
        "ayarlar": lambda: pencere.firma_ayarlari_penceresi(embedded=True),
        "yedekleme": lambda: pencere.bulut_yedekleme_penceresi(embedded=True),
    }
    return {"dashboard": dashboard}


def _bos_sayfa_olustur(sayfa_adi: str) -> QFrame:
    panel = QFrame()
    panel.setObjectName(f"LazyPage_{sayfa_adi}")
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(24, 24, 24, 24)
    lbl = QLabel("Sayfa hazırlanıyor...")
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet("font-size:18px;font-weight:800;color:#64748B;")
    layout.addWidget(lbl, 1)
    return panel


def stack_olustur(pencere) -> QStackedWidget:
    """Sayfa kayıtlarını QStackedWidget içine alır."""
    stack = QStackedWidget()
    pencere.sayfalar = sayfalari_olustur(pencere)
    for sayfa_adi in SAYFA_SIRASI:
        if sayfa_adi not in pencere.sayfalar:
            pencere.sayfalar[sayfa_adi] = _bos_sayfa_olustur(sayfa_adi)
        stack.addWidget(pencere.sayfalar[sayfa_adi])
    if hasattr(pencere, "ilk_sayfa") and pencere.ilk_sayfa in pencere.sayfalar:
        stack.setCurrentWidget(pencere.sayfalar[pencere.ilk_sayfa])
    return stack


def shell_olustur(pencere, sidebar, stack) -> QFrame:
    """Üst bar, sayfa alanı ve durum çubuğunu tek shell içinde toplar."""
    pencere.next_topbar = build_next_topbar(pencere)
    pencere.next_statusbar = build_next_statusbar(pencere)

    content_shell = QFrame()
    content_shell.setObjectName("NextContentShell")
    pencere.content_shell_layout = QVBoxLayout(content_shell)
    pencere.content_shell_layout.setContentsMargins(0, 0, 0, 0)
    pencere.content_shell_layout.setSpacing(0)
    pencere.content_shell_layout.addWidget(pencere.next_topbar)
    pencere.content_shell_layout.addWidget(stack, 1)
    pencere.content_shell_layout.addWidget(pencere.next_statusbar)
    return content_shell


def ana_layout_olustur(pencere) -> None:
    """Sidebar + içerik shell ana yerleşimini oluşturur."""
    pencere.ana_layout = QHBoxLayout()
    pencere.ana_layout.setContentsMargins(0, 0, 0, 0)
    pencere.ana_layout.setSpacing(0)

    sidebar = build_next_sidebar(pencere)
    pencere.stack = stack_olustur(pencere)
    pencere.content_shell = shell_olustur(pencere, sidebar, pencere.stack)

    pencere.ana_layout.addWidget(sidebar)
    pencere.ana_layout.addWidget(pencere.content_shell, 1)
    pencere.setLayout(pencere.ana_layout)
    set_page_title(pencere, getattr(pencere, "ilk_sayfa", "dashboard"))


def performans_baslangic_islerini_planla(pencere) -> None:
    """Ağır DB indeks/migrasyon işlerini pencere açıldıktan sonra çalıştırır."""
    def _calistir():
        try:
            veritabani_indeksleri_olustur()
            urun_tablolari_olustur()
        except Exception:
            pass
    QTimer.singleShot(1200, _calistir)


def dashboard_ve_durum_bilgilerini_yukle(pencere) -> None:
    """İlk açılışta görünen özet ve durum bilgilerini yükler.

    v147 performans: Ağır dashboard sorguları pencere göründükten hemen sonra
    çalışır. Böylece açılış ekranı daha hızlı kapanır ve kullanıcı ana ekranı
    daha erken görür.
    """
    pencere.durum_cubugu_guncelle()

    def _gecikmeli_dashboard_yukle():
        try:
            pencere.ozet_yukle()
            pencere.dashboard_ek_bilgileri_yukle(force=True)
            pencere.durum_cubugu_guncelle()
            if hasattr(pencere, "satis_grafik_guncelle"):
                QTimer.singleShot(1600, pencere.satis_grafik_guncelle)
        except Exception:
            pass

    QTimer.singleShot(350, _gecikmeli_dashboard_yukle)


def oturum_takibini_baslat(pencere) -> None:
    """Oturum zaman aşımı takibini başlatır."""
    pencere.son_aktivite_zamani = time.time()
    pencere.oturum_kilitli = False
    pencere.oturum_timer = QTimer(pencere)
    pencere.oturum_timer.timeout.connect(pencere.oturum_zaman_asimi_kontrol)
    pencere.oturum_timer.start(OTURUM_KONTROL_MS)
    QApplication.instance().installEventFilter(pencere)


def ana_pencereyi_kur(pencere) -> None:
    """AnaPencere için tüm kurulum adımlarını sırayla çalıştırır."""
    tema_ve_firma_bilgilerini_yukle(pencere)
    pencere_boyutlarini_ayarla(pencere)
    ana_layout_olustur(pencere)
    performans_baslangic_islerini_planla(pencere)
    dashboard_ve_durum_bilgilerini_yukle(pencere)
    oturum_takibini_baslat(pencere)
