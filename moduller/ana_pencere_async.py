
from PySide6.QtWidgets import QMessageBox

from moduller.async_worker import VeriYukleyiciWorker
from moduller.loglama import log_yaz

try:
    from kur_modulu import tcmb_usd_kuru_al, tl_karsiligi_hesapla
except Exception:
    tcmb_usd_kuru_al = None
    def tl_karsiligi_hesapla(tutar, para_birimi="TL", kur=1):
        try:
            tutar = float(tutar or 0)
            kur = float(kur or 1)
        except Exception:
            return 0.0
        return tutar if str(para_birimi).upper() == "TL" else tutar * kur

class AnaPencereAsyncMixin:
    def arka_plan_calistir(self, is_fonksiyonu, basarili=None, hatali=None, durum_metni="İşlem arka planda çalışıyor..."):
        """v84: Ağ/DB gibi uzun işlemleri GUI'yi dondurmadan çalıştırır."""
        try:
            if hasattr(self, "lblDurumCubugu") and durum_metni:
                self.lblDurumCubugu.setText(f"DAL ERP v139  •  {durum_metni}")
        except Exception:
            pass

        worker = VeriYukleyiciWorker(is_fonksiyonu)
        self._arka_plan_isleri.append(worker)

        def _temizle():
            try:
                if worker in self._arka_plan_isleri:
                    self._arka_plan_isleri.remove(worker)
            except Exception:
                pass
            try:
                self.durum_cubugu_guncelle()
            except Exception:
                pass

        def _hata(mesaj):
            log_yaz(f"Arka plan işlem hatası: {mesaj}")
            if hatali:
                hatali(mesaj)
            else:
                QMessageBox.warning(self, "İşlem Tamamlanamadı", str(mesaj).splitlines()[0])

        if basarili:
            worker.veri_hazir.connect(basarili)
        worker.hata_olustu.connect(_hata)
        worker.bitti.connect(_temizle)
        worker.start()
        return worker

