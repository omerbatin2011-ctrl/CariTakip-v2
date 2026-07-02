"""Sales page product and group management actions."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, MutableMapping
from typing import Any

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from moduller.db import baglan, db_baglan
from pages.sales.sales_utils import parse_sayi

SalesState = MutableMapping[str, Any]
ReloadCallback = Callable[[], None]


def grup_ekle(pencere: QWidget, durum: SalesState, gruplari_yukle: ReloadCallback) -> None:
    ad, ok = QInputDialog.getText(pencere, "Grup Ekle", "Ürün grubu adı:")
    if not ok:
        return
    ad = ad.strip()
    if not ad:
        QMessageBox.warning(pencere, "Hata", "Grup adı boş olamaz.")
        return
    try:
        with db_baglan() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO urun_gruplari(ad) VALUES (?)", (ad,))
            durum["grup_id"] = cur.lastrowid
            durum["grup_ad"] = ad
        gruplari_yukle()
    except sqlite3.IntegrityError:
        QMessageBox.warning(pencere, "Hata", "Bu grup zaten var.")


def grup_duzenle(pencere: QWidget, durum: SalesState, gruplari_yukle: ReloadCallback) -> None:
    if durum["grup_id"] is None:
        QMessageBox.warning(pencere, "Uyarı", "Önce bir grup seçin.")
        return
    yeni_ad, ok = QInputDialog.getText(
        pencere,
        "Grup Adını Düzenle",
        "Yeni grup adı:",
        text=durum["grup_ad"] or "",
    )
    if not ok:
        return
    yeni_ad = yeni_ad.strip()
    if not yeni_ad:
        return
    try:
        with db_baglan() as conn:
            conn.execute("UPDATE urun_gruplari SET ad=? WHERE id=?", (yeni_ad, durum["grup_id"]))
        durum["grup_ad"] = yeni_ad
        gruplari_yukle()
    except sqlite3.IntegrityError:
        QMessageBox.warning(pencere, "Hata", "Bu grup adı zaten var.")


def grup_sil(pencere: QWidget, durum: SalesState, gruplari_yukle: ReloadCallback) -> None:
    if durum["grup_id"] is None:
        return
    cevap = QMessageBox.question(
        pencere,
        "Silme Onayı",
        f"'{durum['grup_ad']}' grubu ve içindeki ürünler silinsin mi?",
    )
    if cevap != QMessageBox.Yes:
        return
    with db_baglan() as conn:
        conn.execute("DELETE FROM urun_gruplari WHERE id=?", (durum["grup_id"],))
    durum["grup_id"] = None
    durum["grup_ad"] = None
    durum["urun_id"] = None
    durum["urun_ad"] = None
    gruplari_yukle()


def urun_formu_ac(
    pencere: QWidget,
    baslik: str,
    mevcut_ad: str = "",
    mevcut_fiyat: str = "",
    mevcut_stok: str = "",
    mevcut_barkod: str = "",
) -> dict[str, Any]:
    form = QDialog(pencere)
    form.setWindowTitle(baslik)
    form.resize(560, 420)
    ly = QVBoxLayout()

    lbl = QLabel(baslik)
    lbl.setStyleSheet("font-size:22px;font-weight:800;color:#1E293B;padding:8px;")
    ly.addWidget(lbl)

    ly.addWidget(QLabel("Ürün Adı"))
    txtAd = QLineEdit()
    txtAd.setText(mevcut_ad or "")
    txtAd.setPlaceholderText("Örn: AHD Kamera, 5 MP IP Kamera, DVR 8 Kanal...")
    txtAd.setMinimumHeight(42)
    ly.addWidget(txtAd)

    ly.addWidget(QLabel("Varsayılan Satış Fiyatı"))
    txtFiyat = QLineEdit()
    txtFiyat.setText(str(mevcut_fiyat or ""))
    txtFiyat.setPlaceholderText("Örn: 1750 veya 1750,50")
    txtFiyat.setMinimumHeight(42)
    ly.addWidget(txtFiyat)

    ly.addWidget(QLabel("Mevcut Stok"))
    txtStok = QLineEdit()
    txtStok.setText(str(mevcut_stok or "0"))
    txtStok.setPlaceholderText("Örn: 10")
    txtStok.setMinimumHeight(42)
    ly.addWidget(txtStok)

    ly.addWidget(QLabel("Barkod"))
    txtBarkod = QLineEdit()
    txtBarkod.setText(str(mevcut_barkod or ""))
    txtBarkod.setPlaceholderText("Örn: 8691234567890 / barkod okuyucu ile okut")
    txtBarkod.setMinimumHeight(42)
    ly.addWidget(txtBarkod)

    btns = QHBoxLayout()
    btnKaydet = QPushButton("Kaydet")
    btnIptal = QPushButton("İptal")
    btnIptal.setObjectName("GreyButton")
    btns.addWidget(btnKaydet)
    btns.addWidget(btnIptal)
    ly.addLayout(btns)

    sonuc = {"ok": False, "ad": "", "fiyat": 0.0, "stok": 0.0, "barkod": ""}

    def kaydet_form() -> None:
        ad = txtAd.text().strip()
        if not ad:
            QMessageBox.warning(form, "Hata", "Ürün adı boş olamaz.")
            return
        try:
            fiyat = parse_sayi(txtFiyat.text().strip() or "0")
            stok = parse_sayi(txtStok.text().strip() or "0")
        except Exception:
            QMessageBox.warning(form, "Hata", "Fiyat ve stok sayısal olmalı.")
            return
        barkod = txtBarkod.text().strip()
        sonuc.update({"ok": True, "ad": ad, "fiyat": fiyat, "stok": stok, "barkod": barkod})
        form.accept()

    btnKaydet.clicked.connect(kaydet_form)
    btnIptal.clicked.connect(form.reject)
    form.setLayout(ly)
    txtAd.setFocus()
    form.exec()
    return sonuc


def urun_ekle(pencere: QWidget, durum: SalesState, urunleri_yukle: ReloadCallback) -> None:
    if durum["grup_id"] is None:
        QMessageBox.warning(pencere, "Hata", "Önce ürün grubu seçin veya ekleyin.")
        return
    sonuc = urun_formu_ac(pencere, "Ürün Ekle")
    if not sonuc["ok"]:
        return
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO urunler(grup_id, ad, varsayilan_fiyat, stok, barkod) VALUES (?, ?, ?, ?, ?)",
            (
                durum["grup_id"],
                sonuc["ad"],
                sonuc["fiyat"],
                sonuc["stok"],
                sonuc["barkod"],
            ),
        )
        durum["urun_id"] = cur.lastrowid
        durum["urun_ad"] = sonuc["ad"]
        durum["urun_fiyat"] = sonuc["fiyat"]
    urunleri_yukle()


def urun_duzenle(pencere: QWidget, durum: SalesState, urunleri_yukle: ReloadCallback) -> None:
    if durum["urun_id"] is None:
        QMessageBox.warning(pencere, "Uyarı", "Önce düzenlenecek ürüne tıklayın.")
        return
    mevcut_stok = 0
    try:
        with baglan() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT COALESCE(stok,0), COALESCE(barkod,'') FROM urunler WHERE id=?",
                (durum["urun_id"],),
            )
            row_stok = cur.fetchone()
            mevcut_stok = row_stok[0] if row_stok else 0
            mevcut_barkod = row_stok[1] if row_stok else ""
    except Exception:
        mevcut_stok = 0
        mevcut_barkod = ""
    sonuc = urun_formu_ac(
        pencere,
        "Ürün Düzenle",
        durum["urun_ad"] or "",
        str(durum.get("urun_fiyat") or ""),
        str(mevcut_stok),
        str(mevcut_barkod),
    )
    if not sonuc["ok"]:
        return
    with db_baglan() as conn:
        conn.execute(
            "UPDATE urunler SET ad=?, varsayilan_fiyat=?, stok=?, barkod=? WHERE id=?",
            (sonuc["ad"], sonuc["fiyat"], sonuc["stok"], sonuc["barkod"], durum["urun_id"]),
        )
    durum["urun_ad"] = sonuc["ad"]
    durum["urun_fiyat"] = sonuc["fiyat"]
    urunleri_yukle()


def urun_sil(pencere: QWidget, durum: SalesState, urunleri_yukle: ReloadCallback) -> None:
    if durum["urun_id"] is None:
        QMessageBox.warning(pencere, "Uyarı", "Silmek için önce bir ürüne tıklayın.")
        return
    cevap = QMessageBox.question(pencere, "Silme Onayı", f"'{durum['urun_ad']}' ürünü silinsin mi?")
    if cevap != QMessageBox.Yes:
        return
    with db_baglan() as conn:
        conn.execute("DELETE FROM urunler WHERE id=?", (durum["urun_id"],))
    durum["urun_id"] = None
    durum["urun_ad"] = None
    durum["urun_fiyat"] = 0.0
    urunleri_yukle()
