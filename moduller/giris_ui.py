import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core.config import (
    GIRIS_KILIT_SANIYE,
    GIRIS_MAKS_DENEME,
    PROGRAM_SERI_NO,
    RESET_KODU_GECERLILIK_DAKIKA,
)
from moduller.erp_ek_moduller import audit_yaz
from moduller.guvenlik import guclu_sifre_mi, kullanici_sifre_hash_mi, sifre_dogrula
from moduller.loglama import log_yaz
from moduller.reset_kodu import mevcut_program_seri_no, reset_kodu_dogrula
from moduller.sistem import kullanici_bilgisi_getir, kullanici_sifre_guncelle
from moduller.yetki import aktif_kullanici_ayarla, kullanici_giris_bilgisi_getir


def giris_penceresi():
    pencere = QDialog()
    pencere.setWindowTitle("DAL ERP - Güvenli Giriş")
    pencere.resize(960, 585)
    pencere.setMinimumSize(760, 500)
    pencere.setStyleSheet("""
        QDialog {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #EEF2FF, stop:0.50 #F8FAFC, stop:1 #ECFEFF);
            font-family: Segoe UI;
        }
        QFrame#LoginShell {
            background: rgba(255, 255, 255, 245);
            border: 1px solid #E2E8F0;
            border-radius: 28px;
        }
        QFrame#BrandPanel {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #4F46E5, stop:0.55 #2563EB, stop:1 #06B6D4);
            border-radius: 24px;
        }
        QLabel#BrandTitle { color: white; font-size: 32px; font-weight: 900; }
        QLabel#BrandSub { color: #DBEAFE; font-size: 14px; line-height: 150%; }
        QLabel#Edition { color: #E0F2FE; font-size: 13px; font-weight: 800; }
        QLabel#FeatureCard { background: rgba(255,255,255,32); border: 1px solid rgba(255,255,255,58); border-radius: 16px; padding: 10px 12px; color: white; font-size: 13px; font-weight: 800; }
        QLabel#Badge {
            color: white; background: rgba(255,255,255,40); border: 1px solid rgba(255,255,255,70);
            border-radius: 14px; padding: 8px 12px; font-size: 12px; font-weight: 800;
        }
        QLabel#FormTitle { color: #0F172A; font-size: 29px; font-weight: 900; }
        QLabel#FormSub, QLabel#SmallText { color: #64748B; font-size: 13px; }
        QLabel#FieldLabel { color: #334155; font-size: 13px; font-weight: 800; }
        QLineEdit {
            background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 14px;
            padding: 13px 14px; color: #0F172A; font-size: 14px;
        }
        QLineEdit:focus { background: white; border: 2px solid #4F46E5; }
        QPushButton {
            border-radius: 14px; padding: 12px 16px; font-size: 14px; font-weight: 900;
            text-align: center;
        }
        QPushButton#LoginPrimary { background: #4F46E5; color: white; border: none; }
        QPushButton#LoginPrimary:hover { background: #4338CA; }
        QPushButton#LoginSecondary { background: transparent; color: #4F46E5; border: none; padding: 6px; }
        QPushButton#LoginSecondary:hover { color: #312E81; text-decoration: underline; }
        QCheckBox { color: #475569; font-size: 13px; }
    """)

    ana = QVBoxLayout(pencere)
    ana.setContentsMargins(28, 28, 28, 28)
    ana.setSpacing(0)

    shell = QFrame()
    shell.setObjectName("LoginShell")
    ana.addWidget(shell)

    govde = QHBoxLayout(shell)
    govde.setContentsMargins(18, 18, 18, 18)
    govde.setSpacing(22)

    brand = QFrame()
    brand.setObjectName("BrandPanel")
    brand.setMinimumWidth(350)
    brand_layout = QVBoxLayout(brand)
    brand_layout.setContentsMargins(30, 34, 30, 30)
    brand_layout.setSpacing(16)

    badge = QLabel("🔐 GÜVENLİ OTURUM")
    badge.setObjectName("Badge")
    badge.setAlignment(Qt.AlignCenter)
    badge.setFixedWidth(165)
    brand_layout.addWidget(badge, 0, Qt.AlignLeft)

    marka = QLabel("DAL ERP NEXT")
    marka.setObjectName("BrandTitle")
    brand_layout.addWidget(marka)

    edition = QLabel("Professional Edition")
    edition.setObjectName("Edition")
    brand_layout.addWidget(edition)

    aciklama = QLabel("İşletmenizi tek ekrandan yönetin: cari, stok, satış, kasa ve raporlar.")
    aciklama.setObjectName("BrandSub")
    aciklama.setWordWrap(True)
    brand_layout.addWidget(aciklama)
    brand_layout.addSpacing(12)

    ozellikler = ["🛡 Güvenli SQL işlemleri", "⚡ Hızlı veri işleme", "☁ Otomatik yedekleme", "📊 Canlı yönetim paneli"]
    for metin in ozellikler:
        lbl = QLabel(metin)
        lbl.setObjectName("FeatureCard")
        brand_layout.addWidget(lbl)
    brand_layout.addStretch()

    surum = QLabel("DAL ERP Next  •  v2 Professional")
    surum.setObjectName("Edition")
    surum.setAlignment(Qt.AlignLeft)
    brand_layout.addWidget(surum)

    form = QFrame()
    form_layout = QVBoxLayout(form)
    form_layout.setContentsMargins(34, 34, 34, 28)
    form_layout.setSpacing(12)

    baslik = QLabel("Hoş geldiniz")
    baslik.setObjectName("FormTitle")
    form_layout.addWidget(baslik)
    alt = QLabel("Devam etmek için kullanıcı bilgilerinizi girin.")
    alt.setObjectName("FormSub")
    form_layout.addWidget(alt)
    form_layout.addSpacing(18)

    lblKullanici = QLabel("Kullanıcı adı")
    lblKullanici.setObjectName("FieldLabel")
    form_layout.addWidget(lblKullanici)
    txtKullanici = QLineEdit()
    txtKullanici.setPlaceholderText("Kullanıcı adınız")
    kayitli_kullanici, _ = kullanici_bilgisi_getir()
    txtKullanici.setText(kayitli_kullanici)
    txtKullanici.setClearButtonEnabled(True)
    form_layout.addWidget(txtKullanici)

    lblSifre = QLabel("Şifre")
    lblSifre.setObjectName("FieldLabel")
    form_layout.addWidget(lblSifre)
    txtSifre = QLineEdit()
    txtSifre.setPlaceholderText("Şifrenizi girin")
    txtSifre.setEchoMode(QLineEdit.Password)
    txtSifre.setClearButtonEnabled(True)
    form_layout.addWidget(txtSifre)

    satir = QHBoxLayout()
    chkGoster = QCheckBox("Şifreyi göster")
    satir.addWidget(chkGoster)
    satir.addStretch()
    form_layout.addLayout(satir)

    btnGiris = QPushButton("Giriş Yap  →")
    btnGiris.setObjectName("LoginPrimary")
    btnGiris.setMinimumHeight(58)
    form_layout.addWidget(btnGiris)

    btnUnuttum = QPushButton("Şifremi Unuttum?")
    btnUnuttum.setObjectName("LoginSecondary")
    btnUnuttum.setMinimumHeight(32)
    form_layout.addWidget(btnUnuttum)
    form_layout.addStretch()

    guvenlik_notu = QLabel("Hatalı denemelerde oturum geçici olarak kilitlenir.")
    guvenlik_notu.setObjectName("SmallText")
    guvenlik_notu.setAlignment(Qt.AlignCenter)
    guvenlik_notu.setWordWrap(True)
    form_layout.addWidget(guvenlik_notu)

    govde.addWidget(brand, 1)
    govde.addWidget(form, 1)

    deneme = {"sayac": 0, "kilit_baslangic": 0}
    giris_kilit = {"aktif": False}

    def sifre_goster_durum(deger):
        txtSifre.setEchoMode(QLineEdit.Normal if deger else QLineEdit.Password)

    def zorunlu_sifre_degistir(eski_sifre):
        zayif = eski_sifre in ("1234", "admin", "password", "123456", "12345678") or len(eski_sifre) < 8
        if not zayif:
            ok_sifre, _ = guclu_sifre_mi(eski_sifre)
            zayif = not ok_sifre
        if not zayif:
            return True

        QMessageBox.information(
            pencere,
            "Güvenlik",
            "Varsayılan veya zayıf şifre kullanıyorsunuz. Devam etmek için yeni güçlü şifre belirleyin."
        )
        while True:
            yeni_sifre, ok = QInputDialog.getText(
                pencere,
                "Yeni Güçlü Şifre",
                "En az 8 karakter, harf ve rakam içeren yeni şifre:",
                QLineEdit.Password
            )
            if not ok:
                return False
            yeni_sifre = yeni_sifre.strip()
            uygun, mesaj = guclu_sifre_mi(yeni_sifre)
            if not uygun:
                QMessageBox.warning(pencere, "Hata", mesaj)
                continue
            if yeni_sifre == eski_sifre:
                QMessageBox.warning(pencere, "Hata", "Yeni şifre eski şifre ile aynı olamaz.")
                continue
            kullanici_sifre_guncelle(yeni_sifre)
            log_yaz("Zayıf/varsayılan kullanıcı şifresi değiştirildi.")
            return True

    def kontrol_et():
        # Aynı anda hem Enter hem buton tetiklenirse uyarı penceresi iki kez açılmasın.
        if giris_kilit.get("aktif"):
            return
        giris_kilit["aktif"] = True
        btnGiris.setEnabled(False)
        def _giris_serbest_birak(gecikme_ms=350):
            # Enter tuşu ve buton varsayılan davranışı aynı anda tetiklenirse
            # ikinci sinyali yutmak için kilidi kısa süre daha aktif tut.
            def _ac():
                giris_kilit["aktif"] = False
                btnGiris.setEnabled(True)
            QTimer.singleShot(gecikme_ms, _ac)

        simdi = time.time()
        if deneme["kilit_baslangic"] and simdi - deneme["kilit_baslangic"] < GIRIS_KILIT_SANIYE:
            kalan_saniye = int(GIRIS_KILIT_SANIYE - (simdi - deneme["kilit_baslangic"]))
            QMessageBox.warning(pencere, "Giriş Kilitli", f"Çok fazla hatalı giriş yapıldı.\n{kalan_saniye} saniye sonra tekrar deneyin.")
            _giris_serbest_birak()
            return

        kullanici = txtKullanici.text().strip()
        sifre = txtSifre.text().strip()
        kayit = kullanici_giris_bilgisi_getir(kullanici)
        kayitli_kullanici = kayit[1] if kayit else ""
        kayitli_sifre = kayit[2] if kayit else ""
        aktif = int(kayit[4] or 0) if kayit else 0

        if aktif and kullanici == kayitli_kullanici and sifre_dogrula(sifre, kayitli_sifre):
            if not kullanici_sifre_hash_mi(kayitli_sifre):
                kullanici_sifre_guncelle(sifre)
            if not zorunlu_sifre_degistir(sifre):
                _giris_serbest_birak()
                return
            aktif_kullanici_ayarla(kullanici)
            log_yaz(f"Kullanıcı girişi başarılı: {kullanici}")
            audit_yaz("kullanici_girisi", "kullanicilar", kayit[0] if kayit else 1, {"kullanici": kullanici}, kullanici=kullanici)
            pencere.accept()
        else:
            deneme["sayac"] += 1
            kalan = GIRIS_MAKS_DENEME - deneme["sayac"]
            if kalan <= 0:
                deneme["kilit_baslangic"] = time.time()
                deneme["sayac"] = 0
                log_yaz("Çoklu hatalı kullanıcı girişi nedeniyle kilit uygulandı.")
                QMessageBox.warning(pencere, "Giriş Kilitlendi", "Çok fazla hatalı giriş yapıldı. Lütfen daha sonra tekrar deneyin.")
                _giris_serbest_birak()
                return
            QMessageBox.warning(pencere, "Hatalı Giriş", f"Kullanıcı adı veya şifre yanlış.\nKalan deneme hakkı: {kalan}")
            _giris_serbest_birak()

    def sifremi_unuttum():
        try:
            seri_no = mevcut_program_seri_no()
        except Exception:
            seri_no = str(PROGRAM_SERI_NO)
        bilgi = (
            f"Bu programın seri numarası:\n{seri_no}\n\n"
            "001 yetkili programda bu seri numarasını yazarak reset kodu üretin.\n"
            f"Reset kodu yaklaşık {RESET_KODU_GECERLILIK_DAKIKA} dakika geçerlidir ve tek kullanımlıktır."
        )
        QMessageBox.information(pencere, "Şifre Sıfırlama", bilgi)
        reset_kodu, ok = QInputDialog.getText(
            pencere,
            "Reset Kodu",
            "001 yetkili programın ürettiği reset kodunu girin:",
            QLineEdit.Normal
        )
        if not ok:
            return
        gecerli, mesaj = reset_kodu_dogrula(reset_kodu, seri_no=seri_no, tuket=True)
        if not gecerli:
            QMessageBox.warning(pencere, "Hata", mesaj)
            return
        while True:
            yeni_sifre, ok = QInputDialog.getText(
                pencere,
                "Yeni Şifre",
                "Yeni giriş şifresini yazın:\nEn az 8 karakter, harf ve rakam içermelidir.",
                QLineEdit.Password
            )
            if not ok:
                return
            yeni_sifre = yeni_sifre.strip()
            uygun, mesaj = guclu_sifre_mi(yeni_sifre)
            if not uygun:
                QMessageBox.warning(pencere, "Hata", mesaj)
                continue
            kullanici_sifre_guncelle(yeni_sifre)
            txtSifre.clear()
            log_yaz(f"Kullanıcı şifresi reset kodu ile sıfırlandı. Seri No: {seri_no}")
            QMessageBox.information(pencere, "Başarılı", "Giriş şifresi reset kodu ile güncellendi.")
            return

    btnGiris.setAutoDefault(False)
    btnGiris.setDefault(False)
    btnUnuttum.setAutoDefault(False)
    btnUnuttum.setDefault(False)
    btnGiris.clicked.connect(kontrol_et)
    btnUnuttum.clicked.connect(sifremi_unuttum)
    chkGoster.toggled.connect(sifre_goster_durum)
    txtKullanici.returnPressed.connect(kontrol_et)
    txtSifre.returnPressed.connect(kontrol_et)
    txtSifre.setFocus()

    return pencere.exec() == QDialog.Accepted


