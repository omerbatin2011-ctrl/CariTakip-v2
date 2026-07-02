import json
import re
import urllib.parse
import webbrowser
from datetime import date, datetime, timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from moduller.db import baglan, db_baglan, urun_tablolari_olustur
from moduller.kasa_ui import kasa_tablosu_olustur
from moduller.yardimci import para_yaz


class BarkodluSatisMixin:

    def _barkod_satis_maliyet_kolonlarini_gizle(self, tablo):
        """Barkodlu satış ekranında alış/maliyet/kâr kolonları görünmez."""
        gizli_anahtarlar = ("alış", "alis", "maliyet", "kâr", "kar", "profit")
        try:
            for kolon in range(tablo.columnCount()):
                baslik = tablo.horizontalHeaderItem(kolon)
                metin = baslik.text().lower() if baslik else ""
                if any(anahtar in metin for anahtar in gizli_anahtarlar):
                    tablo.setColumnHidden(kolon, True)
        except Exception:
            pass
    """Kasiyer mantığında çalışan geniş barkodlu satış ekranı."""

    def barkodlu_satis_sayfasi_olustur(self):
        urun_tablolari_olustur()
        try:
            with db_baglan() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS bekleyen_sepetler (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tarih TEXT,
                        cari_id INTEGER,
                        cari_ad TEXT,
                        odeme TEXT,
                        toplam REAL,
                        kalem_sayisi INTEGER,
                        sepet_json TEXT
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS veresiye_hatirlatmalar (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cari_id INTEGER,
                        cari_ad TEXT,
                        telefon TEXT,
                        satis_id INTEGER,
                        hareket_id INTEGER,
                        tarih TEXT,
                        vade_tarihi TEXT,
                        tutar REAL,
                        durum TEXT DEFAULT 'AKTIF',
                        mesaj TEXT
                    )
                """)
        except Exception:
            pass

        sayfa = QFrame()
        sayfa.setStyleSheet("""
            QFrame { background:#F6F8FB; }
            QFrame#Panel {
                background:#FFFFFF;
                border:1px solid #E2E8F0;
                border-radius:14px
            }
            QLabel { color:#0F172A; }
            QLineEdit, QComboBox {
                background:white
                border:1px solid #D8E0EA;
                border-radius:10px
                padding:7px 9px
                font-size:13px
            }
            QLineEdit#BarkodInput {
                font-size:19px
                font-weight:800
                padding:10px 12px
                border:2px solid #2563EB;
                border-radius:12px
            }
            QTableWidget {
                background:white
                border:1px solid #D8E0EA;
                border-radius:10px
                gridline-color:#E5E7EB;
                font-size:13px
            }
            QHeaderView::section {
                background:#F1F5F9;
                color:#334155;
                padding:8px
                border:none
                font-weight:900
            }
            QPushButton {
                background:#2563EB;
                color:white
                border:none
                border-radius:14px
                padding:8px 12px
                font-weight:800
                font-size:13px
            }
            QPushButton:hover { background:#1D4ED8; }
            QPushButton:pressed { background:#1E40AF; padding-top:13px; padding-bottom:11px; }
            QPushButton#GreenButton { background:#16A34A; font-size:13px; padding:7px 10px; border-radius:10px; }
            QPushButton#GreenButton:hover { background:#15803D; }
            QPushButton#OrangeButton { background:#FFFFFF; color:#334155; border:1px solid #CBD5E1; font-size:13px; padding:7px 10px; border-radius:10px; }
            QPushButton#OrangeButton:hover { background:#FFF7ED; border-color:#FDBA74; color:#EA580C; }
            QPushButton#PurpleButton { background:#FFFFFF; color:#334155; border:1px solid #CBD5E1; font-size:13px; padding:7px 10px; border-radius:10px; }
            QPushButton#PurpleButton:hover { background:#F5F3FF; border-color:#C4B5FD; color:#6D28D9; }
            QPushButton#DangerButton { background:#DC2626; }
            QPushButton#DangerButton:hover { background:#B91C1C; }
            QPushButton#GreyButton { background:#FFFFFF; color:#334155; border:1px solid #CBD5E1; }
            QPushButton#GreyButton:hover { background:#F8FAFC; color:#0F172A; }
            QPushButton#LightButton { background:#EFF6FF; color:#1D4ED8; border:1px solid #BFDBFE; }
            QPushButton#LightButton:hover { background:#DBEAFE; }
        """)

        durum = {"cari_id": None, "cari_ad": "Peşin Müşteri", "odeme": "NAKİT"}
        hesaplama_kilit = {"aktif": False}

        ana = QVBoxLayout(sayfa)
        ana.setContentsMargins(14, 12, 14, 12)
        ana.setSpacing(10)

        # Üst başlık ve toplam
        ust = QFrame()
        ust.setObjectName("Panel")
        ust_l = QHBoxLayout(ust)
        ust_l.setContentsMargins(16, 10, 16, 10)
        baslik_l = QVBoxLayout()
        baslik = QLabel("▥ Barkodlu Hızlı Satış")
        baslik.setStyleSheet("font-size:22px;font-weight:900;color:#0F172A;")
        alt = QLabel("Barkodu okutun veya ürün arayın. F2 hızlı ürün arama, F4 cari seçimi, Enter/F8 satışı tamamla.")
        alt.setStyleSheet("font-size:12px;color:#64748B;")
        baslik_l.addWidget(baslik)
        baslik_l.addWidget(alt)
        lblToplam = QLabel("0,00 ₺")
        lblToplam.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lblToplam.setStyleSheet("font-size:30px;font-weight:900;color:#15803D;")
        ust_l.addLayout(baslik_l, 2)
        ust_l.addWidget(lblToplam, 1)
        ana.addWidget(ust)

        govde = QHBoxLayout()
        govde.setSpacing(10)
        ana.addLayout(govde, 1)

        # Sol büyük satış alanı
        sol_panel = QFrame()
        sol_panel.setObjectName("Panel")
        sol = QVBoxLayout(sol_panel)
        sol.setContentsMargins(12, 12, 12, 12)
        sol.setSpacing(8)

        barkod_satir = QHBoxLayout()
        txtBarkod = QLineEdit()
        txtBarkod.setObjectName("BarkodInput")
        txtBarkod.setPlaceholderText("Barkod okut / ürün adı yaz ve Enter")
        btnUrunAra = QPushButton("🔎 Ürün Ara")
        btnSepetTemizle = QPushButton("🧹 Temizle")
        btnSepetTemizle.setObjectName("GreyButton")
        barkod_satir.addWidget(txtBarkod, 5)
        barkod_satir.addWidget(btnUrunAra, 1)
        barkod_satir.addWidget(btnSepetTemizle, 1)
        sol.addLayout(barkod_satir)

        tabloSepet = QTableWidget()
        tabloSepet.setColumnCount(7)
        tabloSepet.setHorizontalHeaderLabels(["Ürün", "Adet", "B. Fiyat", "Tutar", "Grup", "Ürün ID", "Barkod"])
        self._barkod_satis_maliyet_kolonlarini_gizle(tabloSepet)
        headerSepet = tabloSepet.horizontalHeader()
        headerSepet.setStretchLastSection(False)
        headerSepet.setSectionResizeMode(0, QHeaderView.Stretch)
        headerSepet.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        headerSepet.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        headerSepet.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        tabloSepet.setColumnWidth(1, 80)
        tabloSepet.setColumnWidth(2, 120)
        tabloSepet.setColumnWidth(3, 120)
        tabloSepet.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        tabloSepet.setColumnHidden(5, True)
        tabloSepet.setColumnHidden(6, True)
        tabloSepet.setSelectionBehavior(QTableWidget.SelectRows)
        tabloSepet.verticalHeader().setVisible(False)
        sol.addWidget(tabloSepet, 1)

        alt_buton = QHBoxLayout()
        btnAdetArttir = QPushButton("＋ Adet")
        btnAdetAzalt = QPushButton("－ Adet")
        btnSatirSil = QPushButton("🗑 Satır Sil")
        btnSatirSil.setObjectName("DangerButton")
        btnIskonto = QPushButton("% Fiyat Değiştir")
        btnIskonto.setObjectName("OrangeButton")
        alt_buton.addWidget(btnAdetArttir)
        alt_buton.addWidget(btnAdetAzalt)
        alt_buton.addWidget(btnIskonto)
        alt_buton.addWidget(btnSatirSil)
        sol.addLayout(alt_buton)
        govde.addWidget(sol_panel, 4)

        # Sağ kontrol alanı
        sag_panel = QFrame()
        sag_panel.setObjectName("Panel")
        sag = QVBoxLayout(sag_panel)
        sag.setContentsMargins(12, 12, 12, 12)
        sag.setSpacing(8)
        sag_panel.setMinimumWidth(330)
        sag_panel.setMaximumWidth(420)

        lblCari = QLabel("👤 Müşteri: Peşin Müşteri")
        lblCari.setWordWrap(True)
        lblCari.setStyleSheet("background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:8px 10px;font-size:13px;font-weight:800;color:#0F172A;")
        lblCari.setMinimumHeight(44)
        lblCari.setMaximumHeight(64)
        sag.addWidget(lblCari)
        btnCariSec = QPushButton("👥 Cari Seç / Veresiye")
        btnCariTemizle = QPushButton("Peşin Müşteri")
        btnCariTemizle.setObjectName("GreyButton")
        cari_btns = QHBoxLayout()
        cari_btns.setSpacing(8)
        cari_btns.addWidget(btnCariSec)
        cari_btns.addWidget(btnCariTemizle)
        sag.addLayout(cari_btns)

        sag.addWidget(QLabel("Ödeme Tipi"))
        cmbOdeme = QComboBox()
        cmbOdeme.addItems(["NAKİT", "KART", "VERESİYE"])
        sag.addWidget(cmbOdeme)

        ozet = QFrame()
        ozet.setObjectName("Panel")
        ozet.setMaximumHeight(92)
        ozet_l = QGridLayout(ozet)
        ozet_l.setContentsMargins(10, 8, 10, 8)
        ozet_l.setHorizontalSpacing(8)
        ozet_l.setVerticalSpacing(4)
        lblKalemSayisi = QLabel("0")
        lblAraToplam = QLabel("0,00 ₺")
        for lbl in (lblKalemSayisi, lblAraToplam):
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lbl.setMinimumWidth(70)
            lbl.setStyleSheet("font-size:14px;font-weight:900;color:#0F172A;")
        lblKalemText = QLabel("Kalem:")
        lblToplamText = QLabel("Toplam:")
        for _lbl in (lblKalemText, lblToplamText):
            _lbl.setStyleSheet("font-size:13px;font-weight:700;color:#334155;background:transparent;")
        ozet_l.addWidget(lblKalemText, 0, 0)
        ozet_l.addWidget(lblKalemSayisi, 0, 1)
        ozet_l.addWidget(lblToplamText, 1, 0)
        ozet_l.addWidget(lblAraToplam, 1, 1)
        sag.addWidget(ozet)

        btnTamamla = QPushButton("✅ Satışı Tamamla")
        btnTamamla.setObjectName("GreenButton")
        btnTamamla.setMinimumHeight(38)
        btnTamamla.setMaximumHeight(40)
        sag.addWidget(btnTamamla)
        btnBeklet = QPushButton("⏸ Sepeti Beklet")
        btnBeklet.setObjectName("OrangeButton")
        btnBeklet.setMinimumHeight(36)
        btnBeklet.setMaximumHeight(38)
        sag.addWidget(btnBeklet)
        btnBekleyen = QPushButton("🧺 Bekleyen Sepetler")
        btnBekleyen.setObjectName("PurpleButton")
        btnBekleyen.setMinimumHeight(36)
        btnBekleyen.setMaximumHeight(38)
        sag.addWidget(btnBekleyen)
        btnVeresiyeHatirlat = QPushButton("🔔 Veresiye Hatırlat")
        btnVeresiyeHatirlat.setObjectName("LightButton")
        btnVeresiyeHatirlat.setMinimumHeight(34)
        btnVeresiyeHatirlat.setMaximumHeight(36)
        sag.addWidget(btnVeresiyeHatirlat)
        sag.addStretch(1)

        # v88: Kısayol listesi bu sağ panelden kaldırıldı.
        # Sebep: küçük yüksekliklerde panel taşmasına ve amatör görünüme yol açıyordu.
        govde.addWidget(sag_panel, 0)

        def parse_sayi(deger):
            try:
                return float(str(deger or "0").replace("₺", "").replace(".", "").replace(",", ".").strip())
            except Exception:
                return 0.0

        def hesapla():
            if hesaplama_kilit["aktif"]:
                return 0.0
            hesaplama_kilit["aktif"] = True
            toplam = 0.0
            kalem = 0
            for r in range(tabloSepet.rowCount()):
                adet = parse_sayi(tabloSepet.item(r, 1).text() if tabloSepet.item(r, 1) else "0")
                fiyat = parse_sayi(tabloSepet.item(r, 2).text() if tabloSepet.item(r, 2) else "0")
                tutar = adet * fiyat
                toplam += tutar
                kalem += 1
                item = QTableWidgetItem(para_yaz(tutar))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                tabloSepet.setItem(r, 3, item)
            lblToplam.setText(para_yaz(toplam))
            lblAraToplam.setText(para_yaz(toplam))
            lblKalemSayisi.setText(str(kalem))
            hesaplama_kilit["aktif"] = False
            return toplam

        def sepet_urun_ekle(urun):
            urun_id, ad, fiyat, stok, grup_ad, barkod = urun
            for r in range(tabloSepet.rowCount()):
                mevcut_id = tabloSepet.item(r, 5).text() if tabloSepet.item(r, 5) else ""
                if mevcut_id == str(urun_id):
                    adet = parse_sayi(tabloSepet.item(r, 1).text() if tabloSepet.item(r, 1) else "0") + 1
                    if stok is not None and float(stok or 0) < adet:
                        QMessageBox.warning(sayfa, "Stok Yetersiz", f"{ad} için stok yetersiz. Stok: {float(stok or 0):g}")
                        return
                    tabloSepet.setItem(r, 1, QTableWidgetItem(str(int(adet) if adet.is_integer() else adet)))
                    tabloSepet.selectRow(r)
                    hesapla()
                    return
            if stok is not None and float(stok or 0) < 1:
                QMessageBox.warning(sayfa, "Stok Yok", f"{ad} stokta yok.")
                return
            r = tabloSepet.rowCount()
            tabloSepet.insertRow(r)
            tabloSepet.setItem(r, 0, QTableWidgetItem(str(ad or "")))
            tabloSepet.setItem(r, 1, QTableWidgetItem("1"))
            tabloSepet.setItem(r, 2, QTableWidgetItem(str(float(fiyat or 0))))
            tabloSepet.setItem(r, 3, QTableWidgetItem("0"))
            tabloSepet.setItem(r, 4, QTableWidgetItem(str(grup_ad or "")))
            tabloSepet.setItem(r, 5, QTableWidgetItem(str(int(urun_id))))
            tabloSepet.setItem(r, 6, QTableWidgetItem(str(barkod or "")))
            tabloSepet.selectRow(r)
            hesapla()

        def hizli_urun_arama_penceresi():
            """F2 ile açılan geniş hızlı ürün arama penceresi."""
            dlg = QDialog(sayfa)
            dlg.setWindowTitle("Hızlı Ürün Ara")
            dlg.resize(900, 560)
            dlg.setStyleSheet("""
                QDialog { background:#EEF3F8; }
                QLineEdit { background:white;border:2px solid #2563EB;border-radius:12px;padding:12px;font-size:20px;font-weight:900; }
                QTableWidget { background:white;border:1px solid #D8E0EA;border-radius:10px;font-size:14px; }
                QHeaderView::section { background:#F1F5F9;color:#334155;padding:8px;border:none;font-weight:900; }
                QPushButton { background:#2563EB;color:white;border:none;border-radius:12px;padding:10px 14px;font-weight:900; }
                QPushButton:hover { background:#1D4ED8; }
            """)
            layout = QVBoxLayout(dlg)
            lbl = QLabel("Ürün adı veya barkod yazın, Enter ile sepete ekleyin.")
            lbl.setStyleSheet("font-size:14px;color:#475569;font-weight:800;")
            layout.addWidget(lbl)
            txtAra = QLineEdit()
            txtAra.setPlaceholderText("Ürün adı / barkod")
            layout.addWidget(txtAra)
            tbl = QTableWidget()
            tbl.setColumnCount(6)
            tbl.setHorizontalHeaderLabels(["Ürün", "Barkod", "Stok", "Fiyat", "Grup", "ID"])
            self._barkod_satis_maliyet_kolonlarini_gizle(tbl)
            headerAra = tbl.horizontalHeader()
            headerAra.setStretchLastSection(False)
            headerAra.setSectionResizeMode(0, QHeaderView.Stretch)
            headerAra.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            headerAra.setSectionResizeMode(2, QHeaderView.ResizeToContents)
            headerAra.setSectionResizeMode(3, QHeaderView.ResizeToContents)
            tbl.setColumnWidth(1, 140)
            tbl.setColumnWidth(2, 80)
            tbl.setColumnWidth(3, 120)
            tbl.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            tbl.setColumnHidden(5, True)
            tbl.setSelectionBehavior(QTableWidget.SelectRows)
            tbl.setEditTriggers(QTableWidget.NoEditTriggers)
            tbl.verticalHeader().setVisible(False)
            layout.addWidget(tbl, 1)
            alt_l = QHBoxLayout()
            btnEkle = QPushButton("✅ Sepete Ekle")
            btnKapat = QPushButton("Kapat")
            btnKapat.setStyleSheet("background:#64748B;")
            alt_l.addStretch()
            alt_l.addWidget(btnEkle)
            alt_l.addWidget(btnKapat)
            layout.addLayout(alt_l)
            sonuc_rows = []

            def listele():
                nonlocal sonuc_rows
                aranan = txtAra.text().strip()
                try:
                    with baglan() as conn:
                        cur = conn.cursor()
                        if aranan:
                            like = f"%{aranan}%"
                            cur.execute("""
                                SELECT u.id, u.ad, COALESCE(u.varsayilan_fiyat,0), COALESCE(u.stok,0),
                                       COALESCE(g.ad,''), COALESCE(u.barkod,'')
                                FROM urunler u
                                LEFT JOIN urun_gruplari g ON g.id=u.grup_id
                                WHERE u.ad LIKE ? OR COALESCE(u.barkod,'') LIKE ? OR COALESCE(g.ad,'') LIKE ?
                                ORDER BY u.ad
                                LIMIT 100
                            """, (like, like, like))
                        else:
                            cur.execute("""
                                SELECT u.id, u.ad, COALESCE(u.varsayilan_fiyat,0), COALESCE(u.stok,0),
                                       COALESCE(g.ad,''), COALESCE(u.barkod,'')
                                FROM urunler u
                                LEFT JOIN urun_gruplari g ON g.id=u.grup_id
                                ORDER BY u.ad
                                LIMIT 100
                            """)
                        sonuc_rows = cur.fetchall()
                except Exception as hata:
                    QMessageBox.warning(dlg, "Hata", f"Ürün listesi alınamadı:\n{hata}")
                    sonuc_rows = []
                tbl.setRowCount(len(sonuc_rows))
                for r, row in enumerate(sonuc_rows):
                    uid, ad, fiyat, stok, grup, barkod = row
                    veriler = [ad or "", barkod or "", f"{float(stok or 0):g}", para_yaz(float(fiyat or 0)), grup or "", str(uid)]
                    for c, val in enumerate(veriler):
                        it = QTableWidgetItem(str(val))
                        tbl.setItem(r, c, it)
                if sonuc_rows:
                    tbl.selectRow(0)

            def secili_ekle():
                r = tbl.currentRow()
                if r < 0 or r >= len(sonuc_rows):
                    return
                sepet_urun_ekle(sonuc_rows[r])
                dlg.accept()
                txtBarkod.clear()
                txtBarkod.setFocus()

            txtAra.textChanged.connect(listele)
            txtAra.returnPressed.connect(secili_ekle)
            tbl.doubleClicked.connect(lambda *_: secili_ekle())
            btnEkle.clicked.connect(secili_ekle)
            btnKapat.clicked.connect(dlg.reject)
            dlg.keyPressEvent = lambda event: (
                secili_ekle() if event.key() in (Qt.Key_Return, Qt.Key_Enter) else
                dlg.reject() if event.key() == Qt.Key_Escape else
                QDialog.keyPressEvent(dlg, event)
            )
            listele()
            txtAra.setFocus()
            dlg.exec()

        def urun_bul_ve_ekle():
            metin = txtBarkod.text().strip()
            if not metin:
                return
            try:
                with baglan() as conn:
                    cur = conn.cursor()
                    # Önce tam barkod, sonra ürün adı araması.
                    cur.execute("""
                        SELECT u.id, u.ad, COALESCE(u.varsayilan_fiyat,0), COALESCE(u.stok,0),
                               COALESCE(g.ad,''), COALESCE(u.barkod,'')
                        FROM urunler u
                        LEFT JOIN urun_gruplari g ON g.id=u.grup_id
                        WHERE COALESCE(u.barkod,'')=?
                        LIMIT 1
                    """, (metin,))
                    row = cur.fetchone()
                    if not row:
                        like = f"%{metin}%"
                        cur.execute("""
                            SELECT u.id, u.ad, COALESCE(u.varsayilan_fiyat,0), COALESCE(u.stok,0),
                                   COALESCE(g.ad,''), COALESCE(u.barkod,'')
                            FROM urunler u
                            LEFT JOIN urun_gruplari g ON g.id=u.grup_id
                            WHERE u.ad LIKE ? OR COALESCE(u.barkod,'') LIKE ?
                            ORDER BY u.ad
                            LIMIT 20
                        """, (like, like))
                        rows = cur.fetchall()
                        if len(rows) == 1:
                            row = rows[0]
                        elif len(rows) > 1:
                            secenekler = [f"{x[1]} | Stok: {float(x[3] or 0):g} | {para_yaz(float(x[2] or 0))}" for x in rows]
                            secim, ok = QInputDialog.getItem(sayfa, "Ürün Seç", "Birden fazla ürün bulundu:", secenekler, 0, False)
                            if not ok:
                                txtBarkod.selectAll()
                                txtBarkod.setFocus()
                                return
                            row = rows[secenekler.index(secim)]
                    if not row:
                        QMessageBox.warning(sayfa, "Ürün Bulunamadı", f"Ürün/barkod bulunamadı:\n{metin}")
                        txtBarkod.selectAll()
                        txtBarkod.setFocus()
                        return
            except Exception as hata:
                QMessageBox.warning(sayfa, "Hata", f"Ürün aranamadı:\n{hata}")
                return
            sepet_urun_ekle(row)
            txtBarkod.clear()
            txtBarkod.setFocus()

        def secili_satir():
            r = tabloSepet.currentRow()
            if r < 0:
                QMessageBox.warning(sayfa, "Uyarı", "Önce sepetten bir satır seçin.")
                return None
            return r

        def adet_degistir(delta):
            r = secili_satir()
            if r is None:
                return
            adet = parse_sayi(tabloSepet.item(r, 1).text() if tabloSepet.item(r, 1) else "0") + delta
            if adet <= 0:
                tabloSepet.removeRow(r)
            else:
                tabloSepet.setItem(r, 1, QTableWidgetItem(str(int(adet) if adet.is_integer() else adet)))
            hesapla()

        def fiyat_degistir():
            r = secili_satir()
            if r is None:
                return
            mevcut = tabloSepet.item(r, 2).text() if tabloSepet.item(r, 2) else "0"
            yeni, ok = QInputDialog.getDouble(sayfa, "Fiyat Değiştir", "Yeni birim fiyat:", parse_sayi(mevcut), 0, 999999999, 2)
            if ok:
                tabloSepet.setItem(r, 2, QTableWidgetItem(str(yeni)))
                hesapla()

        def satir_sil():
            r = tabloSepet.currentRow()
            if r >= 0:
                tabloSepet.removeRow(r)
                hesapla()

        def sepet_temizle():
            if tabloSepet.rowCount() == 0:
                return
            cevap = QMessageBox.question(sayfa, "Sepeti Temizle", "Sepetteki tüm ürünler silinsin mi?")
            if cevap == QMessageBox.Yes:
                tabloSepet.setRowCount(0)
                hesapla()
                txtBarkod.setFocus()

        def cari_sec():
            try:
                with baglan() as conn:
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT c.id, c.ad, COALESCE(c.telefon,'')
                        FROM cariler c
                                        ORDER BY c.ad
                    """)
                    rows = cur.fetchall()
            except Exception as hata:
                QMessageBox.warning(sayfa, "Hata", f"Cari listesi alınamadı:\n{hata}")
                return
            if not rows:
                QMessageBox.information(sayfa, "Cari Yok", "Kayıtlı cari bulunamadı.")
                return
            secenekler = [f"{ad} | {tel}" for _, ad, tel in rows]
            secim, ok = QInputDialog.getItem(sayfa, "Cari Seç", "Veresiye/cari satış için müşteri seçin:", secenekler, 0, False)
            if not ok:
                return
            cari_id, ad, tel = rows[secenekler.index(secim)]
            durum["cari_id"] = int(cari_id)
            durum["cari_ad"] = str(ad or "")
            durum["odeme"] = "VERESİYE"
            lblCari.setText(f"👤 Müşteri: {durum['cari_ad']}")
            cmbOdeme.setCurrentText("VERESİYE")
            txtBarkod.setFocus()

        def cari_temizle():
            durum["cari_id"] = None
            durum["cari_ad"] = "Peşin Müşteri"
            durum["odeme"] = "NAKİT"
            lblCari.setText("👤 Müşteri: Peşin Müşteri")
            cmbOdeme.setCurrentText("NAKİT")
            txtBarkod.clear()
            txtBarkod.setFocus()

        def satis_tamamla():
            toplam = hesapla()
            if tabloSepet.rowCount() == 0 or toplam <= 0:
                QMessageBox.warning(sayfa, "Uyarı", "Sepette ürün yok veya toplam 0.")
                return
            odeme = cmbOdeme.currentText()
            if odeme == "VERESİYE" and not durum.get("cari_id"):
                QMessageBox.warning(sayfa, "Cari Gerekli", "Veresiye satış için önce cari seçmelisiniz.")
                return

            stok_eksikleri = []
            try:
                with baglan() as conn:
                    cur = conn.cursor()
                    for r in range(tabloSepet.rowCount()):
                        uid = int(tabloSepet.item(r, 5).text())
                        adet = parse_sayi(tabloSepet.item(r, 1).text())
                        cur.execute("SELECT ad, COALESCE(stok,0) FROM urunler WHERE id=?", (uid,))
                        row = cur.fetchone()
                        if row and float(row[1] or 0) < adet:
                            stok_eksikleri.append(f"{row[0]}: stok {float(row[1] or 0):g}, istenen {adet:g}")
            except Exception:
                pass
            if stok_eksikleri:
                QMessageBox.warning(sayfa, "Stok Yetersiz", "Yetersiz stok:\n\n" + "\n".join(stok_eksikleri))
                return

            tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
            notlar = f"Barkodlu hızlı satış - Ödeme: {odeme}"
            hatirlatma_gunu = None
            if odeme == "VERESİYE":
                cevap = QMessageBox.question(
                    sayfa,
                    "Veresiye Hatırlatma",
                    "Bu veresiye satış için WhatsApp metin hatırlatması kurulsun mu?"
                )
                if cevap == QMessageBox.Yes:
                    hatirlatma_gunu, ok = QInputDialog.getInt(
                        sayfa,
                        "Hatırlatma Günü",
                        "Kaç gün sonra hatırlatılsın?",
                        7,
                        0,
                        3650,
                        1
                    )
                    if not ok:
                        hatirlatma_gunu = None
            try:
                kasa_tablosu_olustur()
                with db_baglan() as conn:
                    cur = conn.cursor()
                    hareket_id = None
                    cari_id = durum.get("cari_id")
                    if odeme == "VERESİYE":
                        aciklama = f"Barkodlu hızlı satış\nToplam: {para_yaz(toplam)}"
                        cur.execute(
                            "INSERT INTO hareketler(cari_id, tip, tutar, aciklama, tarih) VALUES (?, 'BORÇ', ?, ?, ?)",
                            (cari_id, toplam, aciklama, tarih)
                        )
                        hareket_id = cur.lastrowid
                    else:
                        # Peşin satışlar da satislar tablosuna yazılsın diye sistemde varsa ilk cariyi kullan.
                        # Cari zorunlu şemayı bozmamak için, seçili cari yoksa 0 yerine Peşin Müşteri carisi oluşturulur.
                        if not cari_id:
                            cur.execute("SELECT id FROM cariler WHERE ad='Peşin Müşteri' LIMIT 1")
                            row = cur.fetchone()
                            if row:
                                cari_id = int(row[0])
                            else:
                                cur.execute("INSERT INTO cariler(ad, telefon, adres) VALUES ('Peşin Müşteri', '', '')")
                                cari_id = cur.lastrowid
                    cur.execute(
                        "INSERT INTO satislar(cari_id, tarih, toplam, notlar, hareket_id, belge_turu) VALUES (?, ?, ?, ?, ?, 'SATIŞ')",
                        (cari_id, tarih, toplam, notlar, hareket_id)
                    )
                    satis_id = cur.lastrowid
                    if odeme == "VERESİYE" and hatirlatma_gunu is not None:
                        cur.execute("SELECT COALESCE(telefon,'') FROM cariler WHERE COALESCE(aktif,1)=1 AND id=?", (cari_id,))
                        tel_row = cur.fetchone()
                        telefon = tel_row[0] if tel_row else ""
                        vade = (date.today() + timedelta(days=int(hatirlatma_gunu))).strftime("%Y-%m-%d")
                        mesaj = (
                            f"Merhaba {durum.get('cari_ad') or ''}, \n"
                            f"{tarih} tarihli veresiye alışverişiniz için hatırlatma: \n"
                            f"Tutar: {para_yaz(toplam)}. \n"
                            f"Ödeme tarihi: {(date.today() + timedelta(days=int(hatirlatma_gunu))).strftime('%d.%m.%Y')}. \n"
                            f"Teşekkür ederiz."
                        )
                        cur.execute(
                            """INSERT INTO veresiye_hatirlatmalar
                               (cari_id, cari_ad, telefon, satis_id, hareket_id, tarih, vade_tarihi, tutar, durum, mesaj)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'AKTIF', ?)""",
                            (cari_id, durum.get('cari_ad') or '', telefon, satis_id, hareket_id, tarih, vade, toplam, mesaj)
                        )
                    if odeme in ("NAKİT", "KART", "HAVALE"):
                        cur.execute(
                            """
                            INSERT INTO kasa_hareketleri(tarih, tip, odeme_tipi, tutar, aciklama, kaynak, kaynak_id, kullanici)
                            VALUES (?, 'GIRIS', ?, ?, ?, 'BARKODLU_SATIS', ?, 'admin')
                            """,
                            (tarih, odeme, toplam, f"Barkodlu satış - {durum.get('cari_ad') or 'Peşin Müşteri'}", satis_id)
                        )
                    for r in range(tabloSepet.rowCount()):
                        urun = tabloSepet.item(r, 0).text()
                        adet = parse_sayi(tabloSepet.item(r, 1).text())
                        fiyat = parse_sayi(tabloSepet.item(r, 2).text())
                        grup = tabloSepet.item(r, 4).text() if tabloSepet.item(r, 4) else ""
                        uid = int(tabloSepet.item(r, 5).text())
                        tutar = adet * fiyat
                        cur.execute(
                            "INSERT INTO satis_kalemleri(satis_id, grup_adi, urun_adi, adet, birim_fiyat, tutar) VALUES (?, ?, ?, ?, ?, ?)",
                            (satis_id, grup, urun, adet, fiyat, tutar)
                        )
                        cur.execute("UPDATE urunler SET stok=COALESCE(stok,0)-? WHERE id=? AND COALESCE(stok,0)>=?", (adet, uid, adet))
                        if cur.rowcount == 0:
                            raise ValueError("Stok güncelleme sırasında yetersiz stok algılandı.")
            except Exception as hata:
                QMessageBox.warning(sayfa, "Satış Kaydedilemedi", str(hata))
                return

            QMessageBox.information(sayfa, "Satış Tamamlandı", f"Satış kaydedildi.\nÖdeme: {odeme}\nToplam: {para_yaz(toplam)}")
            tabloSepet.setRowCount(0)
            hesapla()
            cari_temizle()
            try:
                self.ozet_yukle()
                self.dashboard_ek_bilgileri_yukle()
            except Exception:
                pass

        def sepet_verilerini_al():
            sepet = []
            for r in range(tabloSepet.rowCount()):
                sepet.append({
                    "urun": tabloSepet.item(r, 0).text() if tabloSepet.item(r, 0) else "",
                    "adet": tabloSepet.item(r, 1).text() if tabloSepet.item(r, 1) else "0",
                    "fiyat": tabloSepet.item(r, 2).text() if tabloSepet.item(r, 2) else "0",
                    "grup": tabloSepet.item(r, 4).text() if tabloSepet.item(r, 4) else "",
                    "urun_id": tabloSepet.item(r, 5).text() if tabloSepet.item(r, 5) else "",
                    "barkod": tabloSepet.item(r, 6).text() if tabloSepet.item(r, 6) else "",
                })
            return sepet

        def sepet_yukle(sepet, cari_id=None, cari_ad="Peşin Müşteri", odeme="NAKİT"):
            tabloSepet.setRowCount(0)
            for satir in sepet:
                r = tabloSepet.rowCount()
                tabloSepet.insertRow(r)
                tabloSepet.setItem(r, 0, QTableWidgetItem(str(satir.get("urun", ""))))
                tabloSepet.setItem(r, 1, QTableWidgetItem(str(satir.get("adet", "1"))))
                tabloSepet.setItem(r, 2, QTableWidgetItem(str(satir.get("fiyat", "0"))))
                tabloSepet.setItem(r, 3, QTableWidgetItem("0"))
                tabloSepet.setItem(r, 4, QTableWidgetItem(str(satir.get("grup", ""))))
                tabloSepet.setItem(r, 5, QTableWidgetItem(str(satir.get("urun_id", ""))))
                tabloSepet.setItem(r, 6, QTableWidgetItem(str(satir.get("barkod", ""))))
            durum["cari_id"] = cari_id if cari_id else None
            durum["cari_ad"] = cari_ad or "Peşin Müşteri"
            lblCari.setText(f"👤 Müşteri: {durum['cari_ad']}")
            if odeme in [cmbOdeme.itemText(i) for i in range(cmbOdeme.count())]:
                cmbOdeme.setCurrentText(odeme)
            hesapla()
            if tabloSepet.rowCount() > 0:
                tabloSepet.selectRow(0)
            txtBarkod.setFocus()

        def sepet_beklet():
            toplam = hesapla()
            if tabloSepet.rowCount() == 0:
                QMessageBox.warning(sayfa, "Sepet Boş", "Bekletilecek ürün yok.")
                txtBarkod.setFocus()
                return
            sepet = sepet_verilerini_al()
            tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
            try:
                with db_baglan() as conn:
                    conn.execute(
                        """INSERT INTO bekleyen_sepetler
                           (tarih, cari_id, cari_ad, odeme, toplam, kalem_sayisi, sepet_json)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (tarih, durum.get("cari_id"), durum.get("cari_ad") or "Peşin Müşteri",
                         cmbOdeme.currentText(), toplam, tabloSepet.rowCount(), json.dumps(sepet, ensure_ascii=False))
                    )
                QMessageBox.information(sayfa, "Sepet Bekletildi", "Sepet beklemeye alındı. Yeni satışa devam edebilirsiniz.")
                tabloSepet.setRowCount(0)
                hesapla()
                cari_temizle()
            except Exception as hata:
                QMessageBox.warning(sayfa, "Hata", f"Sepet bekletilemedi:\n{hata}")
            txtBarkod.setFocus()

        def bekleyen_sepetler_penceresi():
            dlg = QDialog(sayfa)
            dlg.setWindowTitle("Bekleyen Sepetler")
            dlg.resize(850, 520)
            dlg.setStyleSheet("""
                QDialog { background:#EEF3F8; }
                QLabel { color:#0F172A; font-weight:900; }
                QTableWidget { background:white;border:1px solid #D8E0EA;border-radius:12px;font-size:14px;gridline-color:#E5E7EB; }
                QHeaderView::section { background:#F1F5F9;color:#334155;padding:8px;border:none;font-weight:900; }
                QPushButton { background:#2563EB;color:white;border:none;border-radius:12px;padding:11px 15px;font-weight:900; }
                QPushButton:hover { background:#1D4ED8; }
                QPushButton#GreenButton { background:#16A34A; }
                QPushButton#GreenButton:hover { background:#15803D; }
                QPushButton#DangerButton { background:#DC2626; }
                QPushButton#DangerButton:hover { background:#B91C1C; }
                QPushButton#GreyButton { background:#FFFFFF; color:#334155; border:1px solid #CBD5E1; }
                QPushButton#GreyButton:hover { background:#F8FAFC; color:#0F172A; }
            """)
            layout = QVBoxLayout(dlg)
            bas = QLabel("🧺 Bekleyen Sepetler")
            bas.setStyleSheet("font-size:22px;color:#1E293B;")
            layout.addWidget(bas)
            tbl = QTableWidget()
            tbl.setColumnCount(6)
            tbl.setHorizontalHeaderLabels(["No", "Tarih", "Müşteri", "Kalem", "Toplam", "Ödeme"])
            tbl.setSelectionBehavior(QTableWidget.SelectRows)
            tbl.setEditTriggers(QTableWidget.NoEditTriggers)
            tbl.setSelectionMode(QAbstractItemView.SingleSelection)
            tbl.verticalHeader().setVisible(False)
            h = tbl.horizontalHeader()
            h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            h.setSectionResizeMode(2, QHeaderView.Stretch)
            h.setSectionResizeMode(3, QHeaderView.ResizeToContents)
            h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
            h.setSectionResizeMode(5, QHeaderView.ResizeToContents)
            layout.addWidget(tbl, 1)
            alt_l = QHBoxLayout()
            btnCagir = QPushButton("✅ Sepeti Geri Çağır")
            btnCagir.setObjectName("GreenButton")
            btnSil = QPushButton("🗑 Bekleyeni Sil")
            btnSil.setObjectName("DangerButton")
            btnKapat = QPushButton("Kapat")
            btnKapat.setObjectName("GreyButton")
            alt_l.addStretch()
            alt_l.addWidget(btnCagir)
            alt_l.addWidget(btnSil)
            alt_l.addWidget(btnKapat)
            layout.addLayout(alt_l)
            rows = []

            def listele():
                nonlocal rows
                try:
                    with db_baglan() as conn:
                        rows = conn.execute(
                            "SELECT id, tarih, cari_id, cari_ad, odeme, toplam, kalem_sayisi, sepet_json FROM bekleyen_sepetler ORDER BY id DESC"
                        ).fetchall()
                except Exception as hata:
                    QMessageBox.warning(dlg, "Hata", f"Bekleyen sepetler alınamadı:\n{hata}")
                    rows = []
                tbl.setRowCount(len(rows))
                for r, row in enumerate(rows):
                    sid, tarih, cari_id, cari_ad, odeme, toplam, kalem, sepet_json = row
                    vals = [sid, tarih or "", cari_ad or "Peşin Müşteri", kalem or 0, para_yaz(float(toplam or 0)), odeme or ""]
                    for c, val in enumerate(vals):
                        it = QTableWidgetItem(str(val))
                        it.setData(Qt.UserRole, sid)
                        tbl.setItem(r, c, it)
                if rows:
                    tbl.selectRow(0)

            def secili_row():
                r = tbl.currentRow()
                if r < 0 or r >= len(rows):
                    QMessageBox.warning(dlg, "Seçim Yok", "Önce bir bekleyen sepet seçin.")
                    return None
                return rows[r]

            def cagir():
                row = secili_row()
                if not row:
                    return
                sid, tarih, cari_id, cari_ad, odeme, toplam, kalem, sepet_json = row
                if tabloSepet.rowCount() > 0:
                    cevap = QMessageBox.question(dlg, "Sepet Dolu", "Mevcut sepet temizlenip bekleyen sepet çağırılsın mı?")
                    if cevap != QMessageBox.Yes:
                        return
                try:
                    sepet = json.loads(sepet_json or "[]")
                    sepet_yukle(sepet, cari_id, cari_ad, odeme)
                    with db_baglan() as conn:
                        conn.execute("DELETE FROM bekleyen_sepetler WHERE id=?", (sid,))
                    dlg.accept()
                except Exception as hata:
                    QMessageBox.warning(dlg, "Hata", f"Sepet çağırılamadı:\n{hata}")

            def sil():
                row = secili_row()
                if not row:
                    return
                sid = row[0]
                cevap = QMessageBox.question(dlg, "Sil", "Seçili bekleyen sepet silinsin mi?")
                if cevap != QMessageBox.Yes:
                    return
                try:
                    with db_baglan() as conn:
                        conn.execute("DELETE FROM bekleyen_sepetler WHERE id=?", (sid,))
                    listele()
                except Exception as hata:
                    QMessageBox.warning(dlg, "Hata", f"Silinemedi:\n{hata}")

            btnCagir.clicked.connect(cagir)
            btnSil.clicked.connect(sil)
            btnKapat.clicked.connect(dlg.reject)
            tbl.doubleClicked.connect(lambda *_: cagir())
            listele()
            dlg.exec()
            txtBarkod.setFocus()

        def veresiye_hatirlatma_penceresi():
            try:
                with db_baglan() as conn:
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS veresiye_hatirlatmalar (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            cari_id INTEGER,
                            cari_ad TEXT,
                            telefon TEXT,
                            satis_id INTEGER,
                            hareket_id INTEGER,
                            tarih TEXT,
                            vade_tarihi TEXT,
                            tutar REAL,
                            durum TEXT DEFAULT 'AKTIF',
                            mesaj TEXT
                        )
                    """)
            except Exception:
                pass

            dlg = QDialog(sayfa)
            dlg.setWindowTitle("Veresiye Hatırlatmaları")
            dlg.resize(980, 560)
            dlg.setStyleSheet("""
                QDialog { background:#EEF3F8; }
                QLabel { color:#0F172A; font-weight:900; }
                QTableWidget { background:white;border:1px solid #D8E0EA;border-radius:12px;font-size:14px;gridline-color:#E5E7EB; }
                QHeaderView::section { background:#F1F5F9;color:#334155;padding:8px;border:none;font-weight:900; }
                QPushButton { background:#2563EB;color:white;border:none;border-radius:12px;padding:11px 15px;font-weight:900; }
                QPushButton:hover { background:#1D4ED8; }
                QPushButton#GreenButton { background:#16A34A; }
                QPushButton#GreenButton:hover { background:#15803D; }
                QPushButton#OrangeButton { background:#FFFFFF; color:#334155; border:1px solid #CBD5E1; font-size:13px; padding:7px 10px; border-radius:10px; }
                QPushButton#OrangeButton:hover { background:#FFF7ED; border-color:#FDBA74; color:#EA580C; }
                QPushButton#DangerButton { background:#DC2626; }
                QPushButton#DangerButton:hover { background:#B91C1C; }
                QPushButton#GreyButton { background:#FFFFFF; color:#334155; border:1px solid #CBD5E1; }
                QPushButton#GreyButton:hover { background:#F8FAFC; color:#0F172A; }
            """)
            layout = QVBoxLayout(dlg)
            bas = QLabel("🔔 Veresiye Hatırlatmaları")
            bas.setStyleSheet("font-size:22px;color:#1E293B;")
            layout.addWidget(bas)
            bilgi = QLabel("Satışta ödeme tipi VERESİYE seçilince hatırlatma kurulabilir. Seçili kayıt için WhatsApp metni kopyalanır veya WhatsApp Web açılır.")
            bilgi.setStyleSheet("font-size:13px;color:#64748B;font-weight:700;")
            layout.addWidget(bilgi)
            tbl = QTableWidget()
            tbl.setColumnCount(8)
            tbl.setHorizontalHeaderLabels(["No", "Vade", "Müşteri", "Telefon", "Tutar", "Durum", "Satış", "Mesaj"])
            tbl.setSelectionBehavior(QTableWidget.SelectRows)
            tbl.setEditTriggers(QTableWidget.NoEditTriggers)
            tbl.setSelectionMode(QAbstractItemView.SingleSelection)
            tbl.verticalHeader().setVisible(False)
            h = tbl.horizontalHeader()
            h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            h.setSectionResizeMode(2, QHeaderView.Stretch)
            h.setSectionResizeMode(3, QHeaderView.ResizeToContents)
            h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
            h.setSectionResizeMode(5, QHeaderView.ResizeToContents)
            h.setSectionResizeMode(6, QHeaderView.ResizeToContents)
            h.setSectionResizeMode(7, QHeaderView.Stretch)
            layout.addWidget(tbl, 1)
            alt_l = QHBoxLayout()
            btnKopyala = QPushButton("📋 WhatsApp Metni Kopyala")
            btnKopyala.setObjectName("GreenButton")
            btnWhatsapp = QPushButton("🟢 WhatsApp Aç")
            btnWhatsapp.setObjectName("OrangeButton")
            btnOdendi = QPushButton("✅ Ödendi/Kapat")
            btnSil = QPushButton("🗑 Sil")
            btnSil.setObjectName("DangerButton")
            btnKapat = QPushButton("Kapat")
            btnKapat.setObjectName("GreyButton")
            alt_l.addStretch()
            alt_l.addWidget(btnKopyala)
            alt_l.addWidget(btnWhatsapp)
            alt_l.addWidget(btnOdendi)
            alt_l.addWidget(btnSil)
            alt_l.addWidget(btnKapat)
            layout.addLayout(alt_l)
            rows = []

            def tarih_goster(v):
                try:
                    return datetime.strptime(v or "", "%Y-%m-%d").strftime("%d.%m.%Y")
                except Exception:
                    return v or ""

            def listele():
                nonlocal rows
                try:
                    with db_baglan() as conn:
                        rows = conn.execute(
                            """SELECT id, cari_id, cari_ad, telefon, satis_id, hareket_id, tarih, vade_tarihi, tutar, durum, mesaj
                               FROM veresiye_hatirlatmalar
                               ORDER BY CASE WHEN durum='AKTIF' THEN 0 ELSE 1 END, vade_tarihi ASC, id DESC"""
                        ).fetchall()
                except Exception as hata:
                    QMessageBox.warning(dlg, "Hata", f"Hatırlatmalar alınamadı:\n{hata}")
                    rows = []
                tbl.setRowCount(len(rows))
                bugun = date.today().strftime("%Y-%m-%d")
                for r, row in enumerate(rows):
                    hid, cari_id, cari_ad, telefon, satis_id, hareket_id, tarih, vade, tutar, durum_, mesaj = row
                    durum_yazi = "GECİKMİŞ" if durum_ == "AKTIF" and (vade or "9999-99-99") < bugun else ("BUGÜN" if durum_ == "AKTIF" and vade == bugun else durum_)
                    vals = [hid, tarih_goster(vade), cari_ad or "", telefon or "", para_yaz(float(tutar or 0)), durum_yazi, satis_id or "", mesaj or ""]
                    for c, val in enumerate(vals):
                        it = QTableWidgetItem(str(val))
                        it.setData(Qt.UserRole, hid)
                        tbl.setItem(r, c, it)
                if rows:
                    tbl.selectRow(0)

            def secili_row():
                r = tbl.currentRow()
                if r < 0 or r >= len(rows):
                    QMessageBox.warning(dlg, "Seçim Yok", "Önce bir hatırlatma seçin.")
                    return None
                return rows[r]

            def secili_mesaj():
                row = secili_row()
                if not row:
                    return None
                hid, cari_id, cari_ad, telefon, satis_id, hareket_id, tarih, vade, tutar, durum_, mesaj = row
                if not mesaj:
                    mesaj = f"Merhaba {cari_ad or ''}, veresiye bakiyeniz için ödeme hatırlatması: {para_yaz(float(tutar or 0))}. Vade: {tarih_goster(vade)}. Teşekkür ederiz."
                return row, mesaj

            def kopyala():
                sonuc = secili_mesaj()
                if not sonuc:
                    return
                row, mesaj = sonuc
                QApplication.clipboard().setText(mesaj)
                QMessageBox.information(dlg, "Kopyalandı", "WhatsApp metni panoya kopyalandı. WhatsApp'a yapıştırıp gönderebilirsiniz.")

            def whatsapp_ac():
                sonuc = secili_mesaj()
                if not sonuc:
                    return
                row, mesaj = sonuc
                telefon = re.sub(r"\D", "", row[3] or "")
                if telefon.startswith("0"):
                    telefon = "90" + telefon[1:]
                elif len(telefon) == 10:
                    telefon = "90" + telefon
                QApplication.clipboard().setText(mesaj)
                if telefon:
                    url = "https://wa.me/" + telefon + "?text=" + urllib.parse.quote(mesaj)
                else:
                    url = "https://web.whatsapp.com/send?text=" + urllib.parse.quote(mesaj)
                webbrowser.open(url)

            def odendi():
                row = secili_row()
                if not row:
                    return
                cevap = QMessageBox.question(dlg, "Kapat", "Bu hatırlatma ödendi/kapatıldı olarak işaretlensin mi?")
                if cevap != QMessageBox.Yes:
                    return
                try:
                    with db_baglan() as conn:
                        conn.execute("UPDATE veresiye_hatirlatmalar SET durum='KAPALI' WHERE id=?", (row[0],))
                    listele()
                except Exception as hata:
                    QMessageBox.warning(dlg, "Hata", f"Güncellenemedi:\n{hata}")

            def sil():
                row = secili_row()
                if not row:
                    return
                cevap = QMessageBox.question(dlg, "Sil", "Seçili hatırlatma silinsin mi?")
                if cevap != QMessageBox.Yes:
                    return
                try:
                    with db_baglan() as conn:
                        conn.execute("DELETE FROM veresiye_hatirlatmalar WHERE id=?", (row[0],))
                    listele()
                except Exception as hata:
                    QMessageBox.warning(dlg, "Hata", f"Silinemedi:\n{hata}")

            btnKopyala.clicked.connect(kopyala)
            btnWhatsapp.clicked.connect(whatsapp_ac)
            btnOdendi.clicked.connect(odendi)
            btnSil.clicked.connect(sil)
            btnKapat.clicked.connect(dlg.reject)
            tbl.doubleClicked.connect(lambda *_: kopyala())
            listele()
            dlg.exec()
            txtBarkod.setFocus()

        def barkod_enter_islemi():
            # Barkod alanı doluysa ürün ekler; boşsa satış tamamlar.
            if txtBarkod.text().strip():
                urun_bul_ve_ekle()
            else:
                satis_tamamla()

        txtBarkod.returnPressed.connect(barkod_enter_islemi)
        btnUrunAra.clicked.connect(hizli_urun_arama_penceresi)
        btnSepetTemizle.clicked.connect(sepet_temizle)
        btnSatirSil.clicked.connect(satir_sil)
        btnAdetArttir.clicked.connect(lambda: adet_degistir(1))
        btnAdetAzalt.clicked.connect(lambda: adet_degistir(-1))
        btnIskonto.clicked.connect(fiyat_degistir)
        btnCariSec.clicked.connect(cari_sec)
        btnCariTemizle.clicked.connect(cari_temizle)
        btnTamamla.clicked.connect(satis_tamamla)
        btnBeklet.clicked.connect(sepet_beklet)
        btnBekleyen.clicked.connect(bekleyen_sepetler_penceresi)
        btnVeresiyeHatirlat.clicked.connect(veresiye_hatirlatma_penceresi)
        tabloSepet.itemChanged.connect(lambda item: hesapla() if item and item.column() in (1, 2) else None)

        sayfa.keyPressEvent = lambda event: (
            btnUrunAra.click() if event.key() == Qt.Key_F2 else
            btnCariSec.click() if event.key() == Qt.Key_F4 else
            btnTamamla.click() if event.key() in (Qt.Key_F8, Qt.Key_Return, Qt.Key_Enter) else
            btnBekleyen.click() if event.key() == Qt.Key_F9 else
            satir_sil() if event.key() == Qt.Key_Delete else
            txtBarkod.setFocus() if event.key() == Qt.Key_Escape else
            QFrame.keyPressEvent(sayfa, event)
        )
        txtBarkod.setFocus()
        return sayfa

