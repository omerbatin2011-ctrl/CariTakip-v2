"""DAL ERP Next uygulama başlatma katmanı.

main.py dosyasını sade tutmak için veritabanı, güvenlik,
bakım ve Qt başlatma işlemleri burada toplanır.
"""

from __future__ import annotations

import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from core.config import DB_ADI
from moduller.app_guardian import global_hata_yakalayici, korumayi_baslat
from moduller.db import (
    db_ayarla,
    urun_tablolari_olustur,
    veritabani_indeksleri_olustur,
    veritabani_olustur,
)
from moduller.erp_ek_moduller import erp_migrasyonlarini_uygula
from moduller.giris_ui import giris_penceresi
from moduller.kasa_ui import kasa_tablosu_olustur
from moduller.loglama import log_yaz
from moduller.reset_kodu import reset_kodu_tablosu_olustur
from moduller.runtime_health import calisma_ortami_saglik_kontrolu
from moduller.sistem import (
    ana_sifreyi_istenen_degere_ayarla,
    ayarlar_tablosu_olustur,
    dosya_izinlerini_sikilastir,
    guvenlik_ayarlarini_olustur,
    guvenlik_migrasyonunu_uygula,
    guvenlik_tablosu_olustur,
    kullanici_tablosu_olustur,
    otomatik_gunluk_yedek_olustur,
)
from moduller.veritabani_bakim import (
    eski_yedekleri_temizle,
    kritik_indeksleri_olustur,
    veritabani_butunluk_kontrolu,
)
from moduller.yetki import yetki_tablolari_olustur


def qt_olceklendirmeyi_ayarla() -> None:
    """Yüksek DPI ekranlarda Qt ölçeklendirmesini güvenli şekilde ayarlar."""
    try:
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except Exception:
        pass


def veritabani_ve_sistemi_hazirla() -> None:
    """Veritabanı, güvenlik, migrasyon ve bakım hazırlıklarını çalıştırır."""
    db_ayarla(DB_ADI)
    veritabani_olustur()
    urun_tablolari_olustur()
    ayarlar_tablosu_olustur()
    kullanici_tablosu_olustur()
    yetki_tablolari_olustur()
    guvenlik_tablosu_olustur()
    guvenlik_ayarlarini_olustur()
    reset_kodu_tablosu_olustur()
    kasa_tablosu_olustur()
    erp_migrasyonlarini_uygula()

    # Kurulum/onarım dışında ana şifreyi her açılışta zorla değiştirme.
    if os.environ.get("DAL_ERP_DEFAULT_MASTER_PASSWORD"):
        ana_sifreyi_istenen_degere_ayarla()

    veritabani_indeksleri_olustur()
    kritik_indeksleri_olustur()
    guvenlik_migrasyonunu_uygula()

    calisma_ortami_saglik_kontrolu(log_yaz, DB_ADI)

    ok_db, db_mesaj = veritabani_butunluk_kontrolu()
    if not ok_db:
        log_yaz(f"Veritabanı bütünlük uyarısı: {db_mesaj}", "DB")

    otomatik_gunluk_yedek_olustur()
    eski_yedekleri_temizle(gun=30)
    dosya_izinlerini_sikilastir()
    korumayi_baslat()


def run_app() -> int:
    """DAL ERP Next uygulamasını başlatır ve Qt çıkış kodunu döndürür."""
    qt_olceklendirmeyi_ayarla()

    app = QApplication(sys.argv)
    sys.excepthook = global_hata_yakalayici

    veritabani_ve_sistemi_hazirla()

    if not giris_penceresi():
        return 0

    # Mobil bağlantı altyapısı: masaüstü program açıkken aynı Wi-Fi içindeki telefonlar
    # REST API üzerinden dashboard/cari/tahsilat verilerine erişebilir.
    try:
        from api.launcher import api_baslat
        api_baslat(log_yaz)
    except Exception as exc:
        log_yaz(f"Mobil API başlatma uyarısı: {exc}", "API")

    # Ağır ana pencere modülleri login sonrası yüklenir.
    # Böylece release_check ve giriş ekranı daha hızlı açılır.
    from moduller.ana_pencere import AnaPencere

    pencere = AnaPencere()
    pencere.show()
    return app.exec()
