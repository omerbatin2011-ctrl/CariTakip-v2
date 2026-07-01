"""Sales cart operations for the sales screen."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QTableWidgetItem

from moduller.db import baglan
from moduller.yardimci import para_yaz
from pages.sales.sales_utils import parse_sayi


def urun_sec_ve_ekle(
    urun_id,
    urun_ad,
    fiyat,
    *,
    durum,
    tablo_kalem,
    hesapla_toplam,
    urunleri_yukle,
):
    """Add a selected product to the cart or increment its quantity."""

    durum["urun_id"] = int(urun_id)
    durum["urun_ad"] = urun_ad
    durum["urun_fiyat"] = float(fiyat or 0)

    # Aynı ürün varsa yeni satır açma, adeti 1 artır.
    for row in range(tablo_kalem.rowCount()):
        mevcut = tablo_kalem.item(row, 0).text() if tablo_kalem.item(row, 0) else ""
        grup = tablo_kalem.item(row, 4).text() if tablo_kalem.item(row, 4) else ""
        mevcut_id = (
            tablo_kalem.item(row, 5).text()
            if tablo_kalem.columnCount() > 5 and tablo_kalem.item(row, 5)
            else ""
        )
        if (mevcut_id and mevcut_id == str(urun_id)) or (
            mevcut == urun_ad and grup == (durum["grup_ad"] or "")
        ):
            adet = parse_sayi(tablo_kalem.item(row, 1).text() if tablo_kalem.item(row, 1) else "0")
            yeni_adet = adet + 1
            tablo_kalem.setItem(
                row,
                1,
                QTableWidgetItem(str(int(yeni_adet) if float(yeni_adet).is_integer() else yeni_adet)),
            )
            tablo_kalem.selectRow(row)
            hesapla_toplam()
            urunleri_yukle()
            return

    satir = tablo_kalem.rowCount()
    tablo_kalem.insertRow(satir)
    tablo_kalem.setItem(satir, 0, QTableWidgetItem(urun_ad))
    tablo_kalem.setItem(satir, 1, QTableWidgetItem("1"))
    tablo_kalem.setItem(satir, 2, QTableWidgetItem(str(fiyat if fiyat else "")))
    tablo_kalem.setItem(satir, 3, QTableWidgetItem("0"))
    tablo_kalem.setItem(satir, 4, QTableWidgetItem(durum["grup_ad"] or ""))
    tablo_kalem.setItem(satir, 5, QTableWidgetItem(str(int(urun_id))))
    tablo_kalem.selectRow(satir)
    hesapla_toplam()
    urunleri_yukle()


def barkod_oku_ve_ekle(
    *,
    pencere,
    txt_barkod_oku,
    durum,
    urun_sec_ve_ekle_callback,
):
    """Read barcode input and add the matching product to the cart."""

    barkod = txt_barkod_oku.text().strip()
    if not barkod:
        return
    try:
        with baglan() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT u.id, u.ad, COALESCE(u.varsayilan_fiyat,0),
                       COALESCE(g.id,0), COALESCE(g.ad,'')
                FROM urunler u
                LEFT JOIN urun_gruplari g ON g.id = u.grup_id
                WHERE COALESCE(u.barkod,'')=?
                LIMIT 1
                """,
                (barkod,),
            )
            row = cur.fetchone()
    except Exception as hata:
        QMessageBox.warning(pencere, "Barkod Hatası", f"Barkod okunamadı:\n{hata}")
        return

    if not row:
        QMessageBox.warning(pencere, "Barkod Bulunamadı", f"Bu barkoda ait ürün bulunamadı:\n{barkod}")
        txt_barkod_oku.selectAll()
        txt_barkod_oku.setFocus()
        return

    urun_id, urun_ad, fiyat, grup_id, grup_ad = row
    durum["grup_id"] = int(grup_id or 0) if grup_id else durum.get("grup_id")
    durum["grup_ad"] = str(grup_ad or durum.get("grup_ad") or "")
    urun_sec_ve_ekle_callback(int(urun_id), str(urun_ad or ""), float(fiyat or 0))
    txt_barkod_oku.clear()
    txt_barkod_oku.setFocus()


def hesapla_toplam(
    *,
    tablo_kalem,
    lbl_toplam,
    lbl_ara_toplam,
    lbl_genel_toplam_kart,
    hesaplama_yapiliyor,
):
    """Recalculate cart totals and update summary labels."""

    if hesaplama_yapiliyor["aktif"]:
        return 0.0
    hesaplama_yapiliyor["aktif"] = True
    toplam = 0.0
    for row in range(tablo_kalem.rowCount()):
        try:
            adet = parse_sayi(tablo_kalem.item(row, 1).text() if tablo_kalem.item(row, 1) else "0")
            fiyat = parse_sayi(tablo_kalem.item(row, 2).text() if tablo_kalem.item(row, 2) else "0")
            tutar = adet * fiyat
        except Exception:
            tutar = 0.0
        toplam += tutar
        item = QTableWidgetItem(para_yaz(tutar))
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        tablo_kalem.setItem(row, 3, item)
    lbl_toplam.setText(f"Genel Toplam\n{para_yaz(toplam)}")
    lbl_ara_toplam.setText(para_yaz(toplam))
    lbl_genel_toplam_kart.setText(para_yaz(toplam))
    hesaplama_yapiliyor["aktif"] = False
    return toplam


def satir_sil(*, tablo_kalem, hesapla_toplam):
    """Remove the selected cart row."""

    row = tablo_kalem.currentRow()
    if row >= 0:
        tablo_kalem.removeRow(row)
        hesapla_toplam()


def liste_temizle(*, tablo_kalem, hesapla_toplam):
    """Clear all cart rows."""

    tablo_kalem.setRowCount(0)
    hesapla_toplam()
