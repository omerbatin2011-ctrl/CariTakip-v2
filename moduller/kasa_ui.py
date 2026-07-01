from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QPageSize, QTextDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
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
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from moduller.db import db_baglan
from moduller.loglama import log_yaz
from moduller.sistem import firma_bilgisi_getir
from moduller.yardimci import para_yaz


def kasa_tablosu_olustur():
    """Kasa modülü için gerekli tabloyu güvenli şekilde oluşturur."""
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS kasa_hareketleri (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tarih TEXT,
                tip TEXT,
                odeme_tipi TEXT,
                tutar REAL,
                aciklama TEXT,
                kaynak TEXT,
                kaynak_id INTEGER,
                kullanici TEXT
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_kasa_hareketleri_tarih ON kasa_hareketleri(tarih)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_kasa_hareketleri_tip ON kasa_hareketleri(tip)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_kasa_hareketleri_kaynak ON kasa_hareketleri(kaynak, kaynak_id)")


def kasa_hareketi_ekle(tip, tutar, aciklama="", odeme_tipi="NAKİT", kaynak="MANUEL", kaynak_id=None, kullanici="admin", tarih=None):
    """Kasa hareketi ekler. tip: GIRIS veya CIKIS."""
    kasa_tablosu_olustur()
    tip = str(tip or "").upper().strip()
    if tip not in ("GIRIS", "CIKIS"):
        raise ValueError("Kasa tipi GIRIS veya CIKIS olmalı.")
    tutar = float(tutar or 0)
    if tutar <= 0:
        raise ValueError("Kasa tutarı 0'dan büyük olmalı.")
    tarih = tarih or datetime.now().strftime("%d.%m.%Y %H:%M")
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO kasa_hareketleri(tarih, tip, odeme_tipi, tutar, aciklama, kaynak, kaynak_id, kullanici)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (tarih, tip, odeme_tipi, tutar, aciklama, kaynak, kaynak_id, kullanici)
        )
        return cur.lastrowid


class KasaMixin:
    def kasa_sayfasi_olustur(self):
        kasa_tablosu_olustur()
        sayfa = QFrame()
        sayfa.setStyleSheet("""
            QFrame { background:#F8FAFC; }
            QFrame#Panel { background:#FFFFFF; border:1px solid #E2E8F0; border-radius:16px; }
            QLabel { color:#0F172A; background:transparent; }
            QLineEdit, QTextEdit, QComboBox {
                background:#FFFFFF; border:1px solid #E2E8F0; border-radius:10px; padding:8px 10px; font-size:13px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus { border:1px solid #2563EB; }
            QTableWidget { background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; gridline-color:#E5E7EB; font-size:13px; alternate-background-color:#F8FAFC; }
            QTableWidget::item { padding:8px; }
            QHeaderView::section { background:#F8FAFC; color:#334155; padding:9px; border:none; font-weight:800; }
            QPushButton { background:#FFFFFF; color:#0F172A; border:1px solid #CBD5E1; border-radius:10px; padding:9px 12px; font-weight:800; font-size:13px; }
            QPushButton:hover { background:#F8FAFC; border-color:#94A3B8; }
            QPushButton#PrimaryButton { background:#2563EB; color:white; border:none; }
            QPushButton#PrimaryButton:hover { background:#1D4ED8; }
            QPushButton#GreenButton { background:#FFFFFF; color:#047857; border:1px solid #A7F3D0; }
            QPushButton#GreenButton:hover { background:#ECFDF5; }
            QPushButton#RedButton { background:#FFFFFF; color:#B91C1C; border:1px solid #FECACA; }
            QPushButton#RedButton:hover { background:#FEF2F2; }
            QPushButton#OrangeButton { background:#FFFFFF; color:#C2410C; border:1px solid #FDBA74; }
            QPushButton#OrangeButton:hover { background:#FFF7ED; }
            QPushButton#GreyButton { background:#FFFFFF; color:#334155; border:1px solid #CBD5E1; }
            QPushButton#GreyButton:hover { background:#F8FAFC; }
        """)

        ana = QVBoxLayout(sayfa)
        ana.setContentsMargins(24, 20, 24, 20)
        ana.setSpacing(12)

        ust = QFrame()
        ust.setObjectName("Panel")
        ust_l = QHBoxLayout(ust)
        ust_l.setContentsMargins(16, 12, 16, 12)
        baslik_l = QVBoxLayout()
        baslik = QLabel("Kasa Modülü")
        baslik.setStyleSheet("font-size:26px;font-weight:900;color:#0F172A;")
        alt = QLabel("Nakit/kart girişleri, masraflar ve gün sonu raporu")
        alt.setStyleSheet("font-size:13px;color:#64748B;font-weight:700;")
        baslik_l.addWidget(baslik)
        baslik_l.addWidget(alt)
        ust_l.addLayout(baslik_l, 1)
        self.cmbKasaFiltre = QComboBox()
        self.cmbKasaFiltre.addItems(["Bugün", "Bu Hafta", "Bu Ay", "Tümü"])
        self.cmbKasaFiltre.currentTextChanged.connect(self.kasa_sayfa_yenile)
        ust_l.addWidget(QLabel("Filtre:"))
        ust_l.addWidget(self.cmbKasaFiltre)
        ana.addWidget(ust)

        kartlar = QGridLayout()
        kartlar.setSpacing(10)
        self.lblKasaNakit = self._kasa_kart(kartlar, 0, 0, "₺", "Nakit Kasa", "0,00 ₺")
        self.lblKasaKart = self._kasa_kart(kartlar, 0, 1, "▭", "Kart Tahsilat", "0,00 ₺")
        self.lblKasaGiris = self._kasa_kart(kartlar, 0, 2, "↓", "Dönem Giriş", "0,00 ₺")
        self.lblKasaCikis = self._kasa_kart(kartlar, 0, 3, "↑", "Dönem Çıkış", "0,00 ₺")
        ana.addLayout(kartlar)

        govde = QHBoxLayout()
        govde.setSpacing(12)
        ana.addLayout(govde, 1)

        sol = QFrame()
        sol.setObjectName("Panel")
        sol_l = QVBoxLayout(sol)
        sol_l.setContentsMargins(14, 14, 14, 14)
        sol_l.setSpacing(10)
        btn_l = QHBoxLayout()
        btnGiris = QPushButton("+ Para Girişi")
        btnGiris.setObjectName("GreenButton")
        btnCikis = QPushButton("− Para Çıkışı")
        btnCikis.setObjectName("RedButton")
        btnMasraf = QPushButton("Masraf Ekle")
        btnMasraf.setObjectName("OrangeButton")
        btnPersonel = QPushButton("Personel Ödemesi")
        btnPersonel.setObjectName("GreyButton")
        btnGunSonu = QPushButton("Gün Sonu")
        btnYazdir = QPushButton("Yazdır")
        for b in (btnGiris, btnCikis, btnMasraf, btnPersonel, btnGunSonu, btnYazdir):
            btn_l.addWidget(b)
        sol_l.addLayout(btn_l)

        self.tblKasa = QTableWidget()
        self.tblKasa.setColumnCount(8)
        self.tblKasa.setHorizontalHeaderLabels(["ID", "Tarih", "Tip", "Ödeme", "Tutar", "Açıklama", "Kaynak", "Kullanıcı"])
        self.tblKasa.setColumnHidden(0, True)
        self.tblKasa.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tblKasa.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tblKasa.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tblKasa.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tblKasa.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.tblKasa.setSelectionBehavior(QTableWidget.SelectRows)
        self.tblKasa.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tblKasa.verticalHeader().setVisible(False)
        self.tblKasa.setAlternatingRowColors(True)
        sol_l.addWidget(self.tblKasa, 1)
        govde.addWidget(sol, 4)

        sag = QFrame()
        sag.setObjectName("Panel")
        sag_l = QVBoxLayout(sag)
        sag_l.setContentsMargins(14, 14, 14, 14)
        sag_l.setSpacing(10)
        self.lblKasaNet = QLabel("Net Kasa\n0,00 ₺")
        self.lblKasaNet.setAlignment(Qt.AlignCenter)
        self.lblKasaNet.setWordWrap(True)
        self.lblKasaNet.setStyleSheet("font-size:24px;font-weight:900;color:#047857;background:#ECFDF5;border:1px solid #A7F3D0;border-radius:16px;padding:18px;")
        sag_l.addWidget(self.lblKasaNet)
        self.lblKasaOzet = QLabel("Gün sonu için filtreyi Bugün seçin.")
        self.lblKasaOzet.setWordWrap(True)
        self.lblKasaOzet.setStyleSheet("font-size:13px;color:#475569;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:12px;")
        sag_l.addWidget(self.lblKasaOzet)
        sag_l.addStretch()
        govde.addWidget(sag, 1)

        btnGiris.clicked.connect(lambda: self.kasa_hareket_dialog("GIRIS", "NAKİT", "Para girişi"))
        btnCikis.clicked.connect(lambda: self.kasa_hareket_dialog("CIKIS", "NAKİT", "Para çıkışı"))
        btnMasraf.clicked.connect(lambda: self.kasa_hareket_dialog("CIKIS", "NAKİT", "Masraf"))
        btnPersonel.clicked.connect(lambda: self.kasa_hareket_dialog("CIKIS", "NAKİT", "Personel ödemesi"))
        btnGunSonu.clicked.connect(self.kasa_gun_sonu_raporu)
        btnYazdir.clicked.connect(self.kasa_gun_sonu_yazdir)

        self.kasa_sayfa_yenile()
        return sayfa

    def _kasa_kart(self, grid, row, col, ikon, baslik, deger):
        kart = QFrame()
        kart.setObjectName("Panel")
        kart.setMinimumHeight(98)
        layout = QHBoxLayout(kart)
        layout.setContentsMargins(14, 10, 14, 10)
        i = QLabel(ikon)
        i.setAlignment(Qt.AlignCenter)
        i.setFixedSize(42, 42)
        i.setStyleSheet("font-size:20px;color:#2563EB;background:#EFF6FF;border:1px solid #DBEAFE;border-radius:14px;font-weight:900;")
        y = QVBoxLayout()
        b = QLabel(baslik)
        b.setStyleSheet("font-size:13px;color:#475569;font-weight:800;")
        d = QLabel(deger)
        d.setStyleSheet("font-size:22px;color:#0F172A;font-weight:900;")
        y.addWidget(b)
        y.addWidget(d)
        layout.addWidget(i)
        layout.addLayout(y)
        layout.addStretch()
        grid.addWidget(kart, row, col)
        return d

    def kasa_tarih_where(self):
        filtre = self.cmbKasaFiltre.currentText() if hasattr(self, "cmbKasaFiltre") else "Bugün"
        bugun = datetime.now()
        if filtre == "Bugün":
            return "WHERE tarih LIKE ?", [bugun.strftime("%d.%m.%Y") + "%"]
        if filtre == "Bu Ay":
            return "WHERE substr(tarih, 4, 7)=?", [bugun.strftime("%m.%Y")]
        if filtre == "Bu Hafta":
            # Tarih metin formatı dd.mm.yyyy olduğu için haftayı Python tarafında filtreleyeceğiz.
            return "", []
        return "", []

    def kasa_sayfa_yenile(self):
        if not hasattr(self, "tblKasa"):
            return
        kasa_tablosu_olustur()
        filtre = self.cmbKasaFiltre.currentText() if hasattr(self, "cmbKasaFiltre") else "Bugün"
        where, params = self.kasa_tarih_where()
        try:
            with db_baglan() as conn:
                cur = conn.cursor()
                if where:
                    cur.execute("""
                        SELECT id, tarih, tip, odeme_tipi, tutar, aciklama, kaynak, kullanici
                        FROM kasa_hareketleri
                        WHERE tarih LIKE ?
                        ORDER BY id DESC
                    """, params)
                else:
                    cur.execute("""
                        SELECT id, tarih, tip, odeme_tipi, tutar, aciklama, kaynak, kullanici
                        FROM kasa_hareketleri
                        ORDER BY id DESC
                    """)
                rows = cur.fetchall()
        except Exception as hata:
            log_yaz(f"Kasa hareketleri yüklenemedi: {hata}")
            QMessageBox.warning(self, "Hata", "Kasa hareketleri yüklenemedi. Lütfen tekrar deneyin.")
            return

        if filtre == "Bu Hafta":
            bas = datetime.now().date()
            hafta_basi = bas.fromordinal(bas.toordinal() - bas.weekday())
            filtreli = []
            for row in rows:
                try:
                    trh = datetime.strptime(str(row[1])[:10], "%d.%m.%Y").date()
                    if trh >= hafta_basi:
                        filtreli.append(row)
                except Exception:
                    pass
            rows = filtreli

        self.tblKasa.setRowCount(len(rows))
        giris = cikis = nakit = kart = 0.0
        for r, row in enumerate(rows):
            kid, tarih, tip, odeme, tutar, aciklama, kaynak, kullanici = row
            tutar = float(tutar or 0)
            if str(tip).upper() == "GIRIS":
                giris += tutar
                if str(odeme).upper() == "KART":
                    kart += tutar
                else:
                    nakit += tutar
            else:
                cikis += tutar
                if str(odeme).upper() != "KART":
                    nakit -= tutar
            veriler = [kid, tarih, "Giriş" if tip == "GIRIS" else "Çıkış", odeme or "", para_yaz(tutar), aciklama or "", kaynak or "", kullanici or ""]
            for c, val in enumerate(veriler):
                item = QTableWidgetItem(str(val))
                if c in (2, 4):
                    item.setTextAlignment(Qt.AlignCenter)
                self.tblKasa.setItem(r, c, item)
        net = giris - cikis
        self.lblKasaNakit.setText(para_yaz(nakit))
        self.lblKasaKart.setText(para_yaz(kart))
        self.lblKasaGiris.setText(para_yaz(giris))
        self.lblKasaCikis.setText(para_yaz(cikis))
        self.lblKasaNet.setText(f"Net Kasa\n{para_yaz(net)}")
        self.lblKasaOzet.setText(
            f"Filtre: {filtre}\n"
            f"Toplam Giriş: {para_yaz(giris)}\n"
            f"Toplam Çıkış: {para_yaz(cikis)}\n"
            f"Net: {para_yaz(net)}\n"
            f"Hareket Sayısı: {len(rows)}"
        )
        try:
            self.durum_cubugu_guncelle()
        except Exception:
            pass

    def kasa_hareket_dialog(self, tip, odeme_tipi, varsayilan_aciklama):
        dlg = QDialog(self)
        dlg.setWindowTitle("Kasa Hareketi")
        dlg.resize(420, 330)
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel("Ödeme Tipi"))
        cmb = QComboBox()
        cmb.addItems(["NAKİT", "KART", "HAVALE"])
        cmb.setCurrentText(odeme_tipi)
        layout.addWidget(cmb)
        layout.addWidget(QLabel("Tutar"))
        txtTutar = QLineEdit()
        txtTutar.setPlaceholderText("Örn: 1500")
        layout.addWidget(txtTutar)
        layout.addWidget(QLabel("Açıklama"))
        txtAciklama = QTextEdit()
        txtAciklama.setPlainText(varsayilan_aciklama)
        txtAciklama.setMaximumHeight(110)
        layout.addWidget(txtAciklama)
        btn = QPushButton("Kaydet")
        btn.setObjectName("GreenButton" if tip == "GIRIS" else "RedButton")
        layout.addWidget(btn)

        def kaydet():
            try:
                tutar = float(txtTutar.text().replace(".", "").replace(",", "."))
                kasa_hareketi_ekle(tip, tutar, txtAciklama.toPlainText().strip(), cmb.currentText(), "MANUEL")
                log_yaz(f"Kasa hareketi eklendi: {tip} - {para_yaz(tutar)}")
                dlg.accept()
                self.kasa_sayfa_yenile()
            except Exception as hata:
                QMessageBox.warning(dlg, "Hata", f"Kasa hareketi kaydedilemedi:\n{hata}")
        btn.clicked.connect(kaydet)
        dlg.exec()

    def kasa_rapor_html(self):
        firma = firma_bilgisi_getir()
        filtre = self.cmbKasaFiltre.currentText() if hasattr(self, "cmbKasaFiltre") else "Bugün"
        satirlar = ""
        giris = cikis = 0.0
        if hasattr(self, "tblKasa"):
            for r in range(self.tblKasa.rowCount()):
                tarih = self.tblKasa.item(r, 1).text() if self.tblKasa.item(r, 1) else ""
                tip = self.tblKasa.item(r, 2).text() if self.tblKasa.item(r, 2) else ""
                odeme = self.tblKasa.item(r, 3).text() if self.tblKasa.item(r, 3) else ""
                tutar_txt = self.tblKasa.item(r, 4).text() if self.tblKasa.item(r, 4) else "0"
                aciklama = self.tblKasa.item(r, 5).text() if self.tblKasa.item(r, 5) else ""
                try:
                    tutar = float(tutar_txt.replace("₺", "").replace(".", "").replace(",", ".").strip())
                except Exception:
                    tutar = 0.0
                if tip == "Giriş":
                    giris += tutar
                else:
                    cikis += tutar
                satirlar += f"<tr><td>{tarih}</td><td>{tip}</td><td>{odeme}</td><td>{aciklama}</td><td align='right'>{para_yaz(tutar)}</td></tr>"
        net = giris - cikis
        return f"""
        <html><head><style>
        body {{ font-family: Arial; font-size: 9pt; color:#111827; }}
        h1 {{ color:#1E293B; font-size:18pt; text-align:center; }}
        table {{ width:100%; border-collapse:collapse; }}
        th {{ background:#0D47A1; color:white; padding:6px; }}
        td {{ border:1px solid #D1D5DB; padding:5px; }}
        .ozet {{ margin:8px 0; padding:8px; border:1px solid #9CA3AF; font-size:11pt; }}
        </style></head><body>
        <h1>GÜN SONU / KASA RAPORU</h1>
        <b>{firma.get('firma_adi','')}</b><br>{firma.get('telefon','')}<br>{firma.get('adres','')}<hr>
        <div class='ozet'><b>Filtre:</b> {filtre} &nbsp
        <b>Rapor Tarihi:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}<br>
        <b>Toplam Giriş:</b> {para_yaz(giris)} &nbsp
        <b>Toplam Çıkış:</b> {para_yaz(cikis)} &nbsp
        <b>Net:</b> {para_yaz(net)}</div>
        <table><tr><th>Tarih</th><th>Tip</th><th>Ödeme</th><th>Açıklama</th><th>Tutar</th></tr>{satirlar}</table>
        </body></html>
        """

    def kasa_gun_sonu_raporu(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Gün Sonu Raporu")
        dlg.resize(760, 620)
        layout = QVBoxLayout(dlg)
        doc_lbl = QTextEdit()
        doc_lbl.setReadOnly(True)
        doc_lbl.setHtml(self.kasa_rapor_html())
        layout.addWidget(doc_lbl, 1)
        btn_l = QHBoxLayout()
        btnYazdir = QPushButton("Yazdır")
        btnKapat = QPushButton("Kapat")
        btnKapat.setObjectName("GreyButton")
        btn_l.addStretch()
        btn_l.addWidget(btnYazdir)
        btn_l.addWidget(btnKapat)
        layout.addLayout(btn_l)
        btnYazdir.clicked.connect(self.kasa_gun_sonu_yazdir)
        btnKapat.clicked.connect(dlg.close)
        dlg.exec()

    def kasa_gun_sonu_yazdir(self):
        doc = QTextDocument()
        doc.setHtml(self.kasa_rapor_html())
        printer = QPrinter(QPrinter.HighResolution)
        try:
            printer.setPageSize(QPageSize(QPageSize.A4))
        except Exception:
            pass
        dlg = QPrintDialog(printer, self)
        if dlg.exec() == QPrintDialog.Accepted:
            doc.print_(printer)
            QMessageBox.information(self, "Yazdırıldı", "Kasa raporu yazıcıya gönderildi.")

