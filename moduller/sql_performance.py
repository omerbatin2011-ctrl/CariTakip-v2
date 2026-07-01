"""SQLite performans yardımcıları.

Bu modül tablo/kolon varlığını kontrol ederek indeks oluşturur. Böylece eski
müşteri veritabanlarında eksik kolon varsa uygulama açılışı bozulmaz.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable

IndexSpec = tuple[str, str, tuple[str, ...], str | None]


def tablo_var_mi(conn: sqlite3.Connection, tablo: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1", (tablo,)
    ).fetchone()
    return row is not None


def tablo_kolonlari(conn: sqlite3.Connection, tablo: str) -> set[str]:
    if not tablo_var_mi(conn, tablo):
        return set()
    return {row[1] for row in conn.execute(f"PRAGMA table_info({tablo})").fetchall()}


def indeks_var_mi(conn: sqlite3.Connection, indeks: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='index' AND name=? LIMIT 1", (indeks,)
    ).fetchone()
    return row is not None


def _where_guvenli_mi(where: str | None, kolonlar: set[str]) -> bool:
    if not where:
        return True
    # Basit güvenlik: where ifadesinde kullanılan ana kolon isimlerinden en az biri tabloda olmalı.
    # SQL kullanıcı girdisinden gelmediği için burada amaç eski şemalarda kırılmayı önlemek.
    return any(kolon in where for kolon in kolonlar)


def guvenli_indeks_olustur(
    conn: sqlite3.Connection,
    indeks_adi: str,
    tablo: str,
    kolonlar: Iterable[str],
    where: str | None = None,
) -> bool:
    """Kolonlar varsa indeksi oluşturur, yoksa sessizce atlar."""
    kolon_tuple = tuple(kolonlar)
    mevcut_kolonlar = tablo_kolonlari(conn, tablo)
    if not mevcut_kolonlar or not set(kolon_tuple).issubset(mevcut_kolonlar):
        return False
    if not _where_guvenli_mi(where, mevcut_kolonlar):
        return False
    kolon_sql = ", ".join(kolon_tuple)
    where_sql = f" WHERE {where}" if where else ""
    conn.execute(f"CREATE INDEX IF NOT EXISTS {indeks_adi} ON {tablo}({kolon_sql}){where_sql}")
    return True


def kritik_sql_indeksleri_olustur(conn: sqlite3.Connection) -> int:
    """Sık kullanılan ekranlar için güvenli indeks setini oluşturur."""
    specs: tuple[IndexSpec, ...] = (
        # Cari ekranları: aktif liste, hızlı arama ve cari hareketleri
        ("idx_v45_cariler_aktif_ad_id", "cariler", ("aktif", "ad", "id"), None),
        ("idx_v45_cariler_aktif_telefon", "cariler", ("aktif", "telefon"), None),
        ("idx_v45_cariler_vergi_no", "cariler", ("vergi_no",), "vergi_no IS NOT NULL"),
        ("idx_v45_hareketler_aktif_cari_tarih", "hareketler", ("aktif", "cari_id", "tarih"), None),
        ("idx_v45_hareketler_cari_tip_tarih", "hareketler", ("cari_id", "tip", "tarih"), None),
        # Satış/teklif ekranları
        ("idx_v45_satislar_belge_tarih_id", "satislar", ("belge_turu", "tarih", "id"), None),
        ("idx_v45_satislar_cari_belge_tarih", "satislar", ("cari_id", "belge_turu", "tarih"), None),
        ("idx_v45_satislar_teklif_no", "satislar", ("teklif_no",), "teklif_no IS NOT NULL"),
        ("idx_v45_satis_kalemleri_satis_urun", "satis_kalemleri", ("satis_id", "urun_adi"), None),
        # Stok/barkod ekranları
        ("idx_v45_urunler_aktif_barkod_id", "urunler", ("aktif", "barkod", "id"), None),
        ("idx_v45_urunler_aktif_stok", "urunler", ("aktif", "stok"), None),
        ("idx_v45_urun_alislari_urun_tarih", "urun_alislari", ("urun_id", "tarih"), None),
        # Kasa/tahsilat raporları
        ("idx_v45_tahsilat_cari_tarih", "tahsilat_makbuzlari", ("cari_id", "tarih"), None),
        ("idx_v45_kasa_hareketleri_tarih", "kasa_hareketleri", ("tarih",), None),
        ("idx_v45_kasa_hareketleri_tip_tarih", "kasa_hareketleri", ("tip", "tarih"), None),
    )
    created_or_existing = 0
    for indeks_adi, tablo, kolonlar, where in specs:
        try:
            if guvenli_indeks_olustur(conn, indeks_adi, tablo, kolonlar, where):
                created_or_existing += 1
        except sqlite3.DatabaseError:
            # İndeks oluşturma performans iyileştirmesidir; uygulama açılışını kırmamalı.
            continue
    return created_or_existing


def sqlite_optimize(conn: sqlite3.Connection) -> None:
    """SQLite istatistiklerini hafif ve güvenli şekilde günceller."""
    try:
        conn.execute("PRAGMA analysis_limit = 1000")
        conn.execute("PRAGMA optimize")
    except sqlite3.DatabaseError:
        pass
