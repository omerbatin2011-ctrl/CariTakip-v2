"""Arka plan işçi sistemi.

v84: Uzun süren veritabanı, dosya ve ağ işlemlerinin ana PySide6 GUI
thread'ini dondurmaması için genel amaçlı QThread tabanlı worker.
"""
from __future__ import annotations

import traceback

from PySide6.QtCore import QThread, Signal


class VeriYukleyiciWorker(QThread):
    """Verilen fonksiyonu arka planda çalıştırıp sonucu sinyalle döndürür."""

    veri_hazir = Signal(object)
    hata_olustu = Signal(str)
    bitti = Signal()

    def __init__(self, is_fonksiyonu, *args, **kwargs):
        super().__init__()
        self.is_fonksiyonu = is_fonksiyonu
        self.args = args
        self.kwargs = kwargs
        self._iptal_istendi = False

    def iptal_et(self):
        """Çalışan işi zorla durdurmaz; sonuç sinyalinin yayınlanmasını engeller."""
        self._iptal_istendi = True

    def iptal_istendi(self) -> bool:
        return self._iptal_istendi

    def run(self):
        try:
            sonuc = self.is_fonksiyonu(*self.args, **self.kwargs)
            if not self._iptal_istendi:
                self.veri_hazir.emit(sonuc)
        except Exception as hata:
            detay = f"{type(hata).__name__}: {hata}\n{traceback.format_exc()}"
            if not self._iptal_istendi:
                self.hata_olustu.emit(detay)
        finally:
            self.bitti.emit()
