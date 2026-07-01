"""Satış ekranı iş mantığı için hazırlık modülü.

v135'te güvenli geçiş amacıyla mevcut çalışan akış korunmuştur.
Sonraki sürümlerde kayıt, toplam hesaplama, ödeme ve stok düşme
mantıkları bu sınıfa taşınacaktır.
"""

class SalesController:
    """Satış iş kurallarını UI'dan ayırmak için temel sınıf."""

    def __init__(self, owner=None):
        self.owner = owner

    def format_money(self, value):
        try:
            return f"{float(value):,.2f} ₺".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception:
            return "0,00 ₺"
