"""Cari modülü servis katmanı - V52 stabil refaktör."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from moduller.db import db_baglan
from moduller.perf_utils import TTLCache

DEFAULT_LIMIT = 120
MIN_LIMIT = 50
MAX_LIMIT = 500

CACHE_KEY_CARI_OZET = "cari_ozetleri"
CACHE_KEY_CARI_DETAY = "cari_detay"

_cari_ozet_cache = TTLCache(ttl_seconds=5, max_items=8)
_cari_detay_cache = TTLCache(ttl_seconds=8, max_items=512)


@dataclass(slots=True)
class CariListeSonucu:
    rows: list[tuple]
    toplam_kayit: int
    sayfa_no: int
    max_sayfa: int
    limit: int
    offset: int


@dataclass(slots=True)
class CariDetayOzeti:
    ad: str
    telefon: str
    adres: str
    vergi_dairesi: str
    vergi_no: str
    borc: float
    tahsilat: float
    bakiye: float


def _to_float(value: Any) -> float:
    """SQLite dönüşlerinden gelen boş değerleri güvenli float'a çevirir."""
    return float(value or 0)


def _to_int(value: Any) -> int:
    """SQLite dönüşlerinden gelen boş değerleri güvenli int'e çevirir."""
    return int(value or 0)


def _to_text(value: Any) -> str:
    """SQLite dönüşlerinden gelen boş değerleri güvenli metne çevirir."""
    return str(value or "")


def cari_cache_temizle() -> None:
    """Cari modülünde kullanılan kısa süreli cache kayıtlarını temizler."""
    _cari_ozet_cache.clear()
    _cari_detay_cache.clear()


def cari_liste_indeksleri_hazirla(conn) -> None:
    """Cari listeleme sorgularını destekleyen indeksleri hazırlar."""
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cariler_aktif_ad ON cariler(aktif, ad)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cariler_aktif_tel ON cariler(aktif, telefon)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cariler_aktif_vergi ON cariler(aktif, vergi_no)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_hareketler_aktif_cari_tip ON hareketler(aktif, cari_id, tip)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_hareketler_cari_aktif_tip ON hareketler(cari_id, aktif, tip)")


def _cari_liste_where(arama: str) -> tuple[str, list[object]]:
    """Cari listeleme için ortak WHERE koşulunu üretir."""
    where = "WHERE COALESCE(c.aktif,1)=1"
    params: list[object] = []
    arama = (arama or "").strip()

    if arama:
        like = f"%{arama}%"
        where += (
            " AND (c.ad LIKE ? OR COALESCE(c.telefon,'') LIKE ? "
            "OR COALESCE(c.adres,'') LIKE ? OR COALESCE(c.vergi_no,'') LIKE ?)"
        )
        params.extend([like, like, like, like])

    return where, params


def cari_ozetleri() -> dict[str, float | int]:
    """Aktif cari sayısı ile toplam borç, tahsilat ve bakiyeyi döndürür."""

    def _hesapla() -> dict[str, float | int]:
        with db_baglan() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM cariler WHERE COALESCE(aktif,1)=1) AS toplam,
                    COALESCE(SUM(CASE WHEN tip='BORÇ' THEN tutar ELSE 0 END), 0) AS borc,
                    COALESCE(SUM(CASE WHEN tip='TAHSİLAT' THEN tutar ELSE 0 END), 0) AS tahsilat
                FROM hareketler
                WHERE COALESCE(aktif,1)=1
                """
            )
            toplam, borc, tahsilat = cur.fetchone()

        borc = _to_float(borc)
        tahsilat = _to_float(tahsilat)
        return {
            "toplam": _to_int(toplam),
            "borc": borc,
            "tahsilat": tahsilat,
            "bakiye": borc - tahsilat,
        }

    return _cari_ozet_cache.get(CACHE_KEY_CARI_OZET, _hesapla)


def _cari_liste_count(cur, where: str, params: list[object]) -> int:
    cur.execute(f"SELECT COUNT(*) FROM cariler c {where}", params)
    return _to_int(cur.fetchone()[0])


def _cari_liste_rows(cur, where: str, params: list[object], limit: int, offset: int) -> list[tuple]:
    cur.execute(
        f"""
        WITH secili_cariler AS (
            SELECT
                c.id,
                c.ad,
                COALESCE(c.telefon, '') AS telefon,
                COALESCE(c.adres, '') AS adres
            FROM cariler c
            {where}
            ORDER BY c.ad
            LIMIT ? OFFSET ?
        )
        SELECT
            sc.id,
            sc.ad,
            sc.telefon,
            sc.adres,
            COALESCE(SUM(CASE WHEN h.tip='BORÇ' THEN h.tutar ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN h.tip='TAHSİLAT' THEN h.tutar ELSE 0 END), 0) AS bakiye
        FROM secili_cariler sc
        LEFT JOIN hareketler h
            ON h.cari_id = sc.id
            AND COALESCE(h.aktif,1)=1
        GROUP BY sc.id, sc.ad, sc.telefon, sc.adres
        ORDER BY sc.ad
        """,
        params + [limit, offset],
    )
    return cur.fetchall()


def cari_liste_sayfasi(arama: str = "", sayfa_no: int = 1, limit: int = DEFAULT_LIMIT) -> CariListeSonucu:
    """Cari listesini arama, sayfalama ve bakiye bilgisiyle döndürür."""
    arama = (arama or "").strip()
    limit = max(MIN_LIMIT, min(MAX_LIMIT, int(limit or DEFAULT_LIMIT)))
    sayfa_no = max(1, int(sayfa_no or 1))

    with db_baglan() as conn:
        cari_liste_indeksleri_hazirla(conn)
        cur = conn.cursor()
        where, params = _cari_liste_where(arama)

        toplam_kayit = _cari_liste_count(cur, where, params)
        max_sayfa = max(1, ((toplam_kayit - 1) // limit) + 1) if toplam_kayit else 1
        if sayfa_no > max_sayfa:
            sayfa_no = max_sayfa

        offset = (sayfa_no - 1) * limit
        raw_rows = _cari_liste_rows(cur, where, params, limit, offset)

    rows = [
        (
            _to_int(cari_id),
            index,
            _to_text(ad),
            _to_text(telefon),
            _to_text(adres),
            _to_float(bakiye),
        )
        for index, (cari_id, ad, telefon, adres, bakiye) in enumerate(
            raw_rows,
            start=offset + 1,
        )
    ]

    return CariListeSonucu(rows, toplam_kayit, sayfa_no, max_sayfa, limit, offset)


def _cari_detay_ozeti_hesapla(cari_id: int) -> CariDetayOzeti | None:
    with db_baglan() as conn:
        cari_liste_indeksleri_hazirla(conn)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                c.ad,
                COALESCE(c.telefon, ''),
                COALESCE(c.adres, ''),
                COALESCE(c.vergi_dairesi, ''),
                COALESCE(c.vergi_no, ''),
                COALESCE(SUM(CASE WHEN h.tip='BORÇ' THEN h.tutar ELSE 0 END), 0) AS borc,
                COALESCE(SUM(CASE WHEN h.tip='TAHSİLAT' THEN h.tutar ELSE 0 END), 0) AS tahsilat
            FROM cariler c
            LEFT JOIN hareketler h ON h.cari_id = c.id AND COALESCE(h.aktif,1)=1
            WHERE COALESCE(c.aktif,1)=1 AND c.id=?
            GROUP BY c.id, c.ad, c.telefon, c.adres, c.vergi_dairesi, c.vergi_no
            """,
            (cari_id,),
        )
        row = cur.fetchone()

    if not row:
        return None

    ad, telefon, adres, vergi_dairesi, vergi_no, borc, tahsilat = row
    borc = _to_float(borc)
    tahsilat = _to_float(tahsilat)
    return CariDetayOzeti(
        ad=_to_text(ad),
        telefon=_to_text(telefon),
        adres=_to_text(adres),
        vergi_dairesi=_to_text(vergi_dairesi),
        vergi_no=_to_text(vergi_no),
        borc=borc,
        tahsilat=tahsilat,
        bakiye=borc - tahsilat,
    )


def cari_detay_ozeti(cari_id: int) -> CariDetayOzeti | None:
    """Seçili cari detayını kısa TTL cache ile döndürür."""
    try:
        cari_id = int(cari_id)
    except (TypeError, ValueError):
        return None

    return _cari_detay_cache.get(
        (CACHE_KEY_CARI_DETAY, cari_id),
        lambda: _cari_detay_ozeti_hesapla(cari_id),
    )
