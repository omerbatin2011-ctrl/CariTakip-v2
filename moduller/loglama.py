import json
import os
import re
import sys
import traceback
import uuid
from datetime import datetime

from core.config import BASE_DIR

LOG_KLASOR = os.path.join(BASE_DIR, "logs")
LOG_MAX_BYTES = int(os.environ.get("DAL_ERP_LOG_MAX_BYTES", str(2 * 1024 * 1024)))
LOG_BACKUP_COUNT = int(os.environ.get("DAL_ERP_LOG_BACKUP_COUNT", "5"))
ERROR_JSONL = os.path.join(LOG_KLASOR, "hata_log.jsonl")


def _log_klasoru():
    os.makedirs(LOG_KLASOR, exist_ok=True)
    return LOG_KLASOR


def _temizle(metin):
    """Loglara şifre/token/IBAN gibi hassas bilgilerin düz yazılmasını azaltır."""
    metin = str(metin or "")
    patterns = [
        (r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+", r"\1***"),
        (r"(?i)(token\s*[:=]\s*)[^\s,;]+", r"\1***"),
        (r"(?i)(sifre|şifre|password|parola)(\s*[:=]\s*)[^\s,;]+", r"\1\2***"),
        (r"(?i)(iban)(\s*[:=]\s*)[A-Z0-9 ]{12,}", r"\1\2***"),
    ]
    for pattern, repl in patterns:
        metin = re.sub(pattern, repl, metin)
    return metin


def _rotate_file(yol):
    """Log dosyası büyürse numaralı yedeğe alır; disk şişmesini önler."""
    try:
        if LOG_MAX_BYTES <= 0 or not os.path.exists(yol):
            return
        if os.path.getsize(yol) < LOG_MAX_BYTES:
            return
        for idx in range(max(LOG_BACKUP_COUNT, 1), 0, -1):
            kaynak = f"{yol}.{idx}" if idx > 1 else yol
            hedef = f"{yol}.{idx + 1}"
            if os.path.exists(kaynak):
                if idx >= LOG_BACKUP_COUNT:
                    os.remove(kaynak)
                else:
                    os.replace(kaynak, hedef)
    except Exception:
        pass


def _satir(kategori, islem):
    kategori = str(kategori or "GENEL").upper().strip()
    return f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')} | {kategori:<10} | {_temizle(islem)}\n"


def log_yaz(islem, kategori="GENEL"):
    """Geriye uyumlu genel log. v76 ile kategori desteği eklendi."""
    try:
        klasor = _log_klasoru()
        now = datetime.now()
        satir = _satir(kategori, islem)
        yollar = [
            os.path.join(klasor, "islem_logu.txt"),
            os.path.join(klasor, f"islem_logu_{now.strftime('%Y-%m')}.txt"),
        ]
        for yol in yollar:
            _rotate_file(yol)
            with open(yol, "a", encoding="utf-8") as f:
                f.write(satir)
    except Exception:
        pass


def giris_log_yaz(kullanici, basarili=True):
    log_yaz(f"Kullanıcı girişi {'başarılı' if basarili else 'başarısız'}: {kullanici}", "GIRIS")


def satis_log_yaz(mesaj):
    log_yaz(mesaj, "SATIS")


def tahsilat_log_yaz(mesaj):
    log_yaz(mesaj, "TAHSILAT")


def stok_log_yaz(mesaj):
    log_yaz(mesaj, "STOK")



def hata_kodu_uret() -> str:
    """Kullanıcıya gösterilebilecek kısa hata takip kodu üretir."""
    return datetime.now().strftime("E%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6].upper()


def hata_json_yaz(kod: str, baslik: str, hata_tipi: str, mesaj: str, traceback_metin: str = "") -> None:
    """Makine tarafından okunabilir hata kaydı oluşturur.

    TXT log kullanıcı/teknik destek için okunabilir kalır; JSONL log ise ileride
    hata analiz araçlarıyla kolayca işlenebilir. Hassas alanlar yazmadan önce
    maskelenir.
    """
    try:
        klasor = _log_klasoru()
        yol = os.path.join(klasor, "hata_log.jsonl")
        _rotate_file(yol)
        kayit = {
            "zaman": datetime.now().isoformat(timespec="seconds"),
            "kod": kod,
            "baslik": _temizle(baslik),
            "hata_tipi": _temizle(hata_tipi),
            "mesaj": _temizle(mesaj),
            "traceback": _temizle(traceback_metin),
        }
        with open(yol, "a", encoding="utf-8") as f:
            f.write(json.dumps(kayit, ensure_ascii=False) + "\n")
    except Exception:
        pass

def hata_yaz(hata):
    try:
        klasor = _log_klasoru()
        hata_yolu = os.path.join(klasor, "hata_log.txt")
        _rotate_file(hata_yolu)
        with open(hata_yolu, "a", encoding="utf-8") as f:
            f.write(f"\n--- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            f.write(_temizle(str(hata)))
            f.write("\n")
    except Exception:
        pass


def hata_trace_yaz(exc_type, exc_value, exc_traceback):
    kod = hata_kodu_uret()
    try:
        klasor = _log_klasoru()
        hata_yolu = os.path.join(klasor, "hata_log.txt")
        _rotate_file(hata_yolu)
        trace = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        with open(hata_yolu, "a", encoding="utf-8") as f:
            f.write(f"\n--- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {kod} ---\n")
            f.write(_temizle(trace))
        hata_json_yaz(kod, "Beklenmeyen hata", getattr(exc_type, "__name__", str(exc_type)), str(exc_value), trace)
    except Exception:
        pass
    return kod


def hata_yakalayici(exc_type, exc_value, exc_traceback):
    """Yakalanamayan hataları loglar ve programın sessizce kapanmasını önler."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    kod = hata_trace_yaz(exc_type, exc_value, exc_traceback)
    try:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(
            None,
            "Beklenmeyen Hata",
            "Program beklenmeyen bir hata yakaladı. "
            f"Takip kodu: {kod}\nDetaylar logs/hata_log.txt dosyasına kaydedildi.",
        )
    except Exception:
        try:
            print("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        except Exception:
            pass
