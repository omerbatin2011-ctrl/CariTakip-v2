from __future__ import annotations

import hashlib
import hmac
import os
import platform
import sqlite3
from datetime import datetime

from core.config import PROGRAM_SERI_NO

from .db import baglan, db_baglan
from .loglama import log_yaz

LISANS_TABLO_SQL = """
CREATE TABLE IF NOT EXISTS lisans_bilgileri (
    id INTEGER PRIMARY KEY CHECK (id=1),
    musteri TEXT,
    lisans_anahtari TEXT,
    cihaz_kodu TEXT,
    durum TEXT DEFAULT 'PASIF',
    olusturma_tarihi TEXT,
    son_kontrol_tarihi TEXT
)
"""


def cihaz_kodu_uret() -> str:
    ham = "|".join([
        platform.node(), platform.system(), platform.machine(), os.environ.get("USERNAME", ""), PROGRAM_SERI_NO,
    ])
    return hashlib.sha256(ham.encode("utf-8", "ignore")).hexdigest()[:16].upper()


def lisans_tablosu_olustur() -> None:
    with db_baglan() as conn:
        conn.execute(LISANS_TABLO_SQL)
        conn.execute(
            "INSERT OR IGNORE INTO lisans_bilgileri(id, cihaz_kodu, durum, olusturma_tarihi) VALUES (1, ?, 'PASIF', ?)",
            (cihaz_kodu_uret(), datetime.now().isoformat(timespec="seconds")),
        )


def yerel_lisans_anahtari(musteri: str, gizli: str | None = None) -> str:
    """Basit offline lisans anahtarı üretir. Gizli değer env üzerinden verilmelidir."""
    secret = (gizli or os.environ.get("DAL_ERP_LICENSE_SECRET") or PROGRAM_SERI_NO).encode()
    msg = f"{musteri}|{cihaz_kodu_uret()}|{PROGRAM_SERI_NO}".encode()
    digest = hmac.new(secret, msg, hashlib.sha256).hexdigest().upper()
    return "-".join([digest[i:i+5] for i in range(0, 25, 5)])


def lisans_kaydet(musteri: str, lisans_anahtari: str) -> bool:
    lisans_tablosu_olustur()
    beklenen = yerel_lisans_anahtari(musteri)
    durum = "AKTIF" if hmac.compare_digest(lisans_anahtari.strip().upper(), beklenen) else "GECERSIZ"
    with db_baglan() as conn:
        conn.execute(
            "UPDATE lisans_bilgileri SET musteri=?, lisans_anahtari=?, cihaz_kodu=?, durum=?, son_kontrol_tarihi=? WHERE id=1",
            (musteri, lisans_anahtari.strip().upper(), cihaz_kodu_uret(), durum, datetime.now().isoformat(timespec="seconds")),
        )
    log_yaz(f"Lisans durumu güncellendi: {durum}", "LISANS")
    return durum == "AKTIF"


def lisans_durumu() -> dict:
    lisans_tablosu_olustur()
    try:
        with baglan() as conn:
            row = conn.execute("SELECT musteri, cihaz_kodu, durum, son_kontrol_tarihi FROM lisans_bilgileri WHERE id=1").fetchone()
        return {"musteri": row[0], "cihaz_kodu": row[1], "durum": row[2], "son_kontrol_tarihi": row[3]}
    except sqlite3.Error as hata:
        return {"musteri": None, "cihaz_kodu": cihaz_kodu_uret(), "durum": "HATA", "son_kontrol_tarihi": str(hata)}
