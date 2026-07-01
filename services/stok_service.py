"""Ürün/Stok modülü servis katmanı."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from moduller.db import db_baglan
from moduller.perf_utils import TTLCache

DEFAULT_LIMIT = 120
MIN_LIMIT = 50
MAX_LIMIT = 500

CACHE_KEY_STOK_OZET = "stok_ozetleri"
FATURA_FILTER_ALL = "Tümü"
FATURA_FILTER_INVOICED = "Faturalı"
FATURA_STATUS_INVOICED = "FATURALI"
FATURA_STATUS_UNINVOICED = "FATURASIZ"

_stok_ozet_cache = TTLCache(ttl_seconds=5, max_items=8)


@dataclass(slots=True)
class StokListeSonuc:
    """Sayfalı stok listesi sonucu."""

    rows: list[tuple]
    toplam_kayit: int
    sayfa_no: int
    max_sayfa: int
    limit: int
    offset: int


def _to_int(value: object) -> int:
    return int(value or 0)


def _to_float(value: object) -> float:
    return float(value or 0)


def _normalize_limit(limit: int | str | None) -> int:
    return max(MIN_LIMIT, min(MAX_LIMIT, int(limit or DEFAULT_LIMIT)))


def _normalize_page(page: int | str | None) -> int:
    return max(1, int(page or 1))


def stok_cache_temizle() -> None:
    """Stok servis cache'ini temizler."""

    _stok_ozet_cache.clear()


def stok_ozetleri() -> dict[str, int | float]:
    """Ürün sayısı, kritik stok ve toplam stok miktarı özetini döndürür."""

    def _hesapla() -> dict[str, int | float]:
        with db_baglan() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    SELECT
                        COUNT(*) AS toplam_urun,
                        COALESCE(SUM(stok), 0) AS toplam_stok,
                        COALESCE(
                            SUM(
                                CASE
                                    WHEN COALESCE(stok, 0) <= COALESCE(kritik_stok, 0)
                                    THEN 1
                                    ELSE 0
                                END
                            ),
                            0
                        ) AS kritik
                    FROM urunler
                    WHERE COALESCE(aktif, 1) = 1
                    """
                )
                toplam_urun, toplam_stok, kritik = cur.fetchone()
            except Exception:
                toplam_urun, toplam_stok, kritik = 0, 0, 0

        return {
            "toplam_urun": _to_int(toplam_urun),
            "toplam_stok": _to_float(toplam_stok),
            "kritik": _to_int(kritik),
        }

    return _stok_ozet_cache.get(CACHE_KEY_STOK_OZET, _hesapla)


def stok_liste_indeksleri_hazirla(conn: Any) -> None:
    """Stok listeleme sorgularını destekleyen indeksleri hazırlar."""

    conn.execute("CREATE INDEX IF NOT EXISTS idx_urun_alislari_urun_id_id ON urun_alislari(urun_id, id DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_urunler_aktif_ad ON urunler(aktif, ad)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_urunler_barkod ON urunler(barkod)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_urunler_grup_aktif_ad ON urunler(grup_id, aktif, ad)")


def _stok_liste_where(arama: str, fatura_filtre: str) -> tuple[str, list[object]]:
    where = "WHERE COALESCE(u.aktif, 1) = 1"
    params: list[object] = []
    arama = (arama or "").strip()

    if arama:
        like = f"%{arama}%"
        where += " AND (u.ad LIKE ? OR g.ad LIKE ? OR COALESCE(u.barkod, '') LIKE ?)"
        params.extend([like, like, like])

    if fatura_filtre != FATURA_FILTER_ALL:
        hedef = FATURA_STATUS_INVOICED if fatura_filtre == FATURA_FILTER_INVOICED else FATURA_STATUS_UNINVOICED
        where += " AND COALESCE(ua.fatura_durumu, ?) = ?"
        params.extend([FATURA_STATUS_INVOICED, hedef])

    return where, params


def _stok_liste_count(cur: Any, where: str, params: list[object]) -> int:
    cur.execute(
        f"""
        {SQL_LATEST_PURCHASE}
        SELECT COUNT(*)
        FROM urunler u
        LEFT JOIN urun_gruplari g ON g.id = u.grup_id
        LEFT JOIN son_alis sa ON sa.urun_id = u.id
        LEFT JOIN urun_alislari ua ON ua.id = sa.son_alis_id
        {where}
        """,
        params,
    )
    return _to_int(cur.fetchone()[0])


def _stok_liste_rows(cur: Any, where: str, params: list[object], limit: int, offset: int) -> list[tuple]:
    cur.execute(
        f"""
        {SQL_LATEST_PURCHASE}
        SELECT
            g.ad,
            u.id,
            u.ad,
            COALESCE(u.barkod, ''),
            COALESCE(u.stok, 0),
            COALESCE(u.varsayilan_fiyat, 0),
            COALESCE(ua.alis_fiyati_tl, 0),
            COALESCE(ua.fatura_durumu, ?)
        FROM urunler u
        LEFT JOIN urun_gruplari g ON g.id = u.grup_id
        LEFT JOIN son_alis sa ON sa.urun_id = u.id
        LEFT JOIN urun_alislari ua ON ua.id = sa.son_alis_id
        {where}
        ORDER BY g.ad, u.ad
        LIMIT ? OFFSET ?
        """,
        [FATURA_STATUS_INVOICED, *params, limit, offset],
    )
    return cur.fetchall()


SQL_LATEST_PURCHASE = """
WITH son_alis AS (
    SELECT urun_id, MAX(id) AS son_alis_id
    FROM urun_alislari
    GROUP BY urun_id
)
"""


def stok_liste_sayfasi(
    arama: str = "",
    fatura_filtre: str = FATURA_FILTER_ALL,
    sayfa_no: int = 1,
    limit: int = DEFAULT_LIMIT,
) -> StokListeSonuc:
    """Stok listesini sayfalı ve indeks dostu olarak döndürür."""

    limit = _normalize_limit(limit)
    sayfa_no = _normalize_page(sayfa_no)

    with db_baglan() as conn:
        stok_liste_indeksleri_hazirla(conn)
        cur = conn.cursor()
        where, params = _stok_liste_where(arama, fatura_filtre)

        toplam_kayit = _stok_liste_count(cur, where, params)
        max_sayfa = max(1, ((toplam_kayit - 1) // limit) + 1) if toplam_kayit else 1

        if sayfa_no > max_sayfa:
            sayfa_no = max_sayfa

        offset = (sayfa_no - 1) * limit
        rows = _stok_liste_rows(cur, where, params, limit, offset)

    return StokListeSonuc(
        rows=rows,
        toplam_kayit=toplam_kayit,
        sayfa_no=sayfa_no,
        max_sayfa=max_sayfa,
        limit=limit,
        offset=offset,
    )
