
import os
import sys
import urllib.parse
import webbrowser
from datetime import datetime, timedelta

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
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

from moduller.db import db_baglan, urun_tablolari_olustur
from moduller.loglama import log_yaz
from moduller.responsive import page_scroll
from moduller.sistem import firma_bilgisi_getir
from moduller.yardimci import logo_html, para_yaz

BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))


class TeklifMixin:
    def teklifler_sayfasi_olustur(self):
        urun_tablolari_olustur()
        sayfa = QFrame()
        sayfa.setStyleSheet("background:#F8FAFC;")
        ana = QVBoxLayout()
        ana.setContentsMargins(16, 14, 16, 14)
        ana.setSpacing(14)

        ust = QFrame()
        ust.setObjectName("TopBar")
        ust_l = QHBoxLayout()
        ust_l.setContentsMargins(18, 14, 18, 14)
        baslik = QLabel("📑 Teklif Yönetimi")
        baslik.setStyleSheet("font-size:26px;font-weight:900;color:#0F172A;")
        ust_l.addWidget(baslik)
        ust_l.addStretch()

        self.cmbTeklifDurum = QComboBox()
        self.cmbTeklifDurum.addItems(["Tümü", "BEKLEMEDE", "ONAYLANDI", "REDDEDİLDİ", "SATIŞA DÖNÜŞTÜ"])
        self.cmbTeklifDurum.currentTextChanged.connect(self.teklifler_sayfa_yenile)
        ust_l.addWidget(self.cmbTeklifDurum)

        self.txtTeklifAra = QLineEdit()
        self.txtTeklifAra.setPlaceholderText("Teklif no / cari ara...")
        self.txtTeklifAra.setMinimumWidth(260)
        self.txtTeklifAra.textChanged.connect(self.teklifler_sayfa_yenile)
        ust_l.addWidget(self.txtTeklifAra)
        ust.setLayout(ust_l)
        ana.addWidget(ust)

        butonlar = QGridLayout()
        butonlar.setSpacing(10)
        _btn_i = {"i": 0}
        def btn(text, func, primary=False):
            b = QPushButton(text)
            b.setObjectName("PrimaryButton" if primary else "SecondaryButton")
            b.setMinimumHeight(42)
            if primary:
                b.setStyleSheet("""
                    QPushButton#PrimaryButton {
                        background:#4F46E5;
                        color:#FFFFFF;
                        border:none
                        border-radius:14px
                        padding:10px 16px
                        font-size:14px
                        font-weight:900
                    }
                    QPushButton#PrimaryButton:hover { background:#4338CA; }
                """)
            else:
                b.setStyleSheet("""
                    QPushButton#SecondaryButton {
                        background:#FFFFFF;
                        color:#0F172A;
                        border:1px solid #CBD5E1;
                        border-radius:14px
                        padding:10px 16px
                        font-size:14px
                        font-weight:800
                    }
                    QPushButton#SecondaryButton:hover { background:#EEF2FF; border-color:#4F46E5; }
                """)
            b.clicked.connect(func)
            i = _btn_i["i"]
            butonlar.addWidget(b, i // 4, i % 4)
            _btn_i["i"] += 1
            return b
        btn("＋ Yeni Teklif", lambda: self.sayfa_goster("satis"), True)
        btn("👁 Görüntüle", self.teklif_goruntule)
        btn("📄 PDF Kaydet", self.teklif_pdf_kaydet)
        btn("✅ Satışa Dönüştür", self.teklif_satis_donustur)
        btn("🟡 Beklemede", lambda: self.teklif_durum_guncelle("BEKLEMEDE"))
        btn("🔴 Reddedildi", lambda: self.teklif_durum_guncelle("REDDEDİLDİ"))
        btn("📱 WhatsApp", self.teklif_whatsapp_gonder)
        btn("🔄 Yenile", self.teklifler_sayfa_yenile)
        ana.addLayout(butonlar)

        kart = QFrame()
        kart.setObjectName("MainCard")
        kart_l = QVBoxLayout()
        kart_l.setContentsMargins(12,12,12,12)
        self.lblTeklifOzet = QLabel("Teklifler yükleniyor...")
        self.lblTeklifOzet.setStyleSheet("font-weight:900;color:#475569;padding:4px;")
        kart_l.addWidget(self.lblTeklifOzet)
        self.tblTeklifler = QTableWidget()
        self.tblTeklifler.setColumnCount(8)
        self.tblTeklifler.setHorizontalHeaderLabels(["ID", "Teklif No", "Tarih", "Cari", "Toplam", "Durum", "Tür", "Not"])
        self.tblTeklifler.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tblTeklifler.setMinimumHeight(360)
        self.tblTeklifler.setSelectionBehavior(QTableWidget.SelectRows)
        self.tblTeklifler.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tblTeklifler.verticalHeader().setVisible(False)
        self.tblTeklifler.setColumnHidden(0, True)
        self.tblTeklifler.cellDoubleClicked.connect(lambda r, c: self.teklif_goruntule())
        kart_l.addWidget(self.tblTeklifler, 1)
        kart.setLayout(kart_l)
        ana.addWidget(kart, 1)
        sayfa.setLayout(ana)
        self.teklifler_sayfa_yenile()
        return page_scroll(sayfa)

    def _teklif_no_uret(self, teklif_id):
        return f"TKF-{int(teklif_id):05d}"

    def teklifler_sayfa_yenile(self):
        if not hasattr(self, "tblTeklifler"):
            return
        urun_tablolari_olustur()
        arama = self.txtTeklifAra.text().strip() if hasattr(self, "txtTeklifAra") else ""
        durum = self.cmbTeklifDurum.currentText() if hasattr(self, "cmbTeklifDurum") else "Tümü"
        where = ["COALESCE(s.belge_turu,'') IN ('PROFORMA','TEKLİF')"]
        params = []
        if durum != "Tümü":
            where.append("COALESCE(s.teklif_durumu,'BEKLEMEDE')=?")
            params.append(durum)
        if arama:
            where.append("(COALESCE(s.teklif_no,'') LIKE ? OR c.ad LIKE ? OR s.tarih LIKE ?)")
            like = f"%{arama}%"
            params.extend([like, like, like])
        sql = f"""
            SELECT s.id, COALESCE(s.teklif_no,''), s.tarih, COALESCE(c.ad,''),
                   COALESCE(s.toplam,0), COALESCE(s.teklif_durumu,'BEKLEMEDE'),
                   COALESCE(s.belge_turu,'PROFORMA'), COALESCE(s.notlar,'')
            FROM satislar s
            LEFT JOIN cariler c ON c.id=s.cari_id
            WHERE {' AND '.join(where)}
            ORDER BY s.id DESC
            LIMIT 500
        """
        try:
            with db_baglan() as conn:
                cur = conn.cursor()
                cur.execute(sql, params)
                rows = cur.fetchall()
                for sid, teklif_no, *_ in rows:
                    if not teklif_no:
                        cur.execute("UPDATE satislar SET teklif_no=? WHERE id=?", (self._teklif_no_uret(sid), sid))
                cur.execute("SELECT COUNT(*), COALESCE(SUM(toplam),0) FROM satislar WHERE COALESCE(belge_turu,'') IN ('PROFORMA','TEKLİF') AND COALESCE(teklif_durumu,'BEKLEMEDE')='BEKLEMEDE'")
                bek_sayi, bek_toplam = cur.fetchone()
            # tekrar oku, teklif_no güncellenmiş olsun
            with db_baglan() as conn:
                cur = conn.cursor()
                cur.execute(sql, params)
                rows = cur.fetchall()
        except Exception as hata:
            QMessageBox.warning(self, "Hata", f"Teklifler yüklenemedi:\n{hata}")
            return
        self.tblTeklifler.setRowCount(len(rows))
        for r, row in enumerate(rows):
            sid, teklif_no, tarih, cari, toplam, durum, belge_turu, notlar = row
            vals = [sid, teklif_no or self._teklif_no_uret(sid), tarih, cari, para_yaz(float(toplam or 0)), durum, belge_turu, notlar]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(str(v))
                if c == 0:
                    item.setData(1000, int(sid))
                if durum == "ONAYLANDI" or durum == "SATIŞA DÖNÜŞTÜ":
                    item.setBackground(Qt.green)
                elif durum == "REDDEDİLDİ":
                    item.setBackground(Qt.red)
                    item.setForeground(Qt.white)
                elif durum == "BEKLEMEDE":
                    item.setBackground(Qt.yellow)
                self.tblTeklifler.setItem(r, c, item)
        self.lblTeklifOzet.setText(f"Listelenen: {len(rows)}  •  Bekleyen: {int(bek_sayi or 0)}  •  Bekleyen Tutar: {para_yaz(float(bek_toplam or 0))}")

    def secili_teklif_id(self):
        if not hasattr(self, "tblTeklifler"):
            return None
        row = self.tblTeklifler.currentRow()
        if row < 0 or not self.tblTeklifler.item(row, 0):
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir teklif seçin.")
            return None
        return int(self.tblTeklifler.item(row, 0).text())

    def teklif_detay_html(self, teklif_id):
        firma = firma_bilgisi_getir()
        with db_baglan() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT s.id, COALESCE(s.teklif_no,''), COALESCE(s.teklif_durumu,'BEKLEMEDE'),
                       COALESCE(s.belge_turu,'PROFORMA'), s.tarih, c.ad, c.telefon, c.adres,
                       c.vergi_dairesi, c.vergi_no, s.toplam, s.notlar, s.teklif_gecerlilik
                FROM satislar s
                LEFT JOIN cariler c ON c.id=s.cari_id
                WHERE s.id=?
            """, (teklif_id,))
            bas = cur.fetchone()
            cur.execute("SELECT urun_adi, grup_adi, adet, birim_fiyat, tutar FROM satis_kalemleri WHERE satis_id=? ORDER BY id", (teklif_id,))
            kalemler = cur.fetchall()
        if not bas:
            return "<html><body>Teklif bulunamadı.</body></html>"
        sid, teklif_no, durum, belge_turu, tarih, cari_ad, telefon, adres, vd, vn, toplam, notlar, gecerlilik = bas
        teklif_no = teklif_no or self._teklif_no_uret(sid)
        if not gecerlilik:
            gecerlilik = (datetime.now() + timedelta(days=15)).strftime("%d.%m.%Y")
        satirlar = ""
        for urun, grup, adet, fiyat, tutar in kalemler:
            satirlar += f"""
            <tr>
                <td>{urun or ''}</td><td>{grup or ''}</td>
                <td style='text-align:right'>{float(adet or 0):g}</td>
                <td style='text-align:right'>{para_yaz(float(fiyat or 0))}</td>
                <td style='text-align:right'>{para_yaz(float(tutar or 0))}</td>
            </tr>"""
        return f"""
        <html><body style='font-family:Arial, sans-serif;font-size:10pt;'>
        {logo_html(190)}
        <h1 style='text-align:center;color:#1E293B;margin-bottom:4px;'>{firma.get('firma_adi','')}</h1>
        <div style='text-align:center;line-height:1.45;'>{firma.get('telefon','')} &nbsp
        | &nbsp
        {firma.get('adres','')}</div>
        <div style='text-align:center;line-height:1.45;'>{firma.get('vergi_no','')} &nbsp
        | &nbsp
        {firma.get('vergi_dairesi','')} &nbsp
        | &nbsp
        {firma.get('eposta','')}</div>
        <hr>
        <h2 style='text-align:center;'>TEKLİF FORMU</h2>
        <table width='100%' style='margin-bottom:10px;'>
            <tr><td><b>Teklif No:</b> {teklif_no}</td><td style='text-align:right'><b>Tarih:</b> {tarih}</td></tr>
            <tr><td><b>Durum:</b> {durum}</td><td style='text-align:right'><b>Geçerlilik:</b> {gecerlilik}</td></tr>
            <tr><td><b>Cari:</b> {cari_ad or '-'}</td><td style='text-align:right'><b>Telefon:</b> {telefon or '-'}</td></tr>
            <tr><td><b>Vergi Dairesi:</b> {vd or '-'}</td><td style='text-align:right'><b>Vergi No:</b> {vn or '-'}</td></tr>
            <tr><td colspan='2'><b>Adres:</b> {adres or '-'}</td></tr>
        </table>
        <table width='100%' cellspacing='0' cellpadding='6' style='border-collapse:collapse;'>
            <tr style='background:#0D47A1;color:white;'><th align='left'>Ürün</th><th align='left'>Grup</th><th align='right'>Adet</th><th align='right'>Birim Fiyat</th><th align='right'>Tutar</th></tr>
            {satirlar}
            <tr><td colspan='4' style='text-align:right;border-top:1px solid #333;'><b>GENEL TOPLAM</b></td><td style='text-align:right;border-top:1px solid #333;'><b>{para_yaz(float(toplam or 0))}</b></td></tr>
        </table>
        <p><b>Not:</b> {notlar if notlar else '-'}</p>
        </body></html>"""

    def teklif_goruntule(self):
        teklif_id = self.secili_teklif_id()
        if not teklif_id:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Teklif Görüntüle - {teklif_id}")
        dlg.resize(900,700)
        ly = QVBoxLayout()
        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setHtml(self.teklif_detay_html(teklif_id))
        ly.addWidget(txt,1)
        btns = QHBoxLayout()
        bYaz=QPushButton("Yazdır")
        bPdf=QPushButton("PDF Kaydet")
        bKapat=QPushButton("Kapat")
        btns.addWidget(bYaz)
        btns.addWidget(bPdf)
        btns.addStretch()
        btns.addWidget(bKapat)
        ly.addLayout(btns)
        def yazdir():
            pr=QPrinter(QPrinter.HighResolution)
            dialog=QPrintDialog(pr, dlg)
            if dialog.exec()!=QDialog.Accepted:
                return
            doc=QTextDocument()
            doc.setHtml(self.teklif_detay_html(teklif_id))
            doc.print_(pr)
        bYaz.clicked.connect(yazdir)
        bPdf.clicked.connect(lambda: self.teklif_pdf_kaydet(teklif_id))
        bKapat.clicked.connect(dlg.close)
        dlg.setLayout(ly)
        dlg.exec()

    def teklif_pdf_kaydet(self, teklif_id=None):
        teklif_id = teklif_id or self.secili_teklif_id()
        if not teklif_id:
            return
        os.makedirs(os.path.join(BASE_DIR, "Teklifler"), exist_ok=True)
        teklif_no = self._teklif_no_uret(teklif_id)
        try:
            with db_baglan() as conn:
                cur=conn.cursor()
                cur.execute("SELECT COALESCE(teklif_no,'') FROM satislar WHERE id=?", (teklif_id,))
                row=cur.fetchone()
                if row and row[0]:
                    teklif_no=row[0]
        except Exception:
            pass
        varsayilan = os.path.join(BASE_DIR, "Teklifler", f"{teklif_no}.pdf")
        dosya, _ = QFileDialog.getSaveFileName(self, "Teklif PDF Kaydet", varsayilan, "PDF Dosyası (*.pdf)")
        if not dosya:
            return None
        if not dosya.lower().endswith(".pdf"):
            dosya += ".pdf"
        pr=QPrinter(QPrinter.HighResolution)
        pr.setOutputFormat(QPrinter.PdfFormat)
        pr.setOutputFileName(dosya)
        doc=QTextDocument()
        doc.setHtml(self.teklif_detay_html(teklif_id))
        doc.print_(pr)
        with db_baglan() as conn:
            conn.execute("UPDATE satislar SET pdf_yolu=?, teklif_no=COALESCE(teklif_no, ?) WHERE id=?", (dosya, teklif_no, teklif_id))
        QMessageBox.information(self, "PDF Kaydedildi", f"Teklif PDF oluşturuldu:\n{dosya}")
        return dosya

    def teklif_durum_guncelle(self, durum):
        teklif_id = self.secili_teklif_id()
        if not teklif_id:
            return
        with db_baglan() as conn:
            conn.execute("UPDATE satislar SET teklif_durumu=? WHERE id=?", (durum, teklif_id))
        self.teklifler_sayfa_yenile()

    def teklif_satis_donustur(self):
        teklif_id = self.secili_teklif_id()
        if not teklif_id:
            return
        cevap = QMessageBox.question(self, "Satışa Dönüştür", "Seçili teklif cariye BORÇ olarak işlensin ve satışa dönüştürülsün mü?")
        if cevap != QMessageBox.Yes:
            return
        try:
            with db_baglan() as conn:
                cur = conn.cursor()
                cur.execute("SELECT cari_id, toplam, notlar, COALESCE(hareket_id,0), COALESCE(teklif_durumu,'BEKLEMEDE') FROM satislar WHERE id=?", (teklif_id,))
                row = cur.fetchone()
                if not row:
                    raise RuntimeError("Teklif bulunamadı")
                cari_id, toplam, notlar, hareket_id, durum = row
                if int(hareket_id or 0) > 0:
                    QMessageBox.information(self, "Bilgi", "Bu teklif zaten satışa dönüştürülmüş.")
                    return
                tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
                aciklama = f"Teklif satışa dönüştürüldü. Teklif ID: {teklif_id}\n\n{notlar or ''}"
                cur.execute("INSERT INTO hareketler(cari_id, tip, tutar, aciklama, tarih) VALUES (?, 'BORÇ', ?, ?, ?)", (cari_id, float(toplam or 0), aciklama, tarih))
                hid = cur.lastrowid
                cur.execute("UPDATE satislar SET belge_turu='SATIŞ', teklif_durumu='SATIŞA DÖNÜŞTÜ', hareket_id=? WHERE id=?", (hid, teklif_id))
                # Stok düşümü: ürün adı üzerinden güvenli olduğu kadarıyla yapılır.
                cur.execute("SELECT urun_adi, adet FROM satis_kalemleri WHERE satis_id=?", (teklif_id,))
                for urun_adi, adet in cur.fetchall():
                    cur.execute("UPDATE urunler SET stok=COALESCE(stok,0)-? WHERE ad=?", (float(adet or 0), urun_adi))
            log_yaz(f"Teklif satışa dönüştürüldü: {teklif_id}")
            QMessageBox.information(self, "Başarılı", "Teklif satışa dönüştürüldü ve cariye borç işlendi.")
            self.teklifler_sayfa_yenile()
            self.ozet_yukle()
        except Exception as hata:
            QMessageBox.warning(self, "Hata", f"Teklif satışa dönüştürülemedi:\n{hata}")

    def teklif_whatsapp_gonder(self):
        teklif_id = self.secili_teklif_id()
        if not teklif_id:
            return
        pdf = self.teklif_pdf_kaydet(teklif_id)
        with db_baglan() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT c.telefon, c.ad, COALESCE(s.toplam,0), COALESCE(s.teklif_no,'')
                FROM satislar s LEFT JOIN cariler c ON c.id=s.cari_id WHERE s.id=?
            """, (teklif_id,))
            row = cur.fetchone()
        telefon, cari_ad, toplam, teklif_no = row if row else ("", "", 0, "")
        rakam = "".join(ch for ch in str(telefon or "") if ch.isdigit())
        if rakam.startswith("0"):
            rakam = "90" + rakam[1:]
        elif len(rakam) == 10:
            rakam = "90" + rakam
        mesaj = f"Merhaba {cari_ad or ''}, {teklif_no or self._teklif_no_uret(teklif_id)} numaralı teklifimiz hazırlanmıştır. Toplam: {para_yaz(float(toplam or 0))}"
        url = "https://web.whatsapp.com/send?phone=" + rakam + "&text=" + urllib.parse.quote(mesaj) if rakam else "https://web.whatsapp.com/?text=" + urllib.parse.quote(mesaj)
        webbrowser.open(url)
        try:
            if pdf:
                os.startfile(os.path.dirname(pdf))
        except Exception:
            pass
        QMessageBox.information(self, "WhatsApp Hazır", "WhatsApp Web açıldı. PDF dosyasını açılan klasörden elle ekleyebilirsiniz.")

