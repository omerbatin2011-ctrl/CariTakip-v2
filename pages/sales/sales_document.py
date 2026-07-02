import os
import urllib.parse
import webbrowser
from datetime import datetime

from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QMessageBox

from moduller.db import baglan
from moduller.sistem import firma_bilgisi_getir
from moduller.yardimci import logo_html, para_yaz
from pages.sales.sales_utils import parse_sayi


def belge_html(*, tablo_kalem, txt_not, durum, belge_durumu):
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
        <b>Tel :</b> {firma.get('telefon','')} &nbsp; | &nbsp;
        <b>Vergi No / T.C. No :</b> {firma.get('vergi_no','')}
    </div>
    <div style='text-align:center; line-height:1.45;'>
        <b>Adres :</b> {firma.get('adres','')} &nbsp; | &nbsp;
        <b>Vergi Dairesi :</b> {firma.get('vergi_dairesi','')}
    </div>
    <div style='text-align:center; line-height:1.45;'><b>E-Posta :</b> {firma.get('eposta','')}</div>
    <hr><h2 style='text-align:center;'>{belge_durumu.get('tur', 'PROFORMA')}</h2>
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


def ozet_metni(*, tablo_kalem, txt_not, durum, belge_durumu):
    firma = firma_bilgisi_getir()
    cari = durum.get("cari")
    satirlar = [firma.get("firma_adi", ""), f"{belge_durumu.get('tur', 'PROFORMA')} ÖZETİ", f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}"]
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


def ozet_kopyala(*, pencere, ozet_metni_func):
    QApplication.clipboard().setText(ozet_metni_func())
    QMessageBox.information(pencere, "Kopyalandı", "Özet panoya kopyalandı.")


def mail_ac(*, ozet_metni_func, belge_durumu):
    konu = f"{belge_durumu.get('tur', 'PROFORMA')} Özeti"
    body = ozet_metni_func()
    url = "mailto:?subject=" + urllib.parse.quote(konu) + "&body=" + urllib.parse.quote(body)
    webbrowser.open(url)


def yazdir(*, pencere, tablo_kalem, belge_html_func):
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


def pdf_kaydet(*, pencere, tablo_kalem, belge_html_func, belge_durumu):
    if tablo_kalem.rowCount() == 0:
        QMessageBox.warning(pencere, "Uyarı", "PDF için önce ürün ekleyin.")
        return
    dosya_yolu, _ = QFileDialog.getSaveFileName(pencere, "Satış / Proforma PDF Kaydet", f"{belge_durumu.get('tur', 'Proforma').replace(' ', '_')}.pdf", "PDF Dosyası (*.pdf)")
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


def _whatsapp_numarasi_hazirla(telefon):
    rakamlar = "".join(ch for ch in str(telefon or "") if ch.isdigit())
    if not rakamlar: return ""
    if rakamlar.startswith("00"): rakamlar = rakamlar[2:]
    if rakamlar.startswith("0"): rakamlar = "90" + rakamlar[1:]
    elif len(rakamlar) == 10: rakamlar = "90" + rakamlar
    return rakamlar


def whatsapp_proforma_ac(*, pencere, cari, pdf_yolu, toplam):
    telefon = _whatsapp_numarasi_hazirla(cari.get("telefon", "") if cari else "")
    mesaj = "Merhaba, proforma teklifimiz hazırlanmıştır.\n" + f"Toplam: {para_yaz(float(toplam or 0))}\n\n" + "DAL ELEKTRONİK VE TEDARİK"
    if telefon:
        url = "https://web.whatsapp.com/send?phone=" + telefon + "&text=" + urllib.parse.quote(mesaj)
    else:
        url = "https://web.whatsapp.com/?text=" + urllib.parse.quote(mesaj)
    webbrowser.open(url)
    try: os.startfile(os.path.dirname(pdf_yolu))
    except Exception: pass
    QMessageBox.information(pencere, "WhatsApp Hazır", "WhatsApp Web açıldı.\n\nPDF otomatik eklenemez; açılan Proformalar klasöründen PDF dosyasını WhatsApp'a elle ekleyip gönderin.\n\n" + f"PDF:\n{pdf_yolu}")
