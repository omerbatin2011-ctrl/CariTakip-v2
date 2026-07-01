from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from core.config import BASE_DIR

from .db import db_baglan
from .loglama import log_yaz


def _rapor_klasoru() -> Path:
    klasor = Path(BASE_DIR) / "rapor_ciktilari"
    klasor.mkdir(parents=True, exist_ok=True)
    return klasor


def _csv_yaz(dosya: Path, basliklar: list[str], satirlar) -> str:
    with dosya.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(basliklar)
        writer.writerows(satirlar)
    log_yaz(f"CSV rapor oluşturuldu: {dosya.name}", "RAPOR")
    return str(dosya)


def cari_bakiye_csv() -> str:
    dosya = _rapor_klasoru() / f"cari_bakiye_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT c.ad,
                   COALESCE(SUM(CASE
                     WHEN h.tip IN ('BORÇ','BORC','SATIŞ','SATIS') THEN h.tutar
                     WHEN h.tip IN ('ALACAK','TAHSİLAT','TAHSILAT') THEN -h.tutar
                     ELSE 0 END), 0) AS bakiye
            FROM cariler c
            LEFT JOIN hareketler h ON h.cari_id=c.id
            WHERE COALESCE(c.aktif,1)=1
            GROUP BY c.id, c.ad
            ORDER BY bakiye DESC, c.ad
        """)
        rows = cur.fetchall()
    return _csv_yaz(dosya, ["Cari", "Bakiye"], rows)


def stok_csv() -> str:
    dosya = _rapor_klasoru() / f"stok_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT g.ad AS grup, u.ad AS urun, COALESCE(u.barkod,''), COALESCE(u.stok,0), COALESCE(u.varsayilan_fiyat,0)
            FROM urunler u
            LEFT JOIN urun_gruplari g ON g.id=u.grup_id
            WHERE COALESCE(u.aktif,1)=1
            ORDER BY g.ad, u.ad
        """)
        rows = cur.fetchall()
    return _csv_yaz(dosya, ["Grup", "Ürün", "Barkod", "Stok", "Varsayılan Fiyat"], rows)


def kasa_csv() -> str:
    dosya = _rapor_klasoru() / f"kasa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT tarih, tip, odeme_tipi, tutar, aciklama, kaynak, kullanici
            FROM kasa_hareketleri
            ORDER BY id DESC
        """)
        rows = cur.fetchall()
    return _csv_yaz(dosya, ["Tarih", "Tip", "Ödeme Tipi", "Tutar", "Açıklama", "Kaynak", "Kullanıcı"], rows)
