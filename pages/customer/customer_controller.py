"""Customer controller.

UI ile servis katmanı arasındaki koordinasyonu sağlar.
"""

from __future__ import annotations

from services.cari_service import (
    cari_cache_temizle,
    cari_detay_ozeti,
    cari_liste_sayfasi,
    cari_ozetleri,
)


class CustomerController:
    """Cari işlemlerinin controller katmanı."""

    @staticmethod
    def get_summary():
        """Cari özet bilgilerini döndürür."""
        return cari_ozetleri()

    @staticmethod
    def get_page(search: str = "", page: int = 1, limit: int = 120):
        """Cari listesinin sayfalanmış sonucunu döndürür."""
        return cari_liste_sayfasi(
            arama=search,
            sayfa_no=page,
            limit=limit,
        )

    @staticmethod
    def get_detail(customer_id: int):
        """Seçili cari için detay özetini döndürür."""
        return cari_detay_ozeti(customer_id)

    @staticmethod
    def clear_cache() -> None:
        """Cari modülü cache kayıtlarını temizler."""
        cari_cache_temizle()
