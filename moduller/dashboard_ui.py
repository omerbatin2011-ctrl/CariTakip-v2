"""Geriye dönük uyumluluk katmanı.

v134 itibarıyla Dashboard sayfası pages/dashboard altına taşındı.
Eski importları kırmamak için build_dashboard burada yeniden dışa aktarılır.
"""

from pages.dashboard.dashboard_page import build_dashboard

__all__ = ["build_dashboard"]
