from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from moduller.db import baglan, db_baglan
from moduller.guvenlik import guclu_sifre_mi, sifre_dogrula
from moduller.loglama import log_yaz
from moduller.sistem import (
    firma_bilgisi_getir,
    kullanici_bilgisi_getir,
    kullanici_sifre_guncelle,
    master_sifre_dogrula,
    master_sifre_guncelle,
    oturum_zaman_asimi_getir,
    oturum_zaman_asimi_kaydet,
)
from moduller.ui_theme import apply_theme
from moduller.yetki import (
    AKSIYONLAR,
    EKRANLAR,
    kullanici_ekle,
    kullanici_guncelle,
    kullanici_sil,
    kullanicilari_listele,
    yetki_tablolari_olustur,
    yetkileri_getir,
    yetkileri_kaydet,
)


class AyarlarMixin:
    def tema_degistir(self, koyu=False):
        """Ayarlar ekranından tüm sekme ve pencerelere merkezi tema uygular."""
        self.koyu_tema_aktif = bool(koyu)
        apply_theme(self, self.koyu_tema_aktif)
        try:
            log_yaz("Tema değiştirildi: " + ("Karanlık" if koyu else "Açık"))
        except Exception:
            pass
    def firma_basliklarini_yenile(self):
        self.firma = firma_bilgisi_getir()
        self.lblFirmaAdi.setText(self.firma["firma_adi"])
        self.lblFirmaAltBilgi.setText(
            f'{self.firma["telefon"]}    •    {self.firma["adres"]}    •    {self.firma["vergi_no"]}'
        )
    def master_sifre_degistir_penceresi(self):
        pencere = QDialog(self)
        pencere.setWindowTitle("Ana Şifre Değiştir")
        pencere.resize(420, 320)

        layout = QVBoxLayout()

        baslik = QLabel("ANA ŞİFRE DEĞİŞTİR")
        baslik.setStyleSheet("font-size:22px;font-weight:800;padding:10px;")
        layout.addWidget(baslik)

        layout.addWidget(QLabel("Mevcut Ana Şifre"))
        txtEski = QLineEdit()
        txtEski.setEchoMode(QLineEdit.Password)
        layout.addWidget(txtEski)

        layout.addWidget(QLabel("Yeni Ana Şifre"))
        txtYeni = QLineEdit()
        txtYeni.setEchoMode(QLineEdit.Password)
        layout.addWidget(txtYeni)

        layout.addWidget(QLabel("Yeni Ana Şifre Tekrar"))
        txtTekrar = QLineEdit()
        txtTekrar.setEchoMode(QLineEdit.Password)
        layout.addWidget(txtTekrar)

        btnKaydet = QPushButton("Kaydet")
        layout.addWidget(btnKaydet)

        def kaydet():
            eski = txtEski.text().strip()
            yeni = txtYeni.text().strip()
            tekrar = txtTekrar.text().strip()

            if not master_sifre_dogrula(eski):
                QMessageBox.warning(pencere, "Hata", "Mevcut ana şifre yanlış.")
                return

            ok_sifre, mesaj = guclu_sifre_mi(yeni)
            if not ok_sifre or len(yeni) < 10:
                QMessageBox.warning(pencere, "Hata", mesaj or "Yeni ana şifre en az 10 karakter olmalı.")
                return

            if yeni != tekrar:
                QMessageBox.warning(pencere, "Hata", "Yeni ana şifreler aynı değil.")
                return

            master_sifre_guncelle(yeni)
            log_yaz("Ana şifre değiştirildi.")
            pencere.accept()

        btnKaydet.clicked.connect(kaydet)

        pencere.setLayout(layout)
        pencere.exec()
    def kullanici_adi_degistir_penceresi(self):
        pencere = QDialog(self)
        pencere.setWindowTitle("Kullanıcı Adı Değiştir")
        pencere.resize(420, 240)

        layout = QVBoxLayout()

        baslik = QLabel("KULLANICI ADI DEĞİŞTİR")
        baslik.setStyleSheet("font-size:22px;font-weight:800;padding:10px;")
        layout.addWidget(baslik)

        mevcut_kullanici, kayitli_sifre = kullanici_bilgisi_getir()

        layout.addWidget(QLabel("Yeni Kullanıcı Adı"))
        txtKullanici = QLineEdit()
        txtKullanici.setText(mevcut_kullanici)
        layout.addWidget(txtKullanici)

        layout.addWidget(QLabel("Mevcut Şifre"))
        txtSifre = QLineEdit()
        txtSifre.setEchoMode(QLineEdit.Password)
        layout.addWidget(txtSifre)

        btnKaydet = QPushButton("Kaydet")
        layout.addWidget(btnKaydet)

        def kaydet():
            yeni_kullanici = txtKullanici.text().strip()
            sifre = txtSifre.text().strip()

            if len(yeni_kullanici) < 3:
                QMessageBox.warning(pencere, "Hata", "Kullanıcı adı en az 3 karakter olmalı.")
                return

            if not sifre_dogrula(sifre, kayitli_sifre):
                QMessageBox.warning(pencere, "Hata", "Mevcut şifre yanlış.")
                return

            with db_baglan() as conn:
                cur = conn.cursor()
                cur.execute("UPDATE kullanicilar SET kullanici_adi=? WHERE id=1", (yeni_kullanici,))

            pencere.accept()

        btnKaydet.clicked.connect(kaydet)

        pencere.setLayout(layout)
        pencere.exec()
    def sifre_degistir_penceresi(self):
        pencere = QDialog(self)
        pencere.setWindowTitle("Şifre Değiştir")
        pencere.resize(420, 320)

        layout = QVBoxLayout()

        baslik = QLabel("ŞİFRE DEĞİŞTİR")
        baslik.setStyleSheet("font-size:22px;font-weight:800;padding:10px;")
        layout.addWidget(baslik)

        layout.addWidget(QLabel("Mevcut Şifre"))
        txtEski = QLineEdit()
        txtEski.setEchoMode(QLineEdit.Password)
        layout.addWidget(txtEski)

        layout.addWidget(QLabel("Yeni Şifre"))
        txtYeni = QLineEdit()
        txtYeni.setEchoMode(QLineEdit.Password)
        layout.addWidget(txtYeni)

        layout.addWidget(QLabel("Yeni Şifre Tekrar"))
        txtTekrar = QLineEdit()
        txtTekrar.setEchoMode(QLineEdit.Password)
        layout.addWidget(txtTekrar)

        btnKaydet = QPushButton("Kaydet")
        layout.addWidget(btnKaydet)

        def kaydet():
            _, kayitli_sifre = kullanici_bilgisi_getir()

            eski = txtEski.text().strip()
            yeni = txtYeni.text().strip()
            tekrar = txtTekrar.text().strip()

            if not sifre_dogrula(eski, kayitli_sifre):
                QMessageBox.warning(pencere, "Hata", "Mevcut şifre yanlış.")
                return

            ok_sifre, mesaj = guclu_sifre_mi(yeni)
            if not ok_sifre:
                QMessageBox.warning(pencere, "Hata", mesaj)
                return

            if yeni != tekrar:
                QMessageBox.warning(pencere, "Hata", "Yeni şifreler aynı değil.")
                return

            kullanici_sifre_guncelle(yeni)
            pencere.accept()

        btnKaydet.clicked.connect(kaydet)

        pencere.setLayout(layout)
        pencere.exec()

    def kullanici_yonetimi_penceresi(self):
        """v79: Modern kullanıcı, rol şablonu ve ekran bazlı yetki yönetimi."""
        yetki_tablolari_olustur()
        pencere = QDialog(self)
        pencere.setWindowTitle("Kullanıcı ve Yetki Yönetimi")
        pencere.resize(1320, 820)
        pencere.setMinimumSize(1120, 720)
        pencere.setStyleSheet("""
            QDialog { background:#F1F5F9; }
            QFrame#Panel { background:#FFFFFF; border:1px solid #E2E8F0; border-radius:18px; }
            QFrame#Hero { background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #2563EB, stop:1 #06B6D4); border-radius:22px; }
            QFrame#SoftCard { background:#F8FAFC; border:1px solid #E2E8F0; border-radius:12px; }
            QFrame#InfoCard { background:#EEF2FF; border:1px solid #C7D2FE; border-radius:12px; }
            QLabel#Title { font-size:28px; font-weight:800; color:#0F172A; }
            QLabel#HeroTitle { font-size:28px; font-weight:800; color:white; }
            QLabel#HeroSub { font-size:13px; color:#E0F2FE; }
            QLabel#Section { font-size:15px; font-weight:800; color:#334155; }
            QLabel#Muted { color:#64748B; font-size:12px; }
            QLabel#Avatar { background:#EEF2FF; color:#2563EB; border-radius:24px; font-size:24px; font-weight:800; padding:8px; }
            QLineEdit, QComboBox { min-height:38px; border:1px solid #CBD5E1; border-radius:12px; padding:6px 10px; background:#FFFFFF; }
            QTableWidget { background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; gridline-color:#E2E8F0; selection-background-color:#DBEAFE; selection-color:#0F172A; }
            QHeaderView::section { background:#F8FAFC; color:#334155; font-weight:800; border:0; border-bottom:1px solid #E2E8F0; padding:9px; }
            QPushButton { min-height:38px; border:1px solid #CBD5E1; border-radius:12px; padding:7px 12px; background:#FFFFFF; font-weight:800; color:#0F172A; }
            QPushButton:hover { background:#F8FAFC; }
            QPushButton#PrimaryButton { background:#2563EB; color:white; border:1px solid #2563EB; }
            QPushButton#DangerButton { background:#FEF2F2; color:#B91C1C; border:1px solid #FECACA; }
            QPushButton#TemplateButton { background:#EEF2FF; color:#3730A3; border:1px solid #C7D2FE; }
            QCheckBox { spacing:6px; font-weight:700; color:#334155; }
        """)

        ana = QVBoxLayout()
        ana.setContentsMargins(18, 18, 18, 18)
        ana.setSpacing(14)

        hero = QFrame()
        hero.setObjectName("Hero")
        hero_l = QHBoxLayout()
        hero_l.setContentsMargins(22, 16, 22, 16)
        hero_l.setSpacing(14)
        hero_text = QVBoxLayout()
        hero_text.setSpacing(4)
        h1 = QLabel("👥 Kullanıcı ve Yetki Merkezi")
        h1.setObjectName("HeroTitle")
        h2 = QLabel("Kullanıcı oluştur, rol şablonu uygula, menü ve işlem yetkilerini tek ekrandan yönet.")
        h2.setObjectName("HeroSub")
        hero_text.addWidget(h1)
        hero_text.addWidget(h2)
        hero_l.addLayout(hero_text, 1)
        lblOzet = QLabel("0 kullanıcı • 0 aktif")
        lblOzet.setStyleSheet("color:white;font-weight:800;background:rgba(255,255,255,0.18);border-radius:12px;padding:10px 14px;")
        hero_l.addWidget(lblOzet)
        hero.setLayout(hero_l)
        ana.addWidget(hero)

        govde = QHBoxLayout()
        govde.setSpacing(14)

        sol = QFrame()
        sol.setObjectName("Panel")
        sol_l = QVBoxLayout()
        sol_l.setContentsMargins(14, 14, 14, 14)
        sol_l.setSpacing(10)
        s_title = QLabel("Kullanıcılar")
        s_title.setObjectName("Section")
        txtAra = QLineEdit()
        txtAra.setPlaceholderText("🔎 Kullanıcı ara...")
        tbl = QTableWidget()
        tbl.setColumnCount(4)
        tbl.setHorizontalHeaderLabels(["ID", "Kullanıcı", "Rol", "Durum"])
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        tbl.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        tbl.setSelectionBehavior(QTableWidget.SelectRows)
        tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        tbl.verticalHeader().setVisible(False)
        sol_l.addWidget(s_title)
        sol_l.addWidget(txtAra)
        sol_l.addWidget(tbl, 1)
        sol.setLayout(sol_l)
        govde.addWidget(sol, 34)

        orta = QFrame()
        orta.setObjectName("Panel")
        orta_l = QVBoxLayout()
        orta_l.setContentsMargins(16, 16, 16, 16)
        orta_l.setSpacing(10)
        profil_baslik = QHBoxLayout()
        lblAvatar = QLabel("A")
        lblAvatar.setObjectName("Avatar")
        lblAvatar.setAlignment(Qt.AlignCenter)
        lblAvatar.setFixedSize(56, 56)
        profil_yazi = QVBoxLayout()
        lblProfil = QLabel("Kullanıcı Profili")
        lblProfil.setObjectName("Section")
        lblProfilAlt = QLabel("Seçili kullanıcının hesabını düzenle")
        lblProfilAlt.setObjectName("Muted")
        profil_yazi.addWidget(lblProfil)
        profil_yazi.addWidget(lblProfilAlt)
        profil_baslik.addWidget(lblAvatar)
        profil_baslik.addLayout(profil_yazi, 1)
        orta_l.addLayout(profil_baslik)

        orta_l.addWidget(QLabel("Kullanıcı Adı"))
        txtKullanici = QLineEdit()
        txtKullanici.setPlaceholderText("ornek: satis1")
        orta_l.addWidget(txtKullanici)
        orta_l.addWidget(QLabel("Yeni Şifre / Şifre Değiştir"))
        txtSifre = QLineEdit()
        txtSifre.setEchoMode(QLineEdit.Password)
        txtSifre.setPlaceholderText("Boş bırakırsan mevcut şifre korunur")
        orta_l.addWidget(txtSifre)
        orta_l.addWidget(QLabel("Rol"))
        cmbRol = QComboBox()
        cmbRol.addItems(["Yönetici", "Muhasebe", "Satış", "Depo", "Personel"])
        orta_l.addWidget(cmbRol)
        chkAktif = QCheckBox("Aktif kullanıcı")
        chkAktif.setChecked(True)
        orta_l.addWidget(chkAktif)

        rolBilgi = QLabel("Yönetici: tüm ekranları kullanır. Muhasebe: cari, tahsilat, kasa ve rapor. Satış: cari, satış ve teklif. Depo: stok ve alış.")
        rolBilgi.setObjectName("Muted")
        rolBilgi.setWordWrap(True)
        orta_l.addWidget(rolBilgi)

        btnYeni = QPushButton("✨ Yeni Kullanıcı Formu")
        btnEkle = QPushButton("➕ Kullanıcı Ekle")
        btnEkle.setObjectName("PrimaryButton")
        btnGuncelle = QPushButton("💾 Seçileni Güncelle")
        btnSil = QPushButton("🗑️ Seçileni Sil")
        btnSil.setObjectName("DangerButton")
        orta_l.addWidget(btnYeni)
        orta_l.addWidget(btnEkle)
        orta_l.addWidget(btnGuncelle)
        orta_l.addWidget(btnSil)
        orta_l.addStretch()
        orta.setLayout(orta_l)
        govde.addWidget(orta, 30)

        sag = QFrame()
        sag.setObjectName("Panel")
        sag_l = QVBoxLayout()
        sag_l.setContentsMargins(16, 16, 16, 16)
        sag_l.setSpacing(10)
        y_title = QLabel("Yetki Şablonları")
        y_title.setObjectName("Section")
        y_info = QLabel("Şablon uygula, sonra detayları alttaki yetki tablosundan ince ayarla.")
        y_info.setObjectName("Muted")
        y_info.setWordWrap(True)
        sag_l.addWidget(y_title)
        sag_l.addWidget(y_info)

        btnTplYonetici = QPushButton("🛡 Yönetici")
        btnTplMuhasebe = QPushButton("💰 Muhasebe")
        btnTplSatis = QPushButton("🛒 Satış")
        btnTplDepo = QPushButton("📦 Depo")
        btnTplPersonel = QPushButton("👤 Sadece Görüntüleme")
        for b in (btnTplYonetici, btnTplMuhasebe, btnTplSatis, btnTplDepo, btnTplPersonel):
            b.setObjectName("TemplateButton")
            sag_l.addWidget(b)

        onizleme = QFrame()
        onizleme.setObjectName("InfoCard")
        on_l = QVBoxLayout()
        on_l.setContentsMargins(12, 12, 12, 12)
        on_l.addWidget(QLabel("Yetki Önizleme"))
        lblOnizleme = QLabel("Kullanıcı seçildiğinde açık ekran sayısı burada görünür.")
        lblOnizleme.setObjectName("Muted")
        lblOnizleme.setWordWrap(True)
        on_l.addWidget(lblOnizleme)
        onizleme.setLayout(on_l)
        sag_l.addWidget(onizleme)
        sag_l.addStretch()
        sag.setLayout(sag_l)
        govde.addWidget(sag, 26)

        ana.addLayout(govde, 3)

        alt_panel = QFrame()
        alt_panel.setObjectName("Panel")
        alt_l = QVBoxLayout()
        alt_l.setContentsMargins(14, 14, 14, 14)
        alt_l.setSpacing(10)
        yetkiBaslik = QHBoxLayout()
        yb = QLabel("Ekran ve İşlem Yetkileri")
        yb.setObjectName("Section")
        yetkiBaslik.addWidget(yb)
        yetkiBaslik.addStretch()
        btnTumunuAc = QPushButton("Hepsini Aç")
        btnTumunuKapat = QPushButton("Hepsini Kapat")
        yetkiBaslik.addWidget(btnTumunuAc)
        yetkiBaslik.addWidget(btnTumunuKapat)
        alt_l.addLayout(yetkiBaslik)

        tblYetki = QTableWidget()
        tblYetki.setColumnCount(5)
        tblYetki.setHorizontalHeaderLabels(["Ekran", "Görür", "Ekler", "Düzenler", "Siler"])
        tblYetki.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for c in range(1, 5):
            tblYetki.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)
        tblYetki.verticalHeader().setVisible(False)
        alt_l.addWidget(tblYetki, 1)

        alt_buton = QHBoxLayout()
        btnYetkiKaydet = QPushButton("✅ Yetkileri Kaydet")
        btnYetkiKaydet.setObjectName("PrimaryButton")
        btnKapat = QPushButton("Kapat")
        alt_buton.addStretch()
        alt_buton.addWidget(btnYetkiKaydet)
        alt_buton.addWidget(btnKapat)
        alt_l.addLayout(alt_buton)
        alt_panel.setLayout(alt_l)
        ana.addWidget(alt_panel, 2)

        secili_id = {"id": None}
        tum_kullanicilar = {"rows": []}

        def secili_kullanici_id():
            row = tbl.currentRow()
            if row < 0 or not tbl.item(row, 0):
                return None
            try:
                return int(tbl.item(row, 0).text())
            except Exception:
                return None

        def durum_etiketi(aktif):
            return "✅ Aktif" if aktif else "⛔ Pasif"

        def kullanicilari_yukle(filtre=""):
            rows = kullanicilari_listele()
            tum_kullanicilar["rows"] = rows
            filtre = str(filtre or "").lower().strip()
            if filtre:
                rows = [r for r in rows if filtre in str(r[1]).lower() or filtre in str(r[2]).lower()]
            tbl.setRowCount(len(rows))
            for r, (kid, kadi, rol, aktif) in enumerate(rows):
                vals = [kid, kadi, rol, durum_etiketi(aktif)]
                for c, val in enumerate(vals):
                    item = QTableWidgetItem(str(val))
                    if c == 0:
                        item.setTextAlignment(Qt.AlignCenter)
                    tbl.setItem(r, c, item)
            aktif_sayi = sum(1 for _, _, _, aktif in tum_kullanicilar["rows"] if aktif)
            lblOzet.setText(f"{len(tum_kullanicilar['rows'])} kullanıcı • {aktif_sayi} aktif")
            if rows and tbl.currentRow() < 0:
                tbl.selectRow(0)
                kullanici_secildi()
            elif not rows:
                yeni_form()

        def yetki_tablosu_yukle(kid):
            secili_id["id"] = kid
            yetkiler = yetkileri_getir(kid) if kid else {ekran: {a: 0 for a in AKSIYONLAR} for ekran, _ in EKRANLAR}
            tblYetki.setRowCount(len(EKRANLAR))
            for r, (ekran, ad) in enumerate(EKRANLAR):
                item = QTableWidgetItem(ad)
                item.setData(Qt.UserRole, ekran)
                tblYetki.setItem(r, 0, item)
                for c, aksiyon in enumerate(AKSIYONLAR, start=1):
                    chk = QCheckBox()
                    chk.setChecked(bool(yetkiler.get(ekran, {}).get(aksiyon, 0)))
                    chk.stateChanged.connect(onizleme_guncelle)
                    tblYetki.setCellWidget(r, c, chk)
            onizleme_guncelle()

        def onizleme_guncelle():
            toplam = tblYetki.rowCount()
            gorur = ekler = duz = siler = 0
            for r in range(toplam):
                vals = []
                for c in range(1, 5):
                    w = tblYetki.cellWidget(r, c)
                    vals.append(bool(w and w.isChecked()))
                if vals[0]:
                    gorur += 1
                if vals[1]:
                    ekler += 1
                if vals[2]:
                    duz += 1
                if vals[3]:
                    siler += 1
            lblOnizleme.setText(f"Açık ekran: {gorur}/{toplam}\nEkleme: {ekler} • Düzenleme: {duz} • Silme: {siler}")

        def kullanici_secildi():
            row = tbl.currentRow()
            if row < 0:
                return
            kid = secili_kullanici_id()
            kadi = tbl.item(row, 1).text()
            txtKullanici.setText(kadi)
            txtKullanici.setReadOnly(True)
            lblAvatar.setText((kadi[:1] or "K").upper())
            rol = tbl.item(row, 2).text()
            idx = cmbRol.findText(rol)
            cmbRol.setCurrentIndex(idx if idx >= 0 else 4)
            chkAktif.setChecked("Aktif" in tbl.item(row, 3).text())
            txtSifre.clear()
            yetki_tablosu_yukle(kid)

        def yeni_form():
            secili_id["id"] = None
            tbl.clearSelection()
            txtKullanici.setReadOnly(False)
            txtKullanici.clear()
            txtSifre.clear()
            cmbRol.setCurrentText("Personel")
            chkAktif.setChecked(True)
            lblAvatar.setText("+")
            yetki_tablosu_yukle(None)

        def tablo_yetkilerini_al():
            data = {}
            for r in range(tblYetki.rowCount()):
                ekran = tblYetki.item(r, 0).data(Qt.UserRole)
                data[ekran] = {}
                for c, aksiyon in enumerate(AKSIYONLAR, start=1):
                    w = tblYetki.cellWidget(r, c)
                    data[ekran][aksiyon] = 1 if w and w.isChecked() else 0
            return data

        def yetki_kutularini_ayarla(kural):
            for r in range(tblYetki.rowCount()):
                ekran = tblYetki.item(r, 0).data(Qt.UserRole)
                vals = kural(ekran)
                for c, val in enumerate(vals, start=1):
                    w = tblYetki.cellWidget(r, c)
                    if w:
                        w.setChecked(bool(val))
            onizleme_guncelle()

        def sablon_yonetici():
            cmbRol.setCurrentText("Yönetici")
            yetki_kutularini_ayarla(lambda e: (1, 1, 1, 1))

        def sablon_muhasebe():
            cmbRol.setCurrentText("Muhasebe")
            tam = {"dashboard", "cari", "tahsilat", "kasa", "raporlar", "kar_zarar"}
            gor = tam | {"teklifler"}
            yetki_kutularini_ayarla(lambda e: (e in gor, e in tam, e in tam, e in {"tahsilat", "kasa"}))

        def sablon_satis():
            cmbRol.setCurrentText("Satış")
            tam = {"dashboard", "cari", "satis", "barkotlu_satis", "teklifler", "siparis"}
            yetki_kutularini_ayarla(lambda e: (e in tam or e == "raporlar", e in tam, e in tam, e in {"teklifler", "siparis"}))

        def sablon_depo():
            cmbRol.setCurrentText("Depo")
            tam = {"dashboard", "stok", "alis", "satin_alma"}
            yetki_kutularini_ayarla(lambda e: (e in tam or e == "raporlar", e in tam, e in tam, e in {"stok", "alis"}))

        def sablon_personel():
            cmbRol.setCurrentText("Personel")
            gor = {"dashboard", "cari", "satis", "tahsilat", "stok", "raporlar"}
            yetki_kutularini_ayarla(lambda e: (e in gor, 0, 0, 0))

        def ekle():
            try:
                kullanici_ekle(txtKullanici.text().strip(), txtSifre.text().strip(), cmbRol.currentText(), chkAktif.isChecked())
                rows = kullanicilari_listele()
                yeni_id = None
                for kid, kadi, _, _ in rows:
                    if kadi == txtKullanici.text().strip():
                        yeni_id = kid
                        break
                if yeni_id:
                    yetkileri_kaydet(yeni_id, tablo_yetkilerini_al())
                txtKullanici.setReadOnly(False)
                kullanicilari_yukle(txtAra.text())
                QMessageBox.information(pencere, "Başarılı", "Kullanıcı eklendi ve yetkileri kaydedildi.")
            except Exception as hata:
                QMessageBox.warning(pencere, "Hata", str(hata))

        def guncelle():
            kid = secili_kullanici_id() or secili_id.get("id")
            if not kid:
                QMessageBox.warning(pencere, "Hata", "Önce kullanıcı seç.")
                return
            try:
                kullanici_guncelle(kid, cmbRol.currentText(), chkAktif.isChecked(), txtSifre.text().strip() or None)
                txtSifre.clear()
                kullanicilari_yukle(txtAra.text())
                QMessageBox.information(pencere, "Başarılı", "Kullanıcı güncellendi.")
            except Exception as hata:
                QMessageBox.warning(pencere, "Hata", str(hata))

        def sil():
            kid = secili_kullanici_id()
            if not kid:
                return
            ad = txtKullanici.text().strip() or "seçili kullanıcı"
            if QMessageBox.question(pencere, "Silme Onayı", f"{ad} kullanıcısı silinsin mi?\nBu işlem geri alınamaz.") != QMessageBox.Yes:
                return
            try:
                kullanici_sil(kid)
                yeni_form()
                kullanicilari_yukle(txtAra.text())
            except Exception as hata:
                QMessageBox.warning(pencere, "Hata", str(hata))

        def yetki_kaydet():
            kid = secili_id.get("id") or secili_kullanici_id()
            if not kid:
                QMessageBox.warning(pencere, "Hata", "Önce kullanıcı seç.")
                return
            yetkileri_kaydet(kid, tablo_yetkilerini_al())
            QMessageBox.information(pencere, "Kaydedildi", "Yetkiler kaydedildi. Menü görünürlüğü yeni girişte tam yansır.")

        def tumu(deger):
            yetki_kutularini_ayarla(lambda e: (deger, deger, deger, deger))

        txtAra.textChanged.connect(kullanicilari_yukle)
        tbl.itemSelectionChanged.connect(kullanici_secildi)
        btnYeni.clicked.connect(yeni_form)
        btnEkle.clicked.connect(ekle)
        btnGuncelle.clicked.connect(guncelle)
        btnSil.clicked.connect(sil)
        btnYetkiKaydet.clicked.connect(yetki_kaydet)
        btnTumunuAc.clicked.connect(lambda: tumu(True))
        btnTumunuKapat.clicked.connect(lambda: tumu(False))
        btnKapat.clicked.connect(pencere.accept)
        btnTplYonetici.clicked.connect(sablon_yonetici)
        btnTplMuhasebe.clicked.connect(sablon_muhasebe)
        btnTplSatis.clicked.connect(sablon_satis)
        btnTplDepo.clicked.connect(sablon_depo)
        btnTplPersonel.clicked.connect(sablon_personel)

        pencere.setLayout(ana)
        kullanicilari_yukle()
        pencere.exec()

    def firma_ayarlari_penceresi(self, embedded=False):
        """v60: Ayarlar ekranı scroll + responsive kart düzeni."""
        firma = firma_bilgisi_getir()

        pencere = QDialog(self)
        pencere.setWindowTitle("Firma Ayarları")
        pencere.resize(900, 700)

        ana = QVBoxLayout()
        ana.setContentsMargins(14, 14, 14, 14)
        ana.setSpacing(12)

        baslik = QLabel("⚙️ Firma Ayarları")
        baslik.setStyleSheet("font-size:26px;font-weight:800;color:#0F172A;padding:4px;")
        ana.addWidget(baslik)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        panel = QFrame()
        panel.setObjectName("MainCard")
        panel_l = QVBoxLayout()
        panel_l.setContentsMargins(16, 16, 16, 16)
        panel_l.setSpacing(12)

        form = QGridLayout()
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        def label(text):
            label_widget = QLabel(text)
            label_widget.setStyleSheet("font-weight:800;color:#334155;")
            return label_widget

        txtFirmaAdi = QLineEdit()
        txtFirmaAdi.setText(firma["firma_adi"])
        txtTelefon = QLineEdit()
        txtTelefon.setText(firma["telefon"])
        txtVergiNo = QLineEdit()
        txtVergiNo.setText(firma["vergi_no"])
        txtVergiDairesi = QLineEdit()
        txtVergiDairesi.setText(firma["vergi_dairesi"])
        txtEposta = QLineEdit()
        txtEposta.setText(firma["eposta"])
        txtAdres = QTextEdit()
        txtAdres.setPlainText(firma["adres"])
        txtAdres.setMinimumHeight(80)

        cmbOturum = QComboBox()
        cmbOturum.addItem("Hiçbir zaman", 0)
        cmbOturum.addItem("5 dakika", 5)
        cmbOturum.addItem("10 dakika", 10)
        cmbOturum.addItem("15 dakika", 15)
        cmbOturum.addItem("30 dakika", 30)
        mevcut_timeout = oturum_zaman_asimi_getir()
        for i in range(cmbOturum.count()):
            if cmbOturum.itemData(i) == mevcut_timeout:
                cmbOturum.setCurrentIndex(i)
                break

        alanlar = [
            ("Firma Adı", txtFirmaAdi),
            ("Telefon", txtTelefon),
            ("Vergi No", txtVergiNo),
            ("Vergi Dairesi", txtVergiDairesi),
            ("E-Posta", txtEposta),
            ("Oturum Zaman Aşımı", cmbOturum),
        ]
        for i, (ad, widget) in enumerate(alanlar):
            r, c = divmod(i, 2)
            form.addWidget(label(ad), r * 2, c)
            form.addWidget(widget, r * 2 + 1, c)

        panel_l.addLayout(form)
        panel_l.addWidget(label("Adres"))
        panel_l.addWidget(txtAdres)

        guvenlik = QFrame()
        guvenlik.setStyleSheet("background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;")
        guvenlik_l = QVBoxLayout()
        guvenlik_l.setContentsMargins(14, 14, 14, 14)
        guvenlik_l.setSpacing(10)
        guvenlik_l.addWidget(label("Güvenlik ve Sistem"))

        btnKullaniciYonetimi = QPushButton("👥 Kullanıcı ve Yetki Yönetimi")
        btnKullaniciYonetimi.clicked.connect(self.kullanici_yonetimi_penceresi)
        btnKullanici = QPushButton("👤 Kullanıcı Adı Değiştir")
        btnKullanici.clicked.connect(self.kullanici_adi_degistir_penceresi)
        btnSifre = QPushButton("🔑 Şifre Değiştir")
        btnSifre.clicked.connect(self.sifre_degistir_penceresi)
        btnMaster = QPushButton("🛡️ Ana Şifre Değiştir")
        btnMaster.clicked.connect(self.master_sifre_degistir_penceresi)
        btnGeriYukle = QPushButton("♻️ Veritabanı Geri Yükle")
        btnGeriYukle.clicked.connect(self.veritabani_geri_yukle)
        btnBulut = QPushButton("☁️ Bulut Yedekleme")
        btnBulut.clicked.connect(self.bulut_yedekleme_penceresi)

        buton_grid = QGridLayout()
        butonlar = [btnKullaniciYonetimi, btnKullanici, btnSifre, btnMaster, btnGeriYukle, btnBulut]
        for i, b in enumerate(butonlar):
            b.setMinimumHeight(42)
            buton_grid.addWidget(b, i // 2, i % 2)
        guvenlik_l.addLayout(buton_grid)
        guvenlik.setLayout(guvenlik_l)
        panel_l.addWidget(guvenlik)

        tema = QFrame()
        tema.setObjectName("ThemePanel")
        tema_l = QHBoxLayout()
        tema_l.setContentsMargins(14, 10, 14, 10)
        tema_l.setSpacing(10)
        tema_baslik = label("Tema")
        tema_baslik.setObjectName("ThemePanelTitle")
        tema_l.addWidget(tema_baslik)
        tema_l.addStretch()
        btnAcikTema = QPushButton("☀️  Açık")
        btnAcikTema.setObjectName("ThemeChoiceButton")
        btnAcikTema.setMinimumWidth(120)
        btnAcikTema.clicked.connect(lambda: self.tema_degistir(False))
        try:
            btnAcikTema.setEnabled(bool(getattr(self, "koyu_tema_aktif", False)))
        except Exception:
            pass
        tema_l.addWidget(btnAcikTema)
        btnKoyuTema = QPushButton("🌙  Koyu")
        btnKoyuTema.setObjectName("ThemeChoiceButton")
        btnKoyuTema.setMinimumWidth(120)
        btnKoyuTema.clicked.connect(lambda: self.tema_degistir(True))
        try:
            btnKoyuTema.setEnabled(not bool(getattr(self, "koyu_tema_aktif", False)))
        except Exception:
            pass
        tema_l.addWidget(btnKoyuTema)
        tema.setLayout(tema_l)
        panel_l.addWidget(tema)

        panel.setLayout(panel_l)
        scroll.setWidget(panel)
        ana.addWidget(scroll, 1)

        alt = QHBoxLayout()
        alt.addStretch()
        btnKaydet = QPushButton("✅ Kaydet")
        btnKaydet.setObjectName("PrimaryButton")
        btnKaydet.setMinimumWidth(160)
        btnKaydet.setMinimumHeight(44)
        alt.addWidget(btnKaydet)
        ana.addLayout(alt)

        def kaydet():
            conn = baglan()
            cur = conn.cursor()
            cur.execute("""
                UPDATE firma_ayarlari
                SET firma_adi=?, telefon=?, adres=?, vergi_no=?, vergi_dairesi=?, eposta=?
                WHERE id=1
            """, (
                txtFirmaAdi.text().strip(),
                txtTelefon.text().strip(),
                txtAdres.toPlainText().strip(),
                txtVergiNo.text().strip(),
                txtVergiDairesi.text().strip(),
                txtEposta.text().strip()
            ))
            conn.commit()
            conn.close()
            oturum_zaman_asimi_kaydet(cmbOturum.currentData())
            log_yaz(f"Firma ayarları güncellendi. Oturum zaman aşımı: {cmbOturum.currentText()}")
            self.firma_basliklarini_yenile()
            if embedded:
                QMessageBox.information(self, "Kaydedildi", "Firma ayarları güncellendi.")
            else:
                pencere.accept()

        btnKaydet.clicked.connect(kaydet)

        pencere.setLayout(ana)
        if embedded:
            pencere.setWindowFlags(Qt.Widget)
            return pencere
        pencere.exec()

