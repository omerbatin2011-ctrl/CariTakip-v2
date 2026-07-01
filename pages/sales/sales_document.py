"""Satış/proforma belge, çıktı ve geçmiş ekranı işlemleri."""

from __future__ import annotations

import os
import urllib.parse
import webbrowser
from datetime import datetime
from typing import Callable

from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QApplication,
    QHeaderView,
    QDialog,
    QFileDialog,
    QHBoxLayout,
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
from pages.sales.sales_utils import parse_sayi


def belge_html(*, tablo_kalem, txt_not, durum: dict, belge_durumu: dict) -> str:
    firma = firma_bilgisi_getir()
    cari = durum.get("cari")
    tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
    toplam = 0.0
    satir_html = ""
    for r in range(tablo_kalem.rowCount()):
        urun = tablo_kalem.item(r, 0).text() if tablo_kalem.item(r, 0) else ""
        adet = parse_sayi(tablo_kalem.item(r, 1).text() if tablo_kalem.item(r, 1) else "0")
        fiyat = parse_sayi(tablo_kalem.item(r, 2).text() if tablo_kalem.item(r, 2) else "0")
        grup = tablo_kalem.item(r, 4).text() if tablo_kalem.item(r, 4) else ""
        tutar = adet * fiyat
        toplam += tutar
        satir_html += f"""
        <tr>
            <td>{urun}</td><td>{grup}</td><td style='text-align:right'>{adet:g}</td>
            <td style='text-align:right'>{para_yaz(fiyat)}</td><td style='text-align:right'>{para_yaz(tutar)}</td>
        </tr>
        """
    notlar = txt_not.toPlainText().strip()
    return f"""
    <html><body style='font-family:Arial, sans-serif; font-size:10pt;'>
    {logo_html(190)}
    <h1 style='color:#1E293B;margin-bottom:4px;text-align:center;'>{firma.get('firma_adi','')}</h1>
    <div style='text-align:center; line-height:1.45;'>
        <b>Tel :</b> {firma.get('telefon','')} &nbsp
        | &nbsp
        <b>Vergi No / T.C. No :</b> {firma.get('vergi_no','')}
    </div>
    <div style='text-align:center; line-height:1.45;'>
        <b>Adres :</b> {firma.get('adres','')} &nbsp
        | &nbsp
        <b>Vergi Dairesi :</b> {firma.get('vergi_dairesi','')}
    </div>
    <div style='text-align:center; line-height:1.45;'>
        <b>E-Posta :</b> {firma.get('eposta','')}
    </div>
    <hr>
    <h2 style='text-align:center;'>{belge_durumu.get('tur', 'PROFORMA')}</h2>
    <table width='100%' style='margin-bottom:10px;'>
        <tr><td><b>Tarih:</b> {tarih}</td><td style='text-align:right'><b>Cari:</b> {cari['ad'] if cari else '-'}</td></tr>
        <tr><td><b>Vergi Dairesi:</b> {cari.get('vergi_dairesi', '-') if cari else '-'}</td><td style='text-align:right'><b>Vergi No:</b> {cari.get('vergi_no', '-') if cari else '-'}</td></tr>
        <tr><td colspan='2'><b>Adres:</b> {cari.get('adres', '-') if cari else '-'}</td></tr>
        <tr><td colspan='2'><b>Teklif Geçerlilik Süresi:</b> 15 Gün</td></tr>
    </table>
    <table width='100%' cellspacing='0' cellpadding='6' style='border-collapse:collapse;'>
        <tr style='background:#0D47A1;color:white;'>
            <th align='left'>Ürün</th><th align='left'>Grup</th><th align='right'>Adet</th><th align='right'>Birim Fiyat</th><th align='right'>Tutar</th>
        </tr>
        {satir_html}
        <tr><td colspan='4' style='text-align:right;border-top:1px solid #333;'><b>GENEL TOPLAM</b></td><td style='text-align:right;border-top:1px solid #333;'><b>{para_yaz(toplam)}</b></td></tr>
    </table>
    <p><b>Not:</b> {notlar if notlar else '-'}</p>
    </body></html>
    """


def ozet_metni(*, tablo_kalem, txt_not, durum: dict, belge_durumu: dict) -> str:
    firma = firma_bilgisi_getir()
    cari = durum.get("cari")
    satirlar = [
        firma.get("firma_adi", ""),
        f"{belge_durumu.get('tur', 'PROFORMA')} ÖZETİ",
        f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
    ]
    satirlar.append(f"Cari: {cari['ad'] if cari else '-'}")
    if cari:
        satirlar.append(f"Vergi Dairesi: {cari.get('vergi_dairesi', '-') or '-'}")
        satirlar.append(f"Vergi No: {cari.get('vergi_no', '-') or '-'}")
    satirlar.append("")
    toplam = 0.0
    for r in range(tablo_kalem.rowCount()):
        urun = tablo_kalem.item(r, 0).text() if tablo_kalem.item(r, 0) else ""
        adet = parse_sayi(tablo_kalem.item(r, 1).text() if tablo_kalem.item(r, 1) else "0")
        fiyat = parse_sayi(tablo_kalem.item(r, 2).text() if tablo_kalem.item(r, 2) else "0")
        tutar = adet * fiyat
        toplam += tutar
        satirlar.append(f"- {urun}: {adet:g} x {para_yaz(fiyat)} = {para_yaz(tutar)}")
    satirlar.append("")
    satirlar.append(f"TOPLAM: {para_yaz(toplam)}")
    notlar = txt_not.toPlainText().strip()
    if notlar:
        satirlar.append(f"Not: {notlar}")
    return "\n".join(satirlar)


def ozet_kopyala(*, pencere, ozet_metni_func: Callable[[], str]) -> None:
    QApplication.clipboard().setText(ozet_metni_func())
    QMessageBox.information(pencere, "Kopyalandı", "Özet panoya kopyalandı.")


def mail_ac(*, ozet_metni_func: Callable[[], str], belge_durumu: dict) -> None:
    konu = f"{belge_durumu.get('tur', 'PROFORMA')} Özeti"
    body = ozet_metni_func()
    url = "mailto:?subject=" + urllib.parse.quote(konu) + "&body=" + urllib.parse.quote(body)
    webbrowser.open(url)


def yazdir(*, pencere, tablo_kalem, belge_html_func: Callable[[], str]) -> None:
    if tablo_kalem.rowCount() == 0:
        QMessageBox.warning(pencere, "Uyarı", "Yazdırmak için önce ürün ekleyin.")
        return
    printer = QPrinter(QPrinter.HighResolution)
    dialog = QPrintDialog(printer, pencere)
    dialog.setWindowTitle("Satış / Proforma Yazdır")
    if dialog.exec() != QDialog.Accepted:
        return
    doc = QTextDocument()
    doc.setHtml(belge_html_func())
    doc.print_(printer)


def pdf_kaydet(*, pencere, tablo_kalem, belge_html_func: Callable[[], str], belge_durumu: dict) -> None:
    if tablo_kalem.rowCount() == 0:
        QMessageBox.warning(pencere, "Uyarı", "PDF için önce ürün ekleyin.")
        return
    dosya_yolu, _ = QFileDialog.getSaveFileName(
        pencere,
        "Satış / Proforma PDF Kaydet",
        f"{belge_durumu.get('tur', 'Proforma').replace(' ', '_')}.pdf",
        "PDF Dosyası (*.pdf)",
    )
    if not dosya_yolu:
        return
    if not dosya_yolu.lower().endswith(".pdf"):
        dosya_yolu += ".pdf"
    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(dosya_yolu)
    doc = QTextDocument()
    doc.setHtml(belge_html_func())
    doc.print_(printer)
    QMessageBox.information(pencere, "PDF Kaydedildi", f"PDF oluşturuldu:\n{dosya_yolu}")


def kayit_belge_html(satis_id) -> str:
    firma = firma_bilgisi_getir()
    conn = baglan()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.id, COALESCE(s.belge_turu, CASE WHEN s.hareket_id IS NULL THEN 'PROFORMA' ELSE 'SATIŞ' END),
               s.tarih, c.ad, c.telefon, c.adres, c.vergi_dairesi, c.vergi_no, s.toplam, s.notlar
        FROM satislar s
        LEFT JOIN cariler c ON c.id=s.cari_id
        WHERE s.id=?
    """, (satis_id,))
    baslik_row = cur.fetchone()
    cur.execute("""
        SELECT urun_adi, grup_adi, adet, birim_fiyat, tutar
        FROM satis_kalemleri
        WHERE satis_id=?
        ORDER BY id
    """, (satis_id,))
    kalemler = cur.fetchall()
    conn.close()

    if not baslik_row:
        return "<html><body>Kayıt bulunamadı.</body></html>"

    sid, belge_turu, tarih, cari_ad, telefon, adres, vergi_dairesi, vergi_no, toplam, notlar = baslik_row
    satir_html = ""
    for urun, grup, adet, fiyat, tutar in kalemler:
        satir_html += f"""
        <tr>
            <td>{urun or ''}</td>
            <td>{grup or ''}</td>
            <td style='text-align:right'>{float(adet or 0):g}</td>
            <td style='text-align:right'>{para_yaz(float(fiyat or 0))}</td>
            <td style='text-align:right'>{para_yaz(float(tutar or 0))}</td>
        </tr>
        """

    return f"""
    <html><body style='font-family:Arial, sans-serif; font-size:10pt;'>
    {logo_html(190)}
    <h1 style='color:#1E293B;margin-bottom:2px;text-align:center;'>{firma.get('firma_adi','')}</h1>
    <div style='text-align:center;'>{firma.get('telefon','')} &nbsp
    | &nbsp
    {firma.get('adres','')}</div>
    <div style='text-align:center;'>{firma.get('vergi_no','')} &nbsp
    | &nbsp
    {firma.get('vergi_dairesi','')} &nbsp
    | &nbsp
    {firma.get('eposta','')}</div>
    <hr>
    <h2 style='text-align:center;'>{belge_turu}</h2>
    <table width='100%' style='margin-bottom:10px;'>
        <tr><td><b>Kayıt No:</b> {sid}</td><td style='text-align:right'><b>Tarih:</b> {tarih}</td></tr>
        <tr><td><b>Cari:</b> {cari_ad or '-'}</td><td style='text-align:right'><b>Telefon:</b> {telefon or '-'}</td></tr>
        <tr><td><b>Vergi Dairesi:</b> {vergi_dairesi or '-'}</td><td style='text-align:right'><b>Vergi No:</b> {vergi_no or '-'}</td></tr>
        <tr><td colspan='2'><b>Adres:</b> {adres or '-'}</td></tr>
    </table>
    <table width='100%' cellspacing='0' cellpadding='6' style='border-collapse:collapse;'>
        <tr style='background:#0D47A1;color:white;'>
            <th align='left'>Ürün</th><th align='left'>Grup</th><th align='right'>Adet</th><th align='right'>Birim Fiyat</th><th align='right'>Tutar</th>
        </tr>
        {satir_html}
        <tr><td colspan='4' style='text-align:right;border-top:1px solid #333;'><b>GENEL TOPLAM</b></td><td style='text-align:right;border-top:1px solid #333;'><b>{para_yaz(float(toplam or 0))}</b></td></tr>
    </table>
    <p><b>Not:</b> {notlar if notlar else '-'}</p>
    </body></html>
    """


def kayit_goruntule(*, pencere, satis_id) -> None:
    detay = QDialog(pencere)
    detay.setWindowTitle(f"Kayıt Görüntüle - {satis_id}")
    detay.resize(900, 700)
    ly = QVBoxLayout()

    bas = QLabel("KAYIT GÖRÜNTÜLE")
    bas.setStyleSheet("font-size:22px;font-weight:800;color:#1E293B;padding:8px;")
    ly.addWidget(bas)

    txt = QTextEdit()
    txt.setReadOnly(True)
    txt.setHtml(kayit_belge_html(satis_id))
    ly.addWidget(txt, 1)

    btns = QHBoxLayout()
    btn_yazdir_detay = QPushButton("Yazdır")
    btn_pdf_detay = QPushButton("PDF Kaydet")
    btn_kapat_detay = QPushButton("Kapat")
    btn_kapat_detay.setObjectName("GreyButton")
    btns.addWidget(btn_yazdir_detay)
    btns.addWidget(btn_pdf_detay)
    btns.addStretch()
    btns.addWidget(btn_kapat_detay)
    ly.addLayout(btns)

    def detay_yazdir():
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, detay)
        dialog.setWindowTitle("Kayıt Yazdır")
        if dialog.exec() != QDialog.Accepted:
            return
        doc = QTextDocument()
        doc.setHtml(kayit_belge_html(satis_id))
        doc.print_(printer)

    def detay_pdf():
        dosya_yolu, _ = QFileDialog.getSaveFileName(detay, "Kayıt PDF Kaydet", f"Kayit_{satis_id}.pdf", "PDF Dosyası (*.pdf)")
        if not dosya_yolu:
            return
        if not dosya_yolu.lower().endswith(".pdf"):
            dosya_yolu += ".pdf"
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(dosya_yolu)
        doc = QTextDocument()
        doc.setHtml(kayit_belge_html(satis_id))
        doc.print_(printer)
        QMessageBox.information(detay, "PDF Kaydedildi", f"PDF oluşturuldu:\n{dosya_yolu}")

    btn_yazdir_detay.clicked.connect(detay_yazdir)
    btn_pdf_detay.clicked.connect(detay_pdf)
    btn_kapat_detay.clicked.connect(detay.close)
    detay.setLayout(ly)
    detay.exec()


def satis_gecmisi(*, pencere) -> None:
    gecmis = QDialog(pencere)
    gecmis.setWindowTitle("Satış / Proforma Geçmişi")
    gecmis.resize(1050, 620)
    ly = QVBoxLayout()
    bas = QLabel("SATIŞ / PROFORMA GEÇMİŞİ")
    bas.setStyleSheet("font-size:22px;font-weight:800;color:#1E293B;padding:8px;")
    ly.addWidget(bas)
    bilgi = QLabel("Bir kaydı seçip 'Seçili Kaydı Görüntüle' butonuna basın. İsterseniz satıra çift tıklayarak da açabilirsiniz.")
    bilgi.setStyleSheet("font-size:12px;color:#64748B;padding-left:8px;")
    ly.addWidget(bilgi)
    tablo = QTableWidget()
    tablo.setColumnCount(6)
    tablo.setHorizontalHeaderLabels(["ID", "Tür", "Tarih", "Cari", "Toplam", "Not"])
    tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    tablo.setSelectionBehavior(QTableWidget.SelectRows)
    tablo.setEditTriggers(QTableWidget.NoEditTriggers)
    tablo.verticalHeader().setVisible(False)
    ly.addWidget(tablo, 1)
    conn = baglan()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.id, COALESCE(s.belge_turu, CASE WHEN s.hareket_id IS NULL THEN 'PROFORMA' ELSE 'SATIŞ' END), s.tarih, c.ad, s.toplam, s.notlar
        FROM satislar s
        LEFT JOIN cariler c ON c.id=s.cari_id
        ORDER BY s.id DESC
        LIMIT 300
    """)
    rows = cur.fetchall()
    conn.close()
    tablo.setRowCount(len(rows))
    for r, row in enumerate(rows):
        sid, belge_turu, tarih, cari_ad, toplam, notlar = row
        vals = [sid, belge_turu or "", tarih, cari_ad or "", para_yaz(float(toplam or 0)), notlar or ""]
        for c, v in enumerate(vals):
            item = QTableWidgetItem(str(v))
            if c == 0:
                item.setData(1000, int(sid))
            tablo.setItem(r, c, item)

    btns = QHBoxLayout()
    btn_goruntule = QPushButton("Seçili Kaydı Görüntüle")
    btn_kapat = QPushButton("Kapat")
    btn_kapat.setObjectName("GreyButton")
    btns.addWidget(btn_goruntule)
    btns.addStretch()
    btns.addWidget(btn_kapat)
    ly.addLayout(btns)

    def secili_kaydi_ac():
        row = tablo.currentRow()
        if row < 0 or not tablo.item(row, 0):
            QMessageBox.warning(gecmis, "Uyarı", "Lütfen görüntülemek için bir kayıt seçin.")
            return
        try:
            sid = int(tablo.item(row, 0).text())
        except Exception:
            return
        kayit_goruntule(pencere=pencere, satis_id=sid)

    btn_goruntule.clicked.connect(secili_kaydi_ac)
    tablo.cellDoubleClicked.connect(lambda r, c: kayit_goruntule(pencere=pencere, satis_id=int(tablo.item(r, 0).text())) if tablo.item(r, 0) else None)
    btn_kapat.clicked.connect(gecmis.close)
    gecmis.setLayout(ly)
    gecmis.exec()


def whatsapp_numarasi_hazirla(telefon) -> str:
    rakamlar = "".join(ch for ch in str(telefon or "") if ch.isdigit())
    if not rakamlar:
        return ""
    if rakamlar.startswith("00"):
        rakamlar = rakamlar[2:]
    if rakamlar.startswith("0"):
        rakamlar = "90" + rakamlar[1:]
    elif len(rakamlar) == 10:
        rakamlar = "90" + rakamlar
    return rakamlar


def whatsapp_proforma_ac(*, pencere, cari, pdf_yolu, toplam) -> None:
    telefon = whatsapp_numarasi_hazirla(cari.get("telefon", "") if cari else "")
    mesaj = (
        "Merhaba, proforma teklifimiz hazırlanmıştır.\n"
        f"Toplam: {para_yaz(float(toplam or 0))}\n\n"
        "DAL ELEKTRONİK VE TEDARİK"
    )
    if telefon:
        url = "https://web.whatsapp.com/send?phone=" + telefon + "&text=" + urllib.parse.quote(mesaj)
    else:
        url = "https://web.whatsapp.com/?text=" + urllib.parse.quote(mesaj)
    webbrowser.open(url)
    try:
        os.startfile(os.path.dirname(pdf_yolu))
    except Exception:
        pass
    QMessageBox.information(
        pencere,
        "WhatsApp Hazır",
        "WhatsApp Web açıldı.\n\n"
        "PDF otomatik eklenemez; açılan Proformalar klasöründen PDF dosyasını WhatsApp'a elle ekleyip gönderin.\n\n"
        f"PDF:\n{pdf_yolu}",
    )
