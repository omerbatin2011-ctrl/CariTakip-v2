"""Sales save operations for proforma and cari debt sales."""

from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Callable

from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import QMessageBox

from moduller.db import baglan, db_baglan
from moduller.yardimci import para_yaz
from pages.sales.sales_utils import parse_sayi

BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))


def _kalem_degerleri(tablo_kalem):
    for row_index in range(tablo_kalem.rowCount()):
        urun = tablo_kalem.item(row_index, 0).text() if tablo_kalem.item(row_index, 0) else ""
        adet = parse_sayi(tablo_kalem.item(row_index, 1).text() if tablo_kalem.item(row_index, 1) else "0")
        fiyat = parse_sayi(tablo_kalem.item(row_index, 2).text() if tablo_kalem.item(row_index, 2) else "0")
        grup = tablo_kalem.item(row_index, 4).text() if tablo_kalem.item(row_index, 4) else ""
        urun_id = ""
        if tablo_kalem.columnCount() > 5 and tablo_kalem.item(row_index, 5):
            urun_id = tablo_kalem.item(row_index, 5).text()
        yield {
            "urun": urun,
            "adet": adet,
            "fiyat": fiyat,
            "grup": grup,
            "tutar": adet * fiyat,
            "urun_id": urun_id,
        }


def _stok_eksikleri(tablo_kalem, *, connection_factory):
    eksikler = []
    try:
        with connection_factory() as conn_kontrol:
            cur_kontrol = conn_kontrol.cursor()
            for kalem in _kalem_degerleri(tablo_kalem):
                if not kalem["urun_id"]:
                    continue
                cur_kontrol.execute(
                    "SELECT ad, COALESCE(stok,0) FROM urunler WHERE id=?",
                    (int(kalem["urun_id"]),),
                )
                stok_row = cur_kontrol.fetchone()
                if stok_row and float(stok_row[1] or 0) < kalem["adet"]:
                    eksikler.append(
                        f"{stok_row[0]}: stok {float(stok_row[1] or 0):g}, "
                        f"istenen {kalem['adet']:g}"
                    )
    except Exception:
        return []
    return eksikler


def _cari_ve_sepet_kontrol(*, pencere, durum, secili_cari_al, tablo_kalem, hesapla_toplam):
    cari = durum.get("cari") or secili_cari_al()
    if not cari:
        QMessageBox.warning(pencere, "Uyarı", "Önce müşteri/cari seçin.")
        return None, 0.0
    if tablo_kalem.rowCount() == 0:
        QMessageBox.warning(pencere, "Uyarı", "Önce ürün ekleyin.")
        return None, 0.0
    toplam = hesapla_toplam()
    if toplam <= 0:
        QMessageBox.warning(pencere, "Uyarı", "Toplam tutar 0'dan büyük olmalı.")
        return None, 0.0
    return cari, toplam


def kaydet_proforma(
    *,
    pencere,
    durum,
    belge_durumu,
    secili_cari_al,
    tablo_kalem,
    txt_not,
    hesapla_toplam,
    belge_html: Callable[[], str],
    whatsapp_proforma_ac,
):
    """Save proforma without posting debt to customer account."""

    belge_durumu["tur"] = "PROFORMA"
    cari, toplam = _cari_ve_sepet_kontrol(
        pencere=pencere,
        durum=durum,
        secili_cari_al=secili_cari_al,
        tablo_kalem=tablo_kalem,
        hesapla_toplam=hesapla_toplam,
    )
    if not cari:
        return

    tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
    notlar = txt_not.toPlainText().strip()
    stok_eksikleri = _stok_eksikleri(tablo_kalem, connection_factory=db_baglan)
    if stok_eksikleri:
        QMessageBox.warning(
            pencere,
            "Stok Yetersiz",
            "Bazı ürünlerde yeterli stok yok:\n\n" + "\n".join(stok_eksikleri),
        )
        return

    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO satislar(cari_id, tarih, toplam, notlar, hareket_id, belge_turu) "
            "VALUES (?, ?, ?, ?, NULL, 'PROFORMA')",
            (cari["id"], tarih, toplam, notlar),
        )
        satis_id = cur.lastrowid
        for kalem in _kalem_degerleri(tablo_kalem):
            cur.execute(
                "INSERT INTO satis_kalemleri(satis_id, grup_adi, urun_adi, adet, birim_fiyat, tutar) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (satis_id, kalem["grup"], kalem["urun"], kalem["adet"], kalem["fiyat"], kalem["tutar"]),
            )

    proforma_klasor = os.path.join(BASE_DIR, "Proformalar")
    os.makedirs(proforma_klasor, exist_ok=True)
    pdf_yolu = os.path.join(proforma_klasor, f"PF-{int(satis_id):05d}.pdf")
    if os.path.exists(pdf_yolu):
        pdf_yolu = os.path.join(
            proforma_klasor,
            f"PF-{int(satis_id):05d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        )

    try:
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(pdf_yolu)
        doc = QTextDocument()
        doc.setHtml(belge_html())
        doc.print_(printer)
        QMessageBox.information(
            pencere,
            "Proforma Kaydedildi",
            f"Proforma kaydedildi. Cariye borç işlenmedi.\n"
            f"Toplam: {para_yaz(toplam)}\n\n"
            f"PDF yeri:\n{pdf_yolu}",
        )
        try:
            os.startfile(proforma_klasor)
        except Exception:
            pass

        cevap_wp = QMessageBox.question(pencere, "WhatsApp", "Proformayı WhatsApp Web ile göndermek ister misiniz?")
        if cevap_wp == QMessageBox.Yes:
            whatsapp_proforma_ac(cari, pdf_yolu, toplam)
    except Exception as hata:
        QMessageBox.warning(
            pencere,
            "PDF Hatası",
            f"Proforma kaydedildi ama PDF oluşturulamadı:\n{hata}",
        )


def kaydet_cariye_borc(
    *,
    pencere,
    self_obj,
    durum,
    belge_durumu,
    secili_cari_al,
    tablo_kalem,
    txt_not,
    hesapla_toplam,
    ozet_metni,
    liste_temizle,
    cari_liste_yukle_urun,
):
    """Save sale, post debt to cari account, and decrease stock."""

    belge_durumu["tur"] = "ÜRÜN SATIŞI"
    cari, toplam = _cari_ve_sepet_kontrol(
        pencere=pencere,
        durum=durum,
        secili_cari_al=secili_cari_al,
        tablo_kalem=tablo_kalem,
        hesapla_toplam=hesapla_toplam,
    )
    if not cari:
        return

    stok_eksikleri = _stok_eksikleri(tablo_kalem, connection_factory=baglan)
    if stok_eksikleri:
        QMessageBox.warning(
            pencere,
            "Stok Yetersiz",
            "Bazı ürünlerde yeterli stok yok:\n\n" + "\n".join(stok_eksikleri),
        )
        return

    tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
    notlar = txt_not.toPlainText().strip()
    aciklama = (notlar or "Ürün satış kaydı") + "\n\n" + ozet_metni()
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO hareketler(cari_id, tip, tutar, aciklama, tarih) VALUES (?, 'BORÇ', ?, ?, ?)",
            (cari["id"], toplam, aciklama, tarih),
        )
        hareket_id = cur.lastrowid
        cur.execute(
            "INSERT INTO satislar(cari_id, tarih, toplam, notlar, hareket_id, belge_turu) "
            "VALUES (?, ?, ?, ?, ?, 'SATIŞ')",
            (cari["id"], tarih, toplam, notlar, hareket_id),
        )
        satis_id = cur.lastrowid
        for kalem in _kalem_degerleri(tablo_kalem):
            cur.execute(
                "INSERT INTO satis_kalemleri(satis_id, grup_adi, urun_adi, adet, birim_fiyat, tutar) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (satis_id, kalem["grup"], kalem["urun"], kalem["adet"], kalem["fiyat"], kalem["tutar"]),
            )
            if kalem["urun_id"]:
                cur.execute(
                    "UPDATE urunler SET stok = COALESCE(stok,0) - ? WHERE id=? AND COALESCE(stok,0) >= ?",
                    (kalem["adet"], int(kalem["urun_id"]), kalem["adet"]),
                )
                if cur.rowcount == 0:
                    raise ValueError("Stok güncelleme sırasında yetersiz stok algılandı.")

    QMessageBox.information(
        pencere,
        "Kaydedildi",
        f"Satış kaydı oluşturuldu, stok düşüldü ve {cari['ad']} carisine BORÇ işlendi.\n"
        f"Toplam: {para_yaz(toplam)}",
    )
    liste_temizle()
    cari_liste_yukle_urun()
    self_obj.ozet_yukle()
