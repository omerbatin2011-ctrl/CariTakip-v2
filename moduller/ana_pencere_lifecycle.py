import os
import shutil
from datetime import datetime

from PySide6.QtWidgets import QMessageBox

from core.config import BASE_DIR, DB_ADI, YEDEK_KLASOR_ADI
from moduller.loglama import log_yaz
from moduller.sistem import otomatik_gunluk_yedek_olustur

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

class AnaPencereLifecycleMixin:
    def closeEvent(self, event):
        """Program kapanırken kullanıcı onayı alır, timer'ı durdurur ve güvenli yedek oluşturur."""
        cevap = QMessageBox.question(
            self,
            "Çıkış Onayı",
            "Programdan çıkmak istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if cevap != QMessageBox.Yes:
            event.ignore()
            return

        try:
            if hasattr(self, "oturum_timer") and self.oturum_timer.isActive():
                self.oturum_timer.stop()
        except Exception as hata:
            try:
                log_yaz(f"Oturum timer kapatma hatası: {hata}")
            except Exception:
                pass

        try:
            # Merkezi günlük yedekleme fonksiyonu varsa onu kullan.
            otomatik_gunluk_yedek_olustur()
        except Exception as hata:
            try:
                os.makedirs(os.path.join(BASE_DIR, YEDEK_KLASOR_ADI), exist_ok=True)
                if os.path.exists(DB_ADI):
                    tarih = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    hedef = os.path.join(BASE_DIR, YEDEK_KLASOR_ADI, f"kapanis_yedegi_{tarih}.db")
                    shutil.copy2(DB_ADI, hedef)
            except Exception as yedek_hatasi:
                try:
                    log_yaz(f"Kapanış yedekleme hatası: {yedek_hatasi}")
                except Exception:
                    pass
            try:
                log_yaz(f"Otomatik günlük yedekleme hatası: {hata}")
            except Exception:
                pass

        try:
            log_yaz("Sistem güvenli bir şekilde kapatıldı.")
        except Exception:
            pass
        event.accept()

