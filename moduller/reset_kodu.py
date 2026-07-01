"""Seri numarasına özel, süreli şifre sıfırlama kodu sistemi.

Kod mantığı:
- Kod müşteri seri numarası + zaman dilimi + gizli anahtar ile HMAC-SHA256 üzerinden üretilir.
- Varsayılan geçerlilik 15 dakikadır.
- Doğrulamada saat kaymasına karşı bir önceki ve bir sonraki zaman dilimi de kabul edilir.
- Kullanılan kodlar veritabanına kaydedilir ve tekrar kullanılamaz.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import time
from datetime import datetime

from core.config import PROGRAM_SERI_NO, RESET_KODU_GECERLILIK_DAKIKA, YETKILI_RESET_SERI_NO

from .db import db_baglan
from .loglama import log_yaz

# Bu anahtar her kurulum ailesi için aynıdır; farklı müşterilere farklı dağıtım yapacaksanız değiştirilebilir.
# Not: Python masaüstü uygulamalarında gizli anahtar tamamen saklanamaz; EXE paketleme sadece tersine mühendisliği zorlaştırır.
_RESET_SECRET = os.environ.get(
    "DAL_ERP_RESET_SECRET",
    "DAL-ERP-2026-RESET-v1::cari-takip::degistirilebilir-gizli-anahtar"
).encode("utf-8")


def seri_no_temizle(seri_no: str) -> str:
    """Seri numarasını yalnızca harf/rakam kalacak şekilde normalize eder."""
    seri = re.sub(r"[^0-9A-Za-z]", "", str(seri_no or "")).upper()
    if not seri or len(seri) < 4 or len(seri) > 32:
        raise ValueError("Seri numarası 4-32 karakter arasında olmalıdır.")
    return seri


def reset_kodu_tablosu_olustur() -> None:
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reset_kodu_kullanimlari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seri_no TEXT NOT NULL,
                kod TEXT NOT NULL,
                kullanildi_tarih TEXT NOT NULL,
                UNIQUE(seri_no, kod)
            )
        """)


def _zaman_dilimi(ts: int | None = None) -> int:
    dakika = max(1, int(RESET_KODU_GECERLILIK_DAKIKA or 15))
    return int((ts or int(time.time())) // (dakika * 60))


def _kod_uret(seri_no: str, dilim: int) -> str:
    veri = f"{seri_no}|{dilim}|DAL_ERP_RESET".encode()
    digest = hmac.new(_RESET_SECRET, veri, hashlib.sha256).digest()
    kod = base64.b32encode(digest).decode("ascii").rstrip("=")[:8]
    return f"{kod[:4]}-{kod[4:]}"


def reset_kodu_uret(hedef_seri_no: str) -> str:
    """Yetkili programın müşteriye vereceği süreli reset kodunu üretir."""
    seri = seri_no_temizle(hedef_seri_no)
    return _kod_uret(seri, _zaman_dilimi())


def reset_kodu_kullanildi_mi(seri_no: str, kod: str) -> bool:
    reset_kodu_tablosu_olustur()
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM reset_kodu_kullanimlari WHERE seri_no=? AND kod=? LIMIT 1",
            (seri_no, kod),
        )
        return cur.fetchone() is not None


def reset_kodu_kullanildi_isaretle(seri_no: str, kod: str) -> None:
    reset_kodu_tablosu_olustur()
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO reset_kodu_kullanimlari(seri_no, kod, kullanildi_tarih) VALUES (?, ?, ?)",
            (seri_no, kod, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )


def reset_kodu_dogrula(girilen_kod: str, seri_no: str | None = None, tuket: bool = True) -> tuple[bool, str]:
    """Müşteri programında girilen kodu doğrular."""
    try:
        seri = seri_no_temizle(seri_no or PROGRAM_SERI_NO)
    except ValueError as hata:
        return False, str(hata)
    kod = str(girilen_kod or "").strip().upper().replace(" ", "")
    if not re.fullmatch(r"[A-Z2-7]{4}-?[A-Z2-7]{4}", kod):
        return False, "Reset kodu biçimi geçersiz. Örnek: ABCD-1234"
    if "-" not in kod:
        kod = f"{kod[:4]}-{kod[4:]}"
    if reset_kodu_kullanildi_mi(seri, kod):
        return False, "Bu reset kodu daha önce kullanılmış."

    simdiki = _zaman_dilimi()
    gecerli_kodlar = {_kod_uret(seri, simdiki + kayma) for kayma in (-1, 0, 1)}
    if not hmac.compare_digest(kod, kod) or kod not in gecerli_kodlar:
        return False, f"Reset kodu geçersiz veya süresi dolmuş. Kodlar yaklaşık {RESET_KODU_GECERLILIK_DAKIKA} dakika geçerlidir."
    if tuket:
        reset_kodu_kullanildi_isaretle(seri, kod)
        log_yaz(f"Seri numarası reset kodu ile kullanıcı şifresi sıfırlama yetkisi verildi: {seri}")
    return True, "Reset kodu doğrulandı."


def mevcut_program_seri_no() -> str:
    return seri_no_temizle(PROGRAM_SERI_NO)


def yetkili_program_mi() -> bool:
    try:
        return mevcut_program_seri_no() == seri_no_temizle(YETKILI_RESET_SERI_NO)
    except Exception:
        return False
