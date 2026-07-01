import os
import shutil
import urllib.parse
import webbrowser
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core.config import BASE_DIR, DB_ADI
from moduller.db import db_ayarla
from moduller.loglama import log_yaz
from moduller.sistem import firma_bilgisi_getir, veritabani_gecerli_mi
from moduller.veritabani_bakim import eski_yedekleri_temizle, guvenli_sqlite_yedekle

db_ayarla(DB_ADI)


class YedeklemeMixin:
    def yedek_olustur(self, prefix="manuel_yedek"):
        try:
            os.makedirs(os.path.join(BASE_DIR, "yedekler"), exist_ok=True)

            if not os.path.exists(DB_ADI):
                QMessageBox.warning(self, "Hata", "Veritabanı dosyası bulunamadı.")
                return None

            # SQLite çalışırken düz dosya kopyası yerine backup API kullanılır.
            # Bu yöntem WAL açıkken de tutarlı yedek üretir.
            yedek_yolu = guvenli_sqlite_yedekle(os.path.join(BASE_DIR, "yedekler"), prefix)
            eski_yedekleri_temizle(os.path.join(BASE_DIR, "yedekler"), 30)
            if yedek_yolu:
                log_yaz(f"Yedek oluşturuldu: {os.path.basename(yedek_yolu)}")
            return yedek_yolu

        except Exception as hata:
            QMessageBox.warning(self, "Hata", f"Yedek oluşturulamadı:\n{hata}")
            return None
    def yedekler_klasorunu_ac(self):
        try:
            os.makedirs(os.path.join(BASE_DIR, "yedekler"), exist_ok=True)
            os.startfile(os.path.join(BASE_DIR, "yedekler"))
        except Exception as hata:
            QMessageBox.warning(self, "Hata", f"Yedekler klasörü açılamadı:\n{hata}")
    def manuel_yedek_olustur(self):
        yedek_yolu = self.yedek_olustur("manuel_yedek")

        if yedek_yolu:
            try:
                os.startfile(os.path.join(BASE_DIR, "yedekler"))
            except Exception:
                pass

            QMessageBox.information(
                self,
                "Yedek Oluşturuldu",
                f"Yedek dosyası oluşturuldu:\n{yedek_yolu}"
            )
    def gmail_yedek_hazirla(self):
        yedek_yolu = self.yedek_olustur("gmail_yedek")

        if not yedek_yolu:
            return

        firma = firma_bilgisi_getir()
        tarih = datetime.now().strftime("%d.%m.%Y %H:%M")

        konu = "Cari Takip Veritabanı Yedeği"

        mesaj = (
            "Merhaba,\n\n"
            f"{firma['firma_adi']} Cari Takip veritabanı yedeği ektedir.\n\n"
            f"Tarih: {tarih}\n"
            f"Yedek Dosyası: {os.path.basename(yedek_yolu)}\n\n"
            "Not: Program yedek dosyasını hazırladı. "
            "Lütfen açılan yedekler klasöründen dosyayı Gmail'e ekleyip gönderin."
        )

        url = (
            "https://mail.google.com/mail/?view=cm&fs=1"
            f"&su={urllib.parse.quote(konu)}"
            f"&body={urllib.parse.quote(mesaj)}"
        )

        webbrowser.open(url)

        try:
            os.startfile(os.path.join(BASE_DIR, "yedekler"))
        except Exception:
            pass

        QMessageBox.information(
            self,
            "Gmail Hazır",
            f"Yedek oluşturuldu:\n{yedek_yolu}\n\n"
            "Gmail açıldı. Yedek dosyasını Gmail'e ekleyip gönderebilirsiniz."
        )
    def bulut_yedekleme_penceresi(self, embedded=False):
        pencere = QDialog(self)
        pencere.setWindowTitle("Bulut Yedekleme")
        pencere.resize(760, 520)
        pencere.setStyleSheet("background:#F8FAFC;")

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        ust = QFrame()
        ust.setObjectName("TopBar")
        ust_l = QVBoxLayout()
        ust_l.setContentsMargins(18, 14, 18, 14)
        baslik = QLabel("☁️ Yedekleme Merkezi")
        baslik.setStyleSheet("font-size:26px;font-weight:900;color:#0F172A;")
        aciklama = QLabel("Veritabanı yedeklerini güvenli şekilde oluşturabilir, klasörü açabilir veya Gmail gönderimi için hazırlayabilirsiniz.")
        aciklama.setWordWrap(True)
        aciklama.setStyleSheet("font-size:14px;color:#64748B;")
        ust_l.addWidget(baslik)
        ust_l.addWidget(aciklama)
        ust.setLayout(ust_l)
        layout.addWidget(ust)

        kart = QFrame()
        kart.setObjectName("MainCard")
        kart.setStyleSheet("background:white;border:1px solid #E2E8F0;border-radius:18px;")
        kart_l = QVBoxLayout()
        kart_l.setContentsMargins(18,18,18,18)
        kart_l.setSpacing(12)

        def big_btn(text, func, primary=False):
            b = QPushButton(text)
            b.setMinimumHeight(52)
            b.setObjectName("PrimaryButton" if primary else "")
            b.setStyleSheet("""
                QPushButton { border-radius:14px;padding:12px;font-size:15px;font-weight:900;text-align:left;background:#F8FAFC;color:#0F172A;border:1px solid #E2E8F0; }
                QPushButton:hover { background:#EEF2FF; }
                QPushButton#PrimaryButton { background:#4F46E5;color:white;border:none; }
                QPushButton#PrimaryButton:hover { background:#4338CA; }
            """)
            b.clicked.connect(func)
            kart_l.addWidget(b)
            return b

        big_btn("✅ Manuel Yedek Oluştur", self.manuel_yedek_olustur, True)
        big_btn("📂 Yedekler Klasörünü Aç", self.yedekler_klasorunu_ac)
        big_btn("✉️ Gmail'e Yedek Hazırla", self.gmail_yedek_hazirla)
        big_btn("♻️ Veritabanı Geri Yükle", self.veritabani_geri_yukle)

        not_lbl = QLabel("Not: Gmail şifreniz programa kaydedilmez. Program yedeği hazırlar; dosyayı e-postaya siz eklersiniz.")
        not_lbl.setWordWrap(True)
        not_lbl.setStyleSheet("background:#FEF3C7;border:1px solid #FDE68A;border-radius:14px;padding:12px;color:#92400E;font-weight:800;")
        kart_l.addWidget(not_lbl)
        kart_l.addStretch()
        kart.setLayout(kart_l)
        layout.addWidget(kart, 1)

        if not embedded:
            alt = QHBoxLayout()
            alt.addStretch()
            btnKapat = QPushButton("Kapat")
            btnKapat.clicked.connect(pencere.close)
            alt.addWidget(btnKapat)
            layout.addLayout(alt)

        pencere.setLayout(layout)
        if embedded:
            pencere.setWindowFlags(Qt.Widget)
            return pencere
        pencere.exec()
    def veritabani_geri_yukle(self):
        dosya_yolu, _ = QFileDialog.getOpenFileName(
            self,
            "Veritabanı Yedeği Seç",
            os.path.join(BASE_DIR, "yedekler"),
            "Veritabanı Dosyası (*.db)"
        )

        if not dosya_yolu:
            return

        if not veritabani_gecerli_mi(dosya_yolu):
            QMessageBox.warning(
                self,
                "Geçersiz Veritabanı",
                "Seçilen dosya Cari Takip veritabanı gibi görünmüyor.\n"
                "Geri yükleme iptal edildi."
            )
            return

        cevap = QMessageBox.question(
            self,
            "Geri Yükleme Onayı",
            "Seçilen yedek mevcut veritabanının yerine geçecek.\n"
            "Devam etmeden önce mevcut veritabanının ayrıca yedeği alınacak.\n\n"
            "Devam etmek istiyor musunuz?"
        )

        if cevap != QMessageBox.Yes:
            return

        try:
            os.makedirs(os.path.join(BASE_DIR, "yedekler"), exist_ok=True)

            kaynak = os.path.abspath(dosya_yolu)
            hedef_db = os.path.abspath(DB_ADI)
            if kaynak == hedef_db:
                QMessageBox.warning(self, "Hata", "Mevcut veritabanı dosyası geri yükleme kaynağı olarak seçilemez.")
                return

            tarih = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            if os.path.exists(DB_ADI):
                guvenlik_yedegi = os.path.join(BASE_DIR, "yedekler", f"geri_yukleme_oncesi_{tarih}.db")
                shutil.copy2(DB_ADI, guvenlik_yedegi)

            # Doğrudan ana DB üstüne yazmak yerine önce geçici dosyaya kopyala,
            # doğrula, sonra atomik replace yap. Kopyalama yarıda kalırsa ana DB korunur.
            gecici_db = os.path.join(BASE_DIR, f".restore_tmp_{tarih}.db")
            try:
                shutil.copy2(kaynak, gecici_db)
                if not veritabani_gecerli_mi(gecici_db):
                    raise RuntimeError("Geçici geri yükleme dosyası doğrulanamadı")
                os.replace(gecici_db, DB_ADI)
            finally:
                if os.path.exists(gecici_db):
                    try:
                        os.remove(gecici_db)
                    except Exception:
                        pass

            log_yaz(f"Veritabanı geri yüklendi: {os.path.basename(kaynak)}")

            QMessageBox.information(
                self,
                "Başarılı",
                "Veritabanı geri yüklendi.\n"
                "Değişikliklerin tam uygulanması için program şimdi kapanacak.\n"
                "Programı tekrar açın."
            )

            QApplication.quit()

        except Exception as hata:
            QMessageBox.warning(self, "Hata", f"Veritabanı geri yüklenemedi:\n{hata}")

