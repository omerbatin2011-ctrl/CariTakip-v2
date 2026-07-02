"""Sales history dialog and saved document preview helpers."""

from __future__ import annotations

from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from moduller.db import baglan
from moduller.sistem import firma_bilgisi_getir
from moduller.yardimci import logo_html, para_yaz

def kayit_belge_html(satis_id):
    firma = firma_bilgisi_getir()
    conn = baglan(); cur = conn.cursor()
    cur.execute("""
        SELECT s.id, COALESCE(s.belge_turu, CASE WHEN s.hareket_id IS NULL THEN 'PROFORMA' ELSE 'SATIŞ' END),
               s.tarih, c.ad, c.telefon, c.adres, c.vergi_dairesi, c.vergi_no, s.toplam, s.notlar
        FROM satislar s LEFT JOIN cariler c ON c.id=s.cari_id WHERE s.id=?
    """, (satis_id,))
    baslik_row = cur.fetchone()
    cur.execute("SELECT urun_adi, grup_adi, adet, birim_fiyat, tutar FROM satis_kalemleri WHERE satis_id=? ORDER BY id", (satis_id,))
    kalemler = cur.fetchall(); conn.close()
    if not baslik_row:
        return "<html><body>Kayıt bulunamadı.</body></html>"
    sid, belge_turu, tarih, cari_ad, telefon, adres, vergi_dairesi, vergi_no, toplam, notlar = baslik_row
    satir_html = "".join(f"""
        <tr><td>{urun or ''}</td><td>{grup or ''}</td><td style='text-align:right'>{float(adet or 0):g}</td><td style='text-align:right'>{para_yaz(float(fiyat or 0))}</td><td style='text-align:right'>{para_yaz(float(tutar or 0))}</td></tr>
    """ for urun, grup, adet, fiyat, tutar in kalemler)
    return f"""
    <html><body style='font-family:Arial, sans-serif; font-size:10pt;'>
    {logo_html(190)}<h1 style='color:#1E293B;margin-bottom:2px;text-align:center;'>{firma.get('firma_adi','')}</h1>
    <div style='text-align:center;'>{firma.get('telefon','')} &nbsp; | &nbsp; {firma.get('adres','')}</div>
    <div style='text-align:center;'>{firma.get('vergi_no','')} &nbsp; | &nbsp; {firma.get('vergi_dairesi','')} &nbsp; | &nbsp; {firma.get('eposta','')}</div><hr>
    <h2 style='text-align:center;'>{belge_turu}</h2>
    <table width='100%' style='margin-bottom:10px;'><tr><td><b>Kayıt No:</b> {sid}</td><td style='text-align:right'><b>Tarih:</b> {tarih}</td></tr><tr><td><b>Cari:</b> {cari_ad or '-'}</td><td style='text-align:right'><b>Telefon:</b> {telefon or '-'}</td></tr><tr><td><b>Vergi Dairesi:</b> {vergi_dairesi or '-'}</td><td style='text-align:right'><b>Vergi No:</b> {vergi_no or '-'}</td></tr><tr><td colspan='2'><b>Adres:</b> {adres or '-'}</td></tr></table>
    <table width='100%' cellspacing='0' cellpadding='6' style='border-collapse:collapse;'><tr style='background:#0D47A1;color:white;'><th align='left'>Ürün</th><th align='left'>Grup</th><th align='right'>Adet</th><th align='right'>Birim Fiyat</th><th align='right'>Tutar</th></tr>{satir_html}<tr><td colspan='4' style='text-align:right;border-top:1px solid #333;'><b>GENEL TOPLAM</b></td><td style='text-align:right;border-top:1px solid #333;'><b>{para_yaz(float(toplam or 0))}</b></td></tr></table>
    <p><b>Not:</b> {notlar if notlar else '-'}</p></body></html>
    """


def kayit_goruntule(pencere, satis_id):
    detay = QDialog(pencere); detay.setWindowTitle(f"Kayıt Görüntüle - {satis_id}"); detay.resize(900, 700)
    ly = QVBoxLayout(); bas = QLabel("KAYIT GÖRÜNTÜLE"); bas.setStyleSheet("font-size:22px;font-weight:800;color:#1E293B;padding:8px;"); ly.addWidget(bas)
    txt = QTextEdit(); txt.setReadOnly(True); txt.setHtml(kayit_belge_html(satis_id)); ly.addWidget(txt, 1)
    btns = QHBoxLayout(); btnYazdirDetay = QPushButton("Yazdır"); btnPdfDetay = QPushButton("PDF Kaydet"); btnKapatDetay = QPushButton("Kapat"); btnKapatDetay.setObjectName("GreyButton")
    btns.addWidget(btnYazdirDetay); btns.addWidget(btnPdfDetay); btns.addStretch(); btns.addWidget(btnKapatDetay); ly.addLayout(btns)
    def detay_yazdir():
        printer = QPrinter(QPrinter.HighResolution); dialog = QPrintDialog(printer, detay); dialog.setWindowTitle("Kayıt Yazdır")
        if dialog.exec() != QDialog.Accepted: return
        doc = QTextDocument(); doc.setHtml(kayit_belge_html(satis_id)); doc.print_(printer)
    def detay_pdf():
        dosya_yolu, _ = QFileDialog.getSaveFileName(detay, "Kayıt PDF Kaydet", f"Kayit_{satis_id}.pdf", "PDF Dosyası (*.pdf)")
        if not dosya_yolu: return
        if not dosya_yolu.lower().endswith(".pdf"): dosya_yolu += ".pdf"
        printer = QPrinter(QPrinter.HighResolution); printer.setOutputFormat(QPrinter.PdfFormat); printer.setOutputFileName(dosya_yolu)
        doc = QTextDocument(); doc.setHtml(kayit_belge_html(satis_id)); doc.print_(printer); QMessageBox.information(detay, "PDF Kaydedildi", f"PDF oluşturuldu:\n{dosya_yolu}")
    btnYazdirDetay.clicked.connect(detay_yazdir); btnPdfDetay.clicked.connect(detay_pdf); btnKapatDetay.clicked.connect(detay.close)
    detay.setLayout(ly); detay.exec()


def satis_gecmisi(*, pencere):
    gecmis = QDialog(pencere); gecmis.setWindowTitle("Satış / Proforma Geçmişi"); gecmis.resize(1050, 620)
    ly = QVBoxLayout(); bas = QLabel("SATIŞ / PROFORMA GEÇMİŞİ"); bas.setStyleSheet("font-size:22px;font-weight:800;color:#1E293B;padding:8px;"); ly.addWidget(bas)
    bilgi = QLabel("Bir kaydı seçip 'Seçili Kaydı Görüntüle' butonuna basın. İsterseniz satıra çift tıklayarak da açabilirsiniz."); bilgi.setStyleSheet("font-size:12px;color:#64748B;padding-left:8px;"); ly.addWidget(bilgi)
    tablo = QTableWidget(); tablo.setColumnCount(6); tablo.setHorizontalHeaderLabels(["ID", "Tür", "Tarih", "Cari", "Toplam", "Not"]); tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); tablo.setSelectionBehavior(QTableWidget.SelectRows); tablo.setEditTriggers(QTableWidget.NoEditTriggers); tablo.verticalHeader().setVisible(False); ly.addWidget(tablo, 1)
    conn = baglan(); cur = conn.cursor(); cur.execute("""
        SELECT s.id, COALESCE(s.belge_turu, CASE WHEN s.hareket_id IS NULL THEN 'PROFORMA' ELSE 'SATIŞ' END), s.tarih, c.ad, s.toplam, s.notlar
        FROM satislar s LEFT JOIN cariler c ON c.id=s.cari_id ORDER BY s.id DESC LIMIT 300
    """); rows = cur.fetchall(); conn.close()
    tablo.setRowCount(len(rows))
    for r, row in enumerate(rows):
        sid, belge_turu, tarih, cari_ad, toplam, notlar = row
        vals = [sid, belge_turu or "", tarih, cari_ad or "", para_yaz(float(toplam or 0)), notlar or ""]
        for c, v in enumerate(vals):
            item = QTableWidgetItem(str(v))
            if c == 0: item.setData(1000, int(sid))
            tablo.setItem(r, c, item)
    btns = QHBoxLayout(); btnGoruntule = QPushButton("Seçili Kaydı Görüntüle"); btnKapat = QPushButton("Kapat"); btnKapat.setObjectName("GreyButton"); btns.addWidget(btnGoruntule); btns.addStretch(); btns.addWidget(btnKapat); ly.addLayout(btns)
    def secili_kaydi_ac():
        row = tablo.currentRow()
        if row < 0 or not tablo.item(row, 0):
            QMessageBox.warning(gecmis, "Uyarı", "Lütfen görüntülemek için bir kayıt seçin."); return
        kayit_goruntule(pencere, int(tablo.item(row, 0).text()))
    btnGoruntule.clicked.connect(secili_kaydi_ac); tablo.cellDoubleClicked.connect(lambda r, c: kayit_goruntule(pencere, int(tablo.item(r, 0).text())) if tablo.item(r, 0) else None); btnKapat.clicked.connect(gecmis.close)
    gecmis.setLayout(ly); gecmis.exec()
