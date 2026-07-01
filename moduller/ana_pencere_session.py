import time

from PySide6.QtCore import QEvent, QTimer
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout

from core.config import GIRIS_KILIT_SANIYE, GIRIS_MAKS_DENEME
from moduller.loglama import log_yaz
from moduller.sistem import master_sifre_dogrula, oturum_zaman_asimi_getir

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

class AnaPencereSessionMixin:
    def eventFilter(self, obj, event):
        try:
            if event.type() in (QEvent.MouseButtonPress, QEvent.MouseButtonDblClick, QEvent.KeyPress, QEvent.Wheel):
                self.son_aktivite_zamani = time.time()
        except Exception:
            pass
        return super().eventFilter(obj, event)

    def oturum_zaman_asimi_kontrol(self):
        dakika = oturum_zaman_asimi_getir()
        if dakika <= 0 or self.oturum_kilitli:
            return
        if time.time() - self.son_aktivite_zamani >= dakika * 60:
            self.oturum_kilitli = True
            log_yaz(f"Oturum zaman aşımına uğradı ({dakika} dk).")
            self.oturum_kilidi_ac()

    def oturum_kilidi_ac(self):
        pencere = QDialog(self)
        pencere.setWindowTitle("Oturum Kilitlendi")
        pencere.resize(380, 220)
        layout = QVBoxLayout()

        lbl = QLabel("Oturum zaman aşımına uğradı.\nDevam etmek için ana şifreyi giriniz.")
        lbl.setStyleSheet("font-size:15px;font-weight:bold;color:#0D47A1;")
        layout.addWidget(lbl)

        txtSifre = QLineEdit()
        txtSifre.setEchoMode(QLineEdit.Password)
        txtSifre.setPlaceholderText("Ana şifre")
        layout.addWidget(txtSifre)

        btn = QPushButton("Kilidi Aç")
        layout.addWidget(btn)

        deneme = {"sayac": 0, "kilit_baslangic": 0}
        kontrol_kilit = {"aktif": False}

        def _kontrol_serbest_birak():
            def _ac():
                kontrol_kilit["aktif"] = False
                btn.setEnabled(True)
            QTimer.singleShot(350, _ac)

        def kontrol():
            if kontrol_kilit.get("aktif"):
                return
            kontrol_kilit["aktif"] = True
            btn.setEnabled(False)
            simdi = time.time()
            if deneme["kilit_baslangic"] and simdi - deneme["kilit_baslangic"] < GIRIS_KILIT_SANIYE:
                kalan = int(GIRIS_KILIT_SANIYE - (simdi - deneme["kilit_baslangic"]))
                QMessageBox.warning(pencere, "Kilit", f"Çok fazla hatalı deneme.\n{kalan} saniye sonra tekrar deneyin.")
                _kontrol_serbest_birak()
                return

            if master_sifre_dogrula(txtSifre.text().strip()):
                self.oturum_kilitli = False
                self.son_aktivite_zamani = time.time()
                log_yaz("Oturum kilidi açıldı.")
                pencere.accept()
                return

            deneme["sayac"] += 1
            if deneme["sayac"] >= GIRIS_MAKS_DENEME:
                deneme["kilit_baslangic"] = time.time()
                deneme["sayac"] = 0
                log_yaz("Oturum kilidinde 3 hatalı ana şifre denemesi.")
                QMessageBox.warning(pencere, "Kilit", "3 hatalı deneme yapıldı. 5 dakika bekleyin.")
                _kontrol_serbest_birak()
                return
            else:
                QMessageBox.warning(pencere, "Hata", f"Ana şifre yanlış. Kalan hak: {GIRIS_MAKS_DENEME-deneme['sayac']}")
                _kontrol_serbest_birak()
                return

        btn.setAutoDefault(False)
        btn.setDefault(False)
        btn.clicked.connect(kontrol)
        txtSifre.returnPressed.connect(kontrol)
        pencere.setLayout(layout)
        pencere.exec()

