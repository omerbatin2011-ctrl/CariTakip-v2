"""Uygulama kararlılığı ve yerel güvenlik koruma katmanı."""
import os
import sqlite3
import sys
import traceback
from datetime import datetime

try:
    from PySide6.QtWidgets import QMessageBox
except Exception:  # GUI yüklenmeden de import edilebilsin
    QMessageBox = None

from core.config import BASE_DIR

from . import db as db_modulu
from .loglama import hata_trace_yaz, hata_yaz, log_yaz


def _logs_dir():
    yol = os.path.join(BASE_DIR, "logs")
    os.makedirs(yol, exist_ok=True)
    return yol


def guvenli_hata_kaydet(baslik, hata):
    """Hassas veri sızdırmadan hata kaydı oluşturur ve takip kodu döndürür."""
    try:
        _logs_dir()
        from .loglama import hata_json_yaz, hata_kodu_uret

        kod = hata_kodu_uret()
        mesaj = f"{baslik}: {type(hata).__name__}: {hata}"
        hata_yaz(f"{kod} | {mesaj}")
        hata_json_yaz(kod, baslik, type(hata).__name__, str(hata))
        return kod
    except Exception:
        return "LOG-YOK"


def kullaniciya_hata_goster(baslik="İşlem Tamamlanamadı", mesaj=None, kod=None):
    if QMessageBox is None:
        return
    try:
        metin = mesaj or "İşlem sırasında bir hata oluştu. Detaylar logs/hata_log.txt dosyasına kaydedildi."
        if kod:
            metin = f"{metin}\n\nTakip kodu: {kod}"
        QMessageBox.warning(None, baslik, metin)
    except Exception:
        pass


def global_hata_yakalayici(exc_type, exc_value, exc_traceback):
    """Yakalanamayan hataları loglar; sessiz kapanmayı engeller."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    kod = None
    try:
        kod = hata_trace_yaz(exc_type, exc_value, exc_traceback)
    except Exception:
        try:
            print("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        except Exception:
            pass
    kullaniciya_hata_goster(
        "Beklenmeyen Hata",
        "Program beklenmeyen bir hata yakaladı ve kayıt altına aldı. "
        "Detaylar logs/hata_log.txt dosyasındadır.",
        kod=kod,
    )


def veritabani_saglik_kontrolu():
    """SQLite bütünlük kontrolü yapar. Bozuk DB tespit edilirse False döner."""
    db_yolu = db_modulu.DB_ADI
    if not db_yolu or not os.path.exists(db_yolu):
        return False, "Veritabanı dosyası bulunamadı."
    try:
        conn = sqlite3.connect(db_yolu, timeout=10)
        try:
            sonuc = conn.execute("PRAGMA integrity_check").fetchone()
            fk_hatalari = conn.execute("PRAGMA foreign_key_check").fetchall()
        finally:
            conn.close()
        if fk_hatalari:
            return False, f"Yabancı anahtar hatası sayısı: {len(fk_hatalari)}"
        if not sonuc or str(sonuc[0]).lower() != "ok":
            return False, f"Veritabanı bütünlük hatası: {sonuc[0] if sonuc else 'bilinmiyor'}"
        return True, "OK"
    except Exception as hata:
        guvenli_hata_kaydet("Veritabanı sağlık kontrolü hatası", hata)
        return False, str(hata)


def acilis_kurtarma_yedegi():
    """Program açılışında günlük güvenli yedek oluşturur."""
    try:
        db_yolu = db_modulu.DB_ADI
        if not db_yolu or not os.path.exists(db_yolu):
            return None
        hedef_klasor = os.path.join(BASE_DIR, "yedekler", "kurtarma")
        os.makedirs(hedef_klasor, exist_ok=True)
        gun = datetime.now().strftime("%Y-%m-%d")
        her_acilista_yedek = os.environ.get("DAL_ERP_HER_ACILISTA_YEDEK", "0").strip().lower()
        if her_acilista_yedek not in {"1", "true", "evet", "yes", "on"}:
            mevcut = [
                ad
                for ad in os.listdir(hedef_klasor)
                if ad.startswith(f"acilis_kurtarma_{gun}") and ad.lower().endswith(".db")
            ]
            if mevcut:
                return os.path.join(hedef_klasor, sorted(mevcut)[-1])

        try:
            from .veritabani_bakim import guvenli_sqlite_yedekle

            hedef = guvenli_sqlite_yedekle(hedef_klasor, "acilis_kurtarma")
        except Exception:
            tarih = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            hedef = os.path.join(hedef_klasor, f"acilis_kurtarma_{tarih}.db")
            kaynak = sqlite3.connect(db_yolu)
            yedek = sqlite3.connect(hedef)
            try:
                kaynak.backup(yedek)
                yedek.commit()
            finally:
                yedek.close()
                kaynak.close()
        if hedef:
            log_yaz(f"Açılış kurtarma yedeği oluşturuldu: {os.path.basename(hedef)}")
        return hedef
    except Exception as hata:
        guvenli_hata_kaydet("Açılış kurtarma yedeği hatası", hata)
        return None


def eski_yedekleri_temizle(maksimum=30):
    """Yedek klasörünün kontrolsüz büyümesini önler."""
    try:
        kok = os.path.join(BASE_DIR, "yedekler", "kurtarma")
        if not os.path.isdir(kok):
            return
        dosyalar = [os.path.join(kok, x) for x in os.listdir(kok) if x.lower().endswith(".db")]
        dosyalar.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        for silinecek in dosyalar[int(maksimum):]:
            try:
                os.remove(silinecek)
            except Exception:
                pass
    except Exception as hata:
        guvenli_hata_kaydet("Yedek temizleme hatası", hata)


def korumayi_baslat():
    """Ana programdan tek çağrı ile temel korumaları etkinleştirir."""
    sys.excepthook = global_hata_yakalayici
    _logs_dir()
    acilis_kurtarma_yedegi()
    eski_yedekleri_temizle()
    saglam, mesaj = veritabani_saglik_kontrolu()
    if not saglam:
        log_yaz(f"Veritabanı sağlık uyarısı: {mesaj}")
    return saglam
