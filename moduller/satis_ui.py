"""Uyumluluk katmanı.

v135 itibarıyla Satış ekranı pages.sales paketine taşındı.
Eski importlar kırılmasın diye SatisMixin burada yeniden dışa aktarılır.
"""

from pages.sales.sales_page import SatisMixin

__all__ = ["SatisMixin"]
