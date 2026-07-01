"""Satış ekranı motoru.

Bu paket v135 ile başlatıldı. Eski moduller.satis_ui yolu
uyumluluk için korunur; gerçek uygulama sınıfı burada yaşar.
"""

from .sales_page import SatisMixin

__all__ = ["SatisMixin"]
