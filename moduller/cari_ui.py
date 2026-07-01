"""Cari UI uyumluluk katmanı (v136).

Asıl cari sayfası artık pages/customer/customer_page.py içinde yaşar.
Eski importların kırılmaması için CariMixin adı korunur.
"""

from pages.customer.customer_page import CustomerPageMixin as CariMixin

__all__ = ["CariMixin"]
