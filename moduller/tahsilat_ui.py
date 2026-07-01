import os
from datetime import datetime

from PySide6.QtGui import QPageSize, QTextDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from moduller.db import db_baglan
from moduller.kasa_ui import kasa_tablosu_olustur
from moduller.loglama import log_yaz
from moduller.sistem import firma_bilgisi_getir
from moduller.yardimci import para_yaz

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TahsilatMixin:
    def tahsilat_sayfasi_olustur(self):
        """Tahsilat ekranı v142 UX düzeni.

        Amaç: koyu/açık tema uyumlu, daha kompakt, iki panelli ve
        boş alanı daha iyi kullanan bir tahsilat ekranı oluşturmak.
        """
        sayfa = QFrame()
        sayfa.setObjectName("ERPPage")
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        # Üst başlık + hızlı arama + günlük özet
        ust = QFrame()
        ust.setObjectName("TopBar")
        ust_l = QHBoxLayout()
        ust_l.setContentsMargins(16, 12, 16, 12)
        ust_l.setSpacing(12)

        baslik_blok = QVBoxLayout()
        baslik_blok.setSpacing(2)
        baslik = QLabel("Tahsilat Makbuzu")
        baslik.setObjectName("PageHeroTitle")
        alt = QLabel("Cari seç, tutarı gir, makbuzu oluştur veya direkt yazdır.")
        alt.setObjectName("FormSectionLabel")
        baslik_blok.addWidget(baslik)
        baslik_blok.addWidget(alt)
        ust_l.addLayout(baslik_blok, 1)

        self.lblTahsilatGunOzeti = QLabel("Bugün: 0 işlem")
        self.lblTahsilatGunOzeti.setObjectName("TahsilatInfoPill")
        ust_l.addWidget(self.lblTahsilatGunOzeti)

        self.txtTahsilatCariAra = QLineEdit()
        self.txtTahsilatCariAra.setPlaceholderText("Cari adı veya telefon ara...")
        self.txtTahsilatCariAra.setMinimumWidth(240)
        self.txtTahsilatCariAra.setMaximumWidth(390)
        self.txtTahsilatCariAra.textChanged.connect(self.tahsilat_sayfa_yenile)
        ust_l.addWidget(self.txtTahsilatCariAra)
        ust.setLayout(ust_l)
        layout.addWidget(ust)

        govde_splitter = QSplitter()
        govde_splitter.setObjectName("ERPSplitter")

        # Sol panel: cari listesi
        sol = QFrame()
        sol.setObjectName("MainCard")
        sol.setMinimumWidth(380)
        sol_l = QVBoxLayout()
        sol_l.setContentsMargins(14, 14, 14, 14)
        sol_l.setSpacing(10)

        sol_baslik_l = QHBoxLayout()
        lblCariListesi = QLabel("Cari Listesi")
        lblCariListesi.setObjectName("SectionTitle")
        sol_baslik_l.addWidget(lblCariListesi)
        sol_baslik_l.addStretch()
        self.lblTahsilatCariSayisi = QLabel("0 kayıt")
        self.lblTahsilatCariSayisi.setObjectName("TahsilatMutedBadge")
        sol_baslik_l.addWidget(self.lblTahsilatCariSayisi)
        sol_l.addLayout(sol_baslik_l)

        self.tblTahsilatCari = QTableWidget()
        self.tblTahsilatCari.setObjectName("ERPTable")
        self.tblTahsilatCari.setColumnCount(4)
        self.tblTahsilatCari.setHorizontalHeaderLabels(["No", "Cari", "Telefon", "ID"])
        self.tblTahsilatCari.setColumnHidden(3, True)
        self.tblTahsilatCari.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tblTahsilatCari.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tblTahsilatCari.setSelectionBehavior(QTableWidget.SelectRows)
        self.tblTahsilatCari.setSelectionMode(QTableWidget.SingleSelection)
        self.tblTahsilatCari.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tblTahsilatCari.verticalHeader().setVisible(False)
        self.tblTahsilatCari.setAlternatingRowColors(True)
        self.tblTahsilatCari.itemSelectionChanged.connect(self.tahsilat_cari_secildi)
        sol_l.addWidget(self.tblTahsilatCari, 1)
        sol.setLayout(sol_l)
        govde_splitter.addWidget(sol)

        # Sağ panel: seçili cari + form + işlem butonları
        sag = QFrame()
        sag.setObjectName("MainCard")
        sag.setMinimumWidth(430)
        sag_l = QVBoxLayout()
        sag_l.setContentsMargins(16, 16, 16, 16)
        sag_l.setSpacing(11)

        self.lblTahsilatSeciliCari = QLabel("Seçili Cari: Yok")
        self.lblTahsilatSeciliCari.setMinimumHeight(74)
        self.lblTahsilatSeciliCari.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.lblTahsilatSeciliCari.setObjectName("TahsilatSelectedCari")
        self.lblTahsilatSeciliCari.setWordWrap(True)
        sag_l.addWidget(self.lblTahsilatSeciliCari)

        cari_btn_grid = QGridLayout()
        cari_btn_grid.setHorizontalSpacing(8)
        cari_btn_grid.setVerticalSpacing(8)
        btnCariSec = QPushButton("👤 Cari Seç")
        btnCariSec.setObjectName("CompactActionButton")
        btnCariSec.clicked.connect(self.tahsilat_cari_sec_buton)
        btnMisafir = QPushButton("🚶 Misafir")
        btnMisafir.setObjectName("CompactActionButton")
        btnMisafir.clicked.connect(self.tahsilat_misafir_sec)
        btnYeniCari = QPushButton("➕ Yeni Cari")
        btnYeniCari.setObjectName("CompactActionButton")
        btnYeniCari.clicked.connect(self.tahsilat_yeni_cari_olustur)
        for i, b in enumerate((btnCariSec, btnMisafir, btnYeniCari)):
            b.setMinimumHeight(38)
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            cari_btn_grid.addWidget(b, 0, i)
        sag_l.addLayout(cari_btn_grid)

        form_kart = QFrame()
        form_kart.setObjectName("TahsilatFormCard")
        form_l = QVBoxLayout()
        form_l.setContentsMargins(14, 12, 14, 12)
        form_l.setSpacing(8)

        lblTutar = QLabel("Tahsilat Tutarı")
        lblTutar.setObjectName("FormSectionLabel")
        form_l.addWidget(lblTutar)
        self.txtTahsilatTutar = QLineEdit()
        self.txtTahsilatTutar.setPlaceholderText("Örn: 1500 veya 1.500,50")
        self.txtTahsilatTutar.setMinimumHeight(40)
        form_l.addWidget(self.txtTahsilatTutar)

        lblAciklama = QLabel("Açıklama")
        lblAciklama.setObjectName("FormSectionLabel")
        form_l.addWidget(lblAciklama)
        self.txtTahsilatAciklama = QTextEdit()
        self.txtTahsilatAciklama.setPlaceholderText("Örn: Peşinat / cari tahsilat / makbuz")
        self.txtTahsilatAciklama.setMinimumHeight(88)
        self.txtTahsilatAciklama.setMaximumHeight(140)
        form_l.addWidget(self.txtTahsilatAciklama)
        form_kart.setLayout(form_l)
        sag_l.addWidget(form_kart)

        btnKaydet = QPushButton("🟢 Tahsilatı Kaydet")
        btnKaydet.setMinimumHeight(46)
        btnKaydet.setObjectName("PrimaryButton")
        btnKaydet.clicked.connect(self.tahsilat_sayfa_kaydet)
        sag_l.addWidget(btnKaydet)

        alt_btn_l = QHBoxLayout()
        alt_btn_l.setSpacing(8)
        btnDirektYazdir = QPushButton("🖨 Yazdır")
        btnDirektYazdir.setObjectName("CompactActionButton")
        btnDirektYazdir.setMinimumHeight(38)
        btnDirektYazdir.clicked.connect(self.tahsilat_sayfa_direkt_yazdir)
        btnTemizle = QPushButton("🧹 Temizle")
        btnTemizle.setObjectName("CompactActionButton")
        btnTemizle.setMinimumHeight(38)
        btnTemizle.clicked.connect(self.tahsilat_sayfa_temizle)
        alt_btn_l.addWidget(btnDirektYazdir)
        alt_btn_l.addWidget(btnTemizle)
        sag_l.addLayout(alt_btn_l)

        ipucu = QLabel("İpucu: Cari seçilmezse işlem misafir müşteri olarak hazırlanır.")
        ipucu.setObjectName("TahsilatHint")
        ipucu.setWordWrap(True)
        sag_l.addWidget(ipucu)
        sag_l.addStretch()

        sag.setLayout(sag_l)
        govde_splitter.addWidget(sag)
        govde_splitter.setStretchFactor(0, 5)
        govde_splitter.setStretchFactor(1, 4)
        layout.addWidget(govde_splitter, 1)

        sayfa.setLayout(layout)
        self.tahsilat_secili_cari = None
        self.tahsilat_misafir_sec()
        return sayfa

    def tahsilat_misafir_sec(self):
        """Veritabanına cari kaydı açmadan tahsilat/makbuz hazırlamak için misafir müşteri seçer."""
        self.tahsilat_secili_cari = {
            "id": None,
            "ad": "MİSAFİR MÜŞTERİ",
            "telefon": "",
            "adres": "",
            "vergi_dairesi": "",
            "vergi_no": "",
            "misafir": True,
        }
        if hasattr(self, "tblTahsilatCari"):
            self.tblTahsilatCari.clearSelection()
        if hasattr(self, "lblTahsilatSeciliCari"):
            self.lblTahsilatSeciliCari.setText("👤 MİSAFİR MÜŞTERİ\nCari kartına kaydedilmez. Makbuz yazdırılabilir.")

    def tahsilat_cari_sec_buton(self):
        """Listeden seçili cariyi alır; seçim yoksa hızlı cari seçme penceresi açar."""
        if hasattr(self, "tblTahsilatCari") and self.tblTahsilatCari.currentRow() >= 0:
            self.tahsilat_cari_secildi()
            return
        try:
            with db_baglan() as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, ad, COALESCE(telefon,'') FROM cariler WHERE COALESCE(aktif,1)=1 ORDER BY ad")
                rows = cur.fetchall()
        except Exception as hata:
            QMessageBox.warning(self, "Hata", f"Cari listesi alınamadı:\n{hata}")
            return
        if not rows:
            QMessageBox.information(self, "Cari Yok", "Kayıtlı cari bulunamadı. Yeni cari oluşturabilirsiniz.")
            return
        secenekler = [f"{ad} | {tel}" for _, ad, tel in rows]
        secim, ok = QInputDialog.getItem(self, "Cari Seç", "Tahsilat yapılacak cariyi seçin:", secenekler, 0, False)
        if not ok:
            return
        cari_id = int(rows[secenekler.index(secim)][0])
        cari = self.cari_bilgisi_getir_id(cari_id)
        self.tahsilat_secili_cari = cari
        if cari and hasattr(self, "lblTahsilatSeciliCari"):
            self.lblTahsilatSeciliCari.setText(f"👤 {cari.get('ad','')}\nTelefon: {cari.get('telefon','-') or '-'}  •  Vergi No: {cari.get('vergi_no','-') or '-'}")
        if hasattr(self, "tblTahsilatCari"):
            self.tahsilat_sayfa_yenile()
            for r in range(self.tblTahsilatCari.rowCount()):
                item = self.tblTahsilatCari.item(r, 3)
                if item and item.text() == str(cari_id):
                    self.tblTahsilatCari.selectRow(r)
                    break

    def tahsilat_yeni_cari_olustur(self):
        """Yeni cari oluşturur ve oluşturulan cariyi otomatik seçer."""
        try:
            yeni_id = self.yeni_cari(self.tblTahsilatCari if hasattr(self, "tblTahsilatCari") else None)
        except TypeError:
            yeni_id = self.yeni_cari()
        except Exception as hata:
            QMessageBox.warning(self, "Hata", f"Yeni cari oluşturulamadı:\n{hata}")
            return
        if not yeni_id:
            return
        self.tahsilat_sayfa_yenile()
        cari = self.cari_bilgisi_getir_id(int(yeni_id))
        self.tahsilat_secili_cari = cari
        if cari and hasattr(self, "lblTahsilatSeciliCari"):
            self.lblTahsilatSeciliCari.setText(f"👤 {cari.get('ad','')}\nTelefon: {cari.get('telefon','-') or '-'}  •  Vergi No: {cari.get('vergi_no','-') or '-'}")
        if hasattr(self, "tblTahsilatCari"):
            for r in range(self.tblTahsilatCari.rowCount()):
                item = self.tblTahsilatCari.item(r, 3)
                if item and item.text() == str(yeni_id):
                    self.tblTahsilatCari.selectRow(r)
                    break

    def tahsilat_sayfa_yenile(self):
        if not hasattr(self, "tblTahsilatCari"):
            return
        arama = self.txtTahsilatCariAra.text().strip() if hasattr(self, "txtTahsilatCariAra") else ""
        try:
            with db_baglan() as conn:
                cur = conn.cursor()
                if arama:
                    like = f"%{arama}%"
                    cur.execute("SELECT id, ad, telefon FROM cariler WHERE COALESCE(aktif,1)=1 AND (ad LIKE ? OR telefon LIKE ?) ORDER BY ad", (like, like))
                else:
                    cur.execute("SELECT id, ad, telefon FROM cariler WHERE COALESCE(aktif,1)=1 ORDER BY ad")
                rows = cur.fetchall()
        except Exception as hata:
            QMessageBox.warning(self, "Hata", f"Cari listesi yüklenemedi:\n{hata}")
            return
        self.tblTahsilatCari.setRowCount(len(rows))
        for r, (cid, ad, tel) in enumerate(rows):
            self.tblTahsilatCari.setItem(r, 0, QTableWidgetItem(str(r + 1)))
            self.tblTahsilatCari.setItem(r, 1, QTableWidgetItem(ad or ""))
            self.tblTahsilatCari.setItem(r, 2, QTableWidgetItem(tel or ""))
            self.tblTahsilatCari.setItem(r, 3, QTableWidgetItem(str(cid)))
        if hasattr(self, "lblTahsilatCariSayisi"):
            self.lblTahsilatCariSayisi.setText(f"{len(rows)} kayıt")
        if hasattr(self, "lblTahsilatGunOzeti"):
            try:
                with db_baglan() as conn:
                    cur = conn.cursor()
                    bugun = datetime.now().strftime("%d.%m.%Y") + "%"
                    cur.execute("SELECT COUNT(*), COALESCE(SUM(tutar),0) FROM kasa_hareketleri WHERE tarih LIKE ? AND tip='GIRIS'", (bugun,))
                    adet, toplam = cur.fetchone() or (0, 0)
                self.lblTahsilatGunOzeti.setText(f"Bugün: {adet or 0} işlem • {para_yaz(toplam or 0)}")
            except Exception:
                self.lblTahsilatGunOzeti.setText("Bugün: —")

    def tahsilat_cari_secildi(self):
        if not hasattr(self, "tblTahsilatCari"):
            return
        row = self.tblTahsilatCari.currentRow()
        if row < 0 or not self.tblTahsilatCari.item(row, 3):
            return
        cari = self.cari_bilgisi_getir_id(int(self.tblTahsilatCari.item(row, 3).text()))
        self.tahsilat_secili_cari = cari
        if cari:
            self.lblTahsilatSeciliCari.setText(f"👤 {cari.get('ad','')}\nTelefon: {cari.get('telefon','-') or '-'}  •  Vergi No: {cari.get('vergi_no','-') or '-'}")

    def tahsilat_sayfa_temizle(self):
        if hasattr(self, "txtTahsilatTutar"):
            self.txtTahsilatTutar.clear()
        if hasattr(self, "txtTahsilatAciklama"):
            self.txtTahsilatAciklama.clear()
        self.tahsilat_misafir_sec()

    def tahsilat_makbuz_html_olustur(self, makbuz_id, cari, tutar, aciklama, tarih):
        firma = firma_bilgisi_getir()
        logo_yolu = os.path.join(BASE_DIR, "logo.png")
        logo = ""
        if os.path.exists(logo_yolu):
            logo = f'<img src="file:///{logo_yolu.replace(os.sep, "/")}" width="95" height="45">'
        return f"""
        <html><head><style>
        body {{ font-family: Arial; font-size: 8.5pt; color:#111827; margin:0; }}
        .firma {{ font-size:8pt; line-height:1.25; }}
        .baslik {{ font-size:17pt; font-weight:800; color:#1E293B; text-align:center; margin:7px 0 5px 0; }}
        .kutu {{ border:1px solid #9CA3AF; padding:5px; margin-top:5px; }}
        .bolum {{ font-weight:800; color:#1E293B; margin-bottom:3px; }}
        th {{ background:#0D47A1; color:white; font-weight:800; padding:5px; }}
        td {{ padding:5px; }} .imza td {{ height:45px; vertical-align:top; }}
        </style></head><body>
        <table width='100%'><tr><td width='27%' valign='top'>{logo}</td><td width='73%' align='right' valign='top' class='firma'>
        <b style='font-size:12pt;color:#1E293B;'>{firma.get('firma_adi','')}</b><br>
        <b>Tel:</b> {firma.get('telefon','')} &nbsp; | &nbsp; <b>Vergi No:</b> {firma.get('vergi_no','')}<br>
        <b>Adres:</b> {firma.get('adres','')}<br><b>E-Posta:</b> {firma.get('eposta','')}
        </td></tr></table><hr>
        <div class='baslik'>TAHSİLAT MAKBUZU</div>
        <table width='100%'><tr><td><b>Makbuz No:</b> MK-{int(makbuz_id):05d}</td><td align='right'><b>Tarih:</b> {tarih}</td></tr></table>
        <div class='kutu'><div class='bolum'>Müşteri Bilgileri</div><table width='100%'>
        <tr><td width='24%'><b>Cari:</b></td><td>{cari.get('ad','')}</td></tr>
        <tr><td><b>Telefon:</b></td><td>{cari.get('telefon','')}</td></tr>
        <tr><td><b>Adres:</b></td><td>{cari.get('adres','')}</td></tr>
        <tr><td><b>Vergi Dairesi:</b></td><td>{cari.get('vergi_dairesi','')}</td></tr>
        <tr><td><b>Vergi No / T.C. No:</b></td><td>{cari.get('vergi_no','')}</td></tr>
        </table></div>
        <table width='100%' border='1' cellspacing='0' cellpadding='0' style='margin-top:7px;'>
        <tr><th width='70%'>Açıklama</th><th width='30%'>Tutar</th></tr>
        <tr><td>{aciklama or 'Cari tahsilat'}</td><td align='right'><b>{para_yaz(tutar)}</b></td></tr></table>
        <div class='kutu' style='font-size:10pt; text-align:right;'><b>Tahsil Edilen Tutar: {para_yaz(tutar)}</b></div>
        <table width='100%' class='imza' style='margin-top:9px;'><tr>
        <td width='50%'><b>Tahsil Eden</b><br><br>İsim / Kaşe<br>İmza</td>
        <td width='50%' align='right'><b>Ödeyen</b><br><br>Ad Soyad<br>İmza</td>
        </tr></table></body></html>
        """

    def tahsilat_sayfa_direkt_yazdir(self):
        """Kaydetmeden anında yazıcıya tahsilat makbuzu gönderir."""
        cari = getattr(self, "tahsilat_secili_cari", None)
        if not cari:
            self.tahsilat_misafir_sec()
            cari = getattr(self, "tahsilat_secili_cari", None)
        tutar = self._sayi_oku(self.txtTahsilatTutar.text() if hasattr(self, "txtTahsilatTutar") else "0")
        if tutar <= 0:
            QMessageBox.warning(self, "Uyarı", "Tahsilat tutarı 0'dan büyük olmalı.")
            return
        tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
        aciklama = self.txtTahsilatAciklama.toPlainText().strip() if hasattr(self, "txtTahsilatAciklama") else ""
        aciklama = aciklama or "Tahsilat makbuzu"
        doc = QTextDocument()
        # Direkt yazdırmada veritabanına kayıt açılmaz; makbuz no geçici yazılır.
        doc.setHtml(self.tahsilat_makbuz_html_olustur(0, cari, tutar, aciklama, tarih).replace("MK-00000", "DİREKT YAZDIRMA"))
        printer = QPrinter(QPrinter.HighResolution)
        try:
            printer.setPageSize(QPageSize(QPageSize.A5))
        except Exception:
            pass
        dlg = QPrintDialog(printer, self)
        if dlg.exec() == QPrintDialog.Accepted:
            doc.print_(printer)
            QMessageBox.information(self, "Yazdırıldı", "Tahsilat makbuzu yazıcıya gönderildi.\nBu işlem veritabanına kaydedilmedi.")

    def tahsilat_sayfa_kaydet(self):
        cari = getattr(self, "tahsilat_secili_cari", None)
        if not cari:
            self.tahsilat_misafir_sec()
            cari = getattr(self, "tahsilat_secili_cari", None)
        tutar = self._sayi_oku(self.txtTahsilatTutar.text() if hasattr(self, "txtTahsilatTutar") else "0")
        if tutar <= 0:
            QMessageBox.warning(self, "Uyarı", "Tahsilat tutarı 0'dan büyük olmalı.")
            return
        tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
        aciklama = self.txtTahsilatAciklama.toPlainText().strip() if hasattr(self, "txtTahsilatAciklama") else ""
        aciklama = aciklama or "Tahsilat makbuzu"
        try:
            misafir = bool(cari.get("misafir")) or cari.get("id") is None
            hareket_id = None
            kasa_tablosu_olustur()
            if misafir:
                # Misafir müşteride cari kartı/hareket/makbuz kaydı açılmaz; sadece kasa girişi tutulur.
                makbuz_id = int(datetime.now().strftime("%H%M%S"))
                with db_baglan() as conn:
                    cur = conn.cursor()
                    cur.execute(
                        """
                        INSERT INTO kasa_hareketleri(tarih, tip, odeme_tipi, tutar, aciklama, kaynak, kaynak_id, kullanici)
                        VALUES (?, 'GIRIS', 'NAKİT', ?, ?, 'TAHSILAT_MISAFIR', NULL, 'admin')
                        """,
                        (tarih, tutar, f"Misafir tahsilat - {aciklama}")
                    )
            else:
                with db_baglan() as conn:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO hareketler(cari_id, tip, tutar, aciklama, tarih) VALUES (?, 'TAHSİLAT', ?, ?, ?)", (cari["id"], tutar, aciklama, tarih))
                    hareket_id = cur.lastrowid
                    cur.execute("INSERT INTO tahsilat_makbuzlari(cari_id, tarih, tutar, aciklama, hareket_id) VALUES (?, ?, ?, ?, ?)", (cari["id"], tarih, tutar, aciklama, hareket_id))
                    makbuz_id = cur.lastrowid
                    cur.execute(
                        """
                        INSERT INTO kasa_hareketleri(tarih, tip, odeme_tipi, tutar, aciklama, kaynak, kaynak_id, kullanici)
                        VALUES (?, 'GIRIS', 'NAKİT', ?, ?, 'TAHSILAT', ?, 'admin')
                        """,
                        (tarih, tutar, f"Cari tahsilat - {cari.get('ad','')} - {aciklama}", makbuz_id)
                    )
            klasor = os.path.join(BASE_DIR, "TahsilatMakbuzlari")
            os.makedirs(klasor, exist_ok=True)
            pdf_yolu = os.path.join(klasor, f"MK-{int(makbuz_id):05d}.pdf")
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            try:
                printer.setPageSize(QPageSize(QPageSize.A5))
            except Exception:
                pass
            printer.setOutputFileName(pdf_yolu)
            doc = QTextDocument()
            html = self.tahsilat_makbuz_html_olustur(makbuz_id, cari, tutar, aciklama, tarih)
            if misafir:
                html = html.replace(f"MK-{int(makbuz_id):05d}", f"MS-{int(makbuz_id):06d}")
            doc.setHtml(html)
            try:
                doc.setPageSize(printer.pageRect(QPrinter.Point).size())
            except Exception:
                pass
            doc.print_(printer)
            if not misafir:
                with db_baglan() as conn:
                    conn.cursor().execute("UPDATE tahsilat_makbuzlari SET pdf_yolu=? WHERE id=?", (pdf_yolu, makbuz_id))
                self.ozet_yukle()
                self.raporlar_sayfa_yenile()
            if hasattr(self, "kasa_sayfa_yenile"):
                self.kasa_sayfa_yenile()
            log_yaz(f"Tahsilat makbuzu oluşturuldu: {'MİSAFİR' if misafir else 'MK-' + str(int(makbuz_id)).zfill(5)} - {cari.get('ad','')} - {para_yaz(tutar)}")
            self.tahsilat_sayfa_temizle()
            QMessageBox.information(self, "Tahsilat Kaydedildi", f"Tahsilat makbuzu oluşturuldu.\nTutar: {para_yaz(tutar)}\n\nPDF:\n{pdf_yolu}")
            try:
                os.startfile(klasor)
            except Exception:
                pass
        except Exception as hata:
            QMessageBox.warning(self, "Hata", f"Tahsilat kaydedilemedi:\n{hata}")

