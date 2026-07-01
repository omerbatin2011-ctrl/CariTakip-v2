from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from moduller.db import baglan, db_baglan, urun_tablolari_olustur
from moduller.sistem import master_sifre_dogrula
from moduller.yardimci import para_yaz

try:
    from kur_modulu import tcmb_usd_kuru_al, tl_karsiligi_hesapla
except Exception:
    tcmb_usd_kuru_al = None

    def tl_karsiligi_hesapla(tutar, para_birimi="TL", kur=1):
        try:
            tutar = float(tutar or 0)
            kur = float(kur or 1)
        except Exception:
            return 0.0
        return tutar if str(para_birimi).upper() == "TL" else tutar * kur


class UrunStokIslemlerMixin:
    """Ürün alışları, stok raporu ve stok düzeltme işlemleri."""

    def alis_sayfasi_olustur(self):
        sayfa = QFrame()
        sayfa.setStyleSheet("background:#F8FAFC;")
        layout = QVBoxLayout()
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(14)
        baslik = QLabel("🔒 Şifreli Ürün Alış / Tedarikçi Girişi")
        baslik.setStyleSheet("font-size:24px;font-weight:800;color:#0F172A;")
        aciklama = QLabel("Bu bölüm ana şifre ile açılır. Açıldıktan sonra aynı ana pencere içinde çalışır.")
        aciklama.setStyleSheet("color:#64748B;font-size:14px;")
        btnAc = QPushButton("🔓 Ana Şifreyle Aç")
        btnAc.setObjectName("PrimaryButton")
        btnAc.setEnabled(True)
        btnAc.setMinimumWidth(220)
        btnAc.setMaximumWidth(260)
        btnAc.setMinimumHeight(44)
        btnAc.setStyleSheet("""
            QPushButton#PrimaryButton {
                background:#4F46E5;
                color:#FFFFFF;
                border:none;
                border-radius:14px;
                padding:10px 16px;
                font-size:14px;
                font-weight:900;
            }
            QPushButton#PrimaryButton:hover { background:#4338CA; }
            QPushButton#PrimaryButton:disabled {
                background:#CBD5E1;
                color:#334155;
            }
        """)
        icerik = QFrame()
        icerik.setObjectName("MainCard")
        icerik_l = QVBoxLayout()
        icerik_l.setContentsMargins(18, 18, 18, 18)
        icerik_l.addWidget(aciklama)
        icerik_l.addWidget(btnAc)
        icerik_l.addStretch()
        icerik.setLayout(icerik_l)

        def ac():
            dlg = self.urun_alis_penceresi(embedded=True)
            if dlg is None:
                return
            while icerik_l.count():
                item = icerik_l.takeAt(0)
                w = item.widget()
                if w:
                    w.setParent(None)
            icerik_l.addWidget(dlg)
            dlg.show()

        btnAc.clicked.connect(ac)
        layout.addWidget(baslik)
        layout.addWidget(icerik, 1)
        sayfa.setLayout(layout)
        return sayfa




    def stok_raporu_penceresi(self):
        urun_tablolari_olustur()
        pencere = QDialog(self)
        pencere.setWindowTitle("Stok Raporu")
        pencere.resize(900, 600)
        pencere.setStyleSheet("""
            QDialog { background:#EEF3F8; }
            QPushButton { background:#0D47A1; color:white; border:none; border-radius:8px; padding:10px; font-weight:bold; }
            QTableWidget { background:white; border:1px solid #D8E0EA; border-radius:8px; }
            QLineEdit { background:white; border:1px solid #CBD5E1; border-radius:8px; padding:8px; }
        """)
        layout = QVBoxLayout()
        baslik = QLabel("STOK RAPORU")
        baslik.setStyleSheet("font-size:24px;font-weight:bold;color:#0D47A1;padding:8px;")
        layout.addWidget(baslik)

        filtre = QHBoxLayout()
        txtAra = QLineEdit()
        txtAra.setPlaceholderText("Ürün veya grup ara...")
        btnYenile = QPushButton("Yenile")
        filtre.addWidget(txtAra, 1)
        filtre.addWidget(btnYenile)
        layout.addLayout(filtre)

        tablo = QTableWidget()
        tablo.setColumnCount(5)
        tablo.setHorizontalHeaderLabels(["Ürün", "Grup", "Satış Fiyatı", "Stok", "Durum"])
        tablo.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tablo.setSelectionBehavior(QTableWidget.SelectRows)
        tablo.setEditTriggers(QTableWidget.NoEditTriggers)
        tablo.verticalHeader().setVisible(False)
        layout.addWidget(tablo, 1)

        lblOzet = QLabel("")
        lblOzet.setStyleSheet("background:white;border:1px solid #D8E0EA;border-radius:8px;padding:10px;font-weight:bold;color:#0D47A1;")
        layout.addWidget(lblOzet)

        alt = QHBoxLayout()
        btnKapat = QPushButton("Kapat")
        btnKapat.clicked.connect(pencere.close)
        alt.addStretch()
        alt.addWidget(btnKapat)
        layout.addLayout(alt)

        def yukle():
            arama = txtAra.text().strip()
            with baglan() as conn:
                cur = conn.cursor()
                if arama:
                    like = f"%{arama}%"
                    cur.execute("""
                        SELECT u.ad, COALESCE(g.ad,''), COALESCE(u.varsayilan_fiyat,0), COALESCE(u.stok,0)
                        FROM urunler u
                        LEFT JOIN urun_gruplari g ON g.id=u.grup_id
                        WHERE u.ad LIKE ? OR g.ad LIKE ?
                        ORDER BY g.ad, u.ad
                    """, (like, like))
                else:
                    cur.execute("""
                        SELECT u.ad, COALESCE(g.ad,''), COALESCE(u.varsayilan_fiyat,0), COALESCE(u.stok,0)
                        FROM urunler u
                        LEFT JOIN urun_gruplari g ON g.id=u.grup_id
                        ORDER BY g.ad, u.ad
                    """)
                rows = cur.fetchall()
            tablo.setRowCount(len(rows))
            kritik = 0
            toplam_stok = 0.0
            for r, (urun, grup, fiyat, stok) in enumerate(rows):
                stok = float(stok or 0)
                toplam_stok += stok
                durum = "Kritik" if stok <= 0 else ("Az" if stok <= 3 else "Normal")
                if stok <= 3:
                    kritik += 1
                vals = [urun or "", grup or "", para_yaz(float(fiyat or 0)), str(int(stok) if stok.is_integer() else stok), durum]
                for c, v in enumerate(vals):
                    tablo.setItem(r, c, QTableWidgetItem(str(v)))
            lblOzet.setText(f"Toplam ürün: {len(rows)}    |    Toplam stok adedi: {toplam_stok:g}    |    Kritik/Az stok: {kritik}")

        txtAra.textChanged.connect(yukle)
        btnYenile.clicked.connect(yukle)
        yukle()
        pencere.setLayout(layout)
        pencere.exec()

    def urun_alis_penceresi(self, embedded=False):
        # Şifreli bölüm: ana yönetici şifresi olmadan açılmaz.
        master, ok = QInputDialog.getText(self, "Ana Şifre", "Ürün alış bölümünü açmak için ana şifreyi girin:", QLineEdit.Password)
        if not ok:
            return
        if not master_sifre_dogrula(master.strip()):
            QMessageBox.warning(self, "Hata", "Ana şifre yanlış.")
            return

        urun_tablolari_olustur()
        pencere = QDialog(self)
        pencere.setWindowTitle("Ürün Girişi / Stok Artır")
        ekran = QGuiApplication.primaryScreen().availableGeometry()
        pencere.resize(min(1160, ekran.width() - 80), min(760, ekran.height() - 80))
        pencere.setMinimumSize(880, 560)
        pencere.setStyleSheet("""
            QDialog { background:#F3F4F6; }
            QFrame#Panel { background:white;border:1px solid #D8E0EA;border-radius:16px; }
            QLabel { color:#0F172A; font-size:13px; background:transparent; }
            QPushButton { background:#2563EB;color:white;border:none;border-radius:10px;padding:7px 12px;font-weight:800;min-height:34px; }
            QPushButton:hover { background:#1D4ED8; }
            QPushButton#GreenButton { background:#16A34A; }
            QPushButton#GreenButton:hover { background:#15803D; }
            QPushButton#OrangeButton { background:#F97316; }
            QPushButton#OrangeButton:hover { background:#EA580C; }
            QPushButton#DarkButton { background:#1E293B; }
            QLineEdit, QComboBox { background:white;border:1px solid #CBD5E1;border-radius:10px;padding:8px 10px;min-height:36px;font-size:13px; }
            QTextEdit { background:white;border:1px solid #CBD5E1;border-radius:10px;padding:8px 10px;font-size:13px; }
            QTableWidget { background:white;border:1px solid #D8E0EA;border-radius:10px; font-size:12px; }
            QHeaderView::section { background:#F8FAFC; padding:7px; font-weight:bold; border:0; }
            QScrollArea { border:none; background:transparent; }
            QScrollBar:vertical { background:#F1F5F9;width:10px;border-radius:5px; }
            QScrollBar::handle:vertical { background:#CBD5E1;border-radius:5px;min-height:28px; }
        """)
        ana = QVBoxLayout()
        ana.setContentsMargins(12, 12, 12, 12)
        ana.setSpacing(10)
        # Ana sayfada zaten başlık olduğu için gömülü kullanımda ikinci başlığı göstermiyoruz.
        if not embedded:
            baslik = QLabel("ŞİFRELİ ÜRÜN ALIŞ / TEDARİKÇİ GİRİŞİ")
            baslik.setStyleSheet("font-size:18px;font-weight:bold;color:#0D47A1;")
            ana.addWidget(baslik)

        sekmeler = QTabWidget()
        sekmeler.setDocumentMode(True)
        sekmeler.setStyleSheet("""
            QTabWidget::pane { border:1px solid #D8E0EA; border-radius:10px; background:white; }
            QTabBar::tab { background:#E5E7EB; color:#0F172A; padding:8px 16px; margin-right:4px; border-top-left-radius:8px; border-top-right-radius:8px; font-weight:800; }
            QTabBar::tab:selected { background:#0D47A1; color:white; }
        """)
        tab_giris = QWidget()
        tab_giris_layout = QVBoxLayout()
        tab_giris_layout.setContentsMargins(8, 8, 8, 8)
        tab_giris_layout.setSpacing(6)
        govde = QHBoxLayout()
        govde.setSpacing(10)

        sol_panel = QFrame()
        sol_panel.setObjectName("Panel")
        sol = QVBoxLayout()
        sol.setContentsMargins(9, 8, 9, 8)
        sol.setSpacing(4)
        sol.addWidget(QLabel("Ürün Ara"))
        txtUrunAra = QLineEdit()
        txtUrunAra.setPlaceholderText("Ürün adı ara...")
        sol.addWidget(txtUrunAra)
        tabloUrun = QTableWidget()
        tabloUrun.setColumnCount(7)
        tabloUrun.setHorizontalHeaderLabels(["Ürün", "Grup", "Satış Fiyatı", "Son Alış TL", "Kâr/Adet", "Stok", "ID"])
        tabloUrun.setColumnHidden(6, True)
        tabloUrun.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tabloUrun.verticalHeader().setDefaultSectionSize(26)
        tabloUrun.setAlternatingRowColors(True)
        tabloUrun.setSelectionBehavior(QTableWidget.SelectRows)
        tabloUrun.setEditTriggers(QTableWidget.NoEditTriggers)
        tabloUrun.verticalHeader().setVisible(False)
        sol.addWidget(tabloUrun, 1)
        sol_panel.setLayout(sol)
        govde.addWidget(sol_panel, 4)

        sag_panel = QFrame()
        sag_panel.setObjectName("Panel")
        sag = QVBoxLayout()
        sag.setContentsMargins(16, 14, 16, 14)
        sag.setSpacing(8)
        sag_panel.setMinimumWidth(430)
        sag_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        lblSecili = QLabel("📦 Seçili Ürün: Yok")
        lblSecili.setStyleSheet("font-size:14px;font-weight:900;color:#0F172A;background:#F8FAFC;border:1px solid #D8E0EA;border-radius:12px;padding:10px;")
        lblSecili.setMinimumHeight(58)
        lblSecili.setWordWrap(True)
        sag.addWidget(lblSecili)
        lblKar = QLabel("Satış / son alış / kâr bilgileri burada görünür.")
        lblKar.setStyleSheet("font-size:12px;color:#334155;background:#F8FAFC;border:1px solid #D8E0EA;border-radius:12px;padding:8px;")
        lblKar.setMinimumHeight(46)
        lblKar.setWordWrap(True)
        sag.addWidget(lblKar)
        sag.addWidget(QLabel("Aldığımız Firma / Tedarikçi"))
        txtTedarikci = QLineEdit()
        txtTedarikci.setPlaceholderText("Örn: ABC Elektronik")
        sag.addWidget(txtTedarikci)
        sag.addWidget(QLabel("Adet / Stok Girişi"))
        txtAdet = QLineEdit()
        txtAdet.setPlaceholderText("Örn: 10")
        sag.addWidget(txtAdet)

        sag.addWidget(QLabel("Para Birimi"))
        cmbParaBirimi = QComboBox()
        cmbParaBirimi.addItems(["TL", "USD"])
        sag.addWidget(cmbParaBirimi)

        sag.addWidget(QLabel("Belge Durumu"))
        cmbFaturaDurumu = QComboBox()
        cmbFaturaDurumu.addItems(["FATURALI", "FATURASIZ"])
        cmbFaturaDurumu.setToolTip("Bu stok girişinin faturalı mı faturasız mı olduğunu seçin.")
        sag.addWidget(cmbFaturaDurumu)

        kur_satiri = QHBoxLayout()
        txtKur = QLineEdit()
        txtKur.setPlaceholderText("Kur")
        txtKur.setText("1")
        btnKurAl = QPushButton("TCMB USD Kurunu Al")
        btnKurAl.setMinimumHeight(38)
        btnKurAl.setMaximumHeight(44)
        kur_satiri.addWidget(txtKur, 1)
        kur_satiri.addWidget(btnKurAl, 2)
        sag.addLayout(kur_satiri)

        sag.addWidget(QLabel("Alış Fiyatı (seçilen para birimiyle)"))
        txtAlisFiyat = QLineEdit()
        txtAlisFiyat.setPlaceholderText("Örn: 1250 veya 100 USD")
        sag.addWidget(txtAlisFiyat)
        lblTlKarsilik = QLabel("TL Karşılığı: 0,00 ₺")
        lblTlKarsilik.setStyleSheet("font-size:13px;font-weight:900;color:#15803D;background:#ECFDF5;border:1px solid #BBF7D0;border-radius:10px;padding:8px;")
        lblTlKarsilik.setMinimumHeight(38)
        sag.addWidget(lblTlKarsilik)
        sag.addWidget(QLabel("Açıklama"))
        txtAciklama = QTextEdit()
        txtAciklama.setMinimumHeight(90)
        sag.addWidget(txtAciklama)
        btnKaydet = QPushButton("💾 Ürün Girişini Kaydet / Stok Artır")
        btnKaydet.setObjectName("GreenButton")
        btnKaydet.setMinimumHeight(42)
        sag.addWidget(btnKaydet)
        btnStokDuzelt = QPushButton("✏️ Seçili Ürün Stok Düzelt")
        btnStokDuzelt.setObjectName("OrangeButton")
        btnStokDuzelt.setMinimumHeight(40)
        sag.addWidget(btnStokDuzelt)
        btnKapat = QPushButton("✕ Kapat")
        btnKapat.setObjectName("DarkButton")
        btnKapat.clicked.connect(pencere.close)
        sag.addWidget(btnKapat)
        sag.addSpacing(8)
        sag_panel.setLayout(sag)

        sag_scroll = QScrollArea()
        sag_scroll.setWidgetResizable(True)
        sag_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sag_scroll.setWidget(sag_panel)
        sag_scroll.setMinimumWidth(450)
        sag_scroll.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        govde.addWidget(sag_scroll, 3)
        tab_giris_layout.addLayout(govde, 1)
        tab_giris.setLayout(tab_giris_layout)
        sekmeler.addTab(tab_giris, "📥 Ürün Alış Girişi")

        # 2. sekme: responsive ürün kâr/zarar listesi
        tab_kar = QWidget()
        tab_kar_layout = QVBoxLayout()
        tab_kar_layout.setContentsMargins(8, 8, 8, 8)
        tab_kar_layout.setSpacing(6)

        kar_ust = QHBoxLayout()
        lblKarBaslik = QLabel("Ürün Kâr / Zarar Listesi")
        lblKarBaslik.setStyleSheet("font-size:16px;font-weight:900;color:#0D47A1;")
        txtKarAra = QLineEdit()
        txtKarAra.setPlaceholderText("Ürün / grup ara...")
        txtKarAra.setMaximumWidth(360)
        btnKarYenile = QPushButton("↻ Yenile")
        btnKarYenile.setMaximumWidth(120)
        kar_ust.addWidget(lblKarBaslik)
        kar_ust.addStretch()
        kar_ust.addWidget(txtKarAra)
        kar_ust.addWidget(btnKarYenile)
        tab_kar_layout.addLayout(kar_ust)

        lblKarOzet = QLabel("Toplam ürün: 0  |  Stok maliyeti: 0,00 ₺  |  Tahmini kâr: 0,00 ₺")
        lblKarOzet.setStyleSheet("background:#F3F4F6;border:1px solid #E5E7EB;border-radius:8px;padding:6px;font-weight:800;color:#0F172A;")
        tab_kar_layout.addWidget(lblKarOzet)

        tabloGecmis = QTableWidget()
        tabloGecmis.setColumnCount(9)
        tabloGecmis.setHorizontalHeaderLabels(["Ürün", "Grup", "Stok", "Son Alış TL", "Satış", "Kâr/Adet", "Stok Maliyeti", "Tahmini Kâr", "Durum"])
        tabloGecmis.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tabloGecmis.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        tabloGecmis.setColumnWidth(0, 260)
        tabloGecmis.setEditTriggers(QTableWidget.NoEditTriggers)
        tabloGecmis.verticalHeader().setVisible(False)
        tabloGecmis.verticalHeader().setDefaultSectionSize(26)
        tabloGecmis.setAlternatingRowColors(True)
        tabloGecmis.setSelectionBehavior(QTableWidget.SelectRows)
        tab_kar_layout.addWidget(tabloGecmis, 1)
        tab_kar.setLayout(tab_kar_layout)
        sekmeler.addTab(tab_kar, "📊 Ürün Kâr / Zarar Listesi")
        ana.addWidget(sekmeler, 1)

        durum = {"urun": None}

        def urun_listele():
            arama = txtUrunAra.text().strip()
            conn = baglan()
            cur = conn.cursor()
            if arama:
                like = f"%{arama}%"
                cur.execute("""
                    SELECT u.id, u.ad, COALESCE(g.ad,''), COALESCE(u.varsayilan_fiyat,0), COALESCE(u.stok,0),
                           COALESCE((SELECT CASE WHEN COALESCE(ua.alis_fiyati_tl,0)>0 THEN ua.alis_fiyati_tl ELSE ua.alis_fiyati END FROM urun_alislari ua WHERE ua.urun_id=u.id ORDER BY ua.id DESC LIMIT 1), 0)
                    FROM urunler u LEFT JOIN urun_gruplari g ON g.id=u.grup_id
                    WHERE u.ad LIKE ? ORDER BY u.ad
                """, (like,))
            else:
                cur.execute("""
                    SELECT u.id, u.ad, COALESCE(g.ad,''), COALESCE(u.varsayilan_fiyat,0), COALESCE(u.stok,0),
                           COALESCE((SELECT CASE WHEN COALESCE(ua.alis_fiyati_tl,0)>0 THEN ua.alis_fiyati_tl ELSE ua.alis_fiyati END FROM urun_alislari ua WHERE ua.urun_id=u.id ORDER BY ua.id DESC LIMIT 1), 0)
                    FROM urunler u LEFT JOIN urun_gruplari g ON g.id=u.grup_id ORDER BY u.ad
                """)
            rows = cur.fetchall()
            conn.close()
            tabloUrun.setRowCount(len(rows))
            for r, (uid, ad, grup, fiyat, stok, son_alis) in enumerate(rows):
                satis_f = float(fiyat or 0)
                son_alis_f = float(son_alis or 0)
                kar_f = satis_f - son_alis_f if son_alis_f > 0 else 0
                tabloUrun.setItem(r, 0, QTableWidgetItem(ad or ""))
                tabloUrun.setItem(r, 1, QTableWidgetItem(grup or ""))
                tabloUrun.setItem(r, 2, QTableWidgetItem(para_yaz(satis_f)))
                tabloUrun.setItem(r, 3, QTableWidgetItem(para_yaz(son_alis_f) if son_alis_f > 0 else "-"))
                tabloUrun.setItem(r, 4, QTableWidgetItem(para_yaz(kar_f) if son_alis_f > 0 else "-"))
                tabloUrun.setItem(r, 5, QTableWidgetItem(str(float(stok or 0)).rstrip('0').rstrip('.')))
                tabloUrun.setItem(r, 6, QTableWidgetItem(str(uid)))

        def gecmis_listele():
            arama = txtKarAra.text().strip() if 'txtKarAra' in locals() else ""
            conn = baglan()
            cur = conn.cursor()
            params = []
            where = ""
            if arama:
                where = "WHERE u.ad LIKE ? OR COALESCE(g.ad,'') LIKE ?"
                like = f"%{arama}%"
                params = [like, like]
            if arama:
                cur.execute("""
                    SELECT
                        u.ad,
                        COALESCE(g.ad,''),
                        COALESCE(u.stok,0),
                        COALESCE((
                            SELECT CASE WHEN COALESCE(ua.alis_fiyati_tl,0)>0 THEN ua.alis_fiyati_tl ELSE ua.alis_fiyati END
                            FROM urun_alislari ua
                            WHERE ua.urun_id=u.id
                            ORDER BY ua.id DESC LIMIT 1
                        ),0) AS son_alis_tl,
                        COALESCE(u.varsayilan_fiyat,0) AS satis_fiyati
                    FROM urunler u
                    LEFT JOIN urun_gruplari g ON g.id=u.grup_id
                    WHERE u.ad LIKE ? OR COALESCE(g.ad,'') LIKE ?
                    ORDER BY u.ad
                """, params)
            else:
                cur.execute("""
                    SELECT
                        u.ad,
                        COALESCE(g.ad,''),
                        COALESCE(u.stok,0),
                        COALESCE((
                            SELECT CASE WHEN COALESCE(ua.alis_fiyati_tl,0)>0 THEN ua.alis_fiyati_tl ELSE ua.alis_fiyati END
                            FROM urun_alislari ua
                            WHERE ua.urun_id=u.id
                            ORDER BY ua.id DESC LIMIT 1
                        ),0) AS son_alis_tl,
                        COALESCE(u.varsayilan_fiyat,0) AS satis_fiyati
                    FROM urunler u
                    LEFT JOIN urun_gruplari g ON g.id=u.grup_id
                    ORDER BY u.ad
                """)
            rows = cur.fetchall()
            conn.close()
            tabloGecmis.setRowCount(len(rows))
            toplam_maliyet = 0.0
            toplam_kar = 0.0
            for r, row in enumerate(rows):
                urun, grup, stok, son_alis_tl, satis = row
                stok = float(stok or 0)
                son_alis_tl = float(son_alis_tl or 0)
                satis = float(satis or 0)
                kar_birim = satis - son_alis_tl if son_alis_tl > 0 else 0
                stok_maliyet = stok * son_alis_tl
                tahmini_kar = stok * kar_birim if son_alis_tl > 0 else 0
                toplam_maliyet += stok_maliyet
                toplam_kar += tahmini_kar
                durum_txt = "KÂR" if kar_birim > 0 else ("ZARAR" if kar_birim < 0 else "NÖTR / ALIŞ YOK")
                vals = [
                    urun or "", grup or "", f"{stok:g}",
                    para_yaz(son_alis_tl) if son_alis_tl > 0 else "-",
                    para_yaz(satis),
                    para_yaz(kar_birim) if son_alis_tl > 0 else "-",
                    para_yaz(stok_maliyet) if son_alis_tl > 0 else "-",
                    para_yaz(tahmini_kar) if son_alis_tl > 0 else "-",
                    durum_txt
                ]
                for c, val in enumerate(vals):
                    tabloGecmis.setItem(r, c, QTableWidgetItem(str(val)))
            lblKarOzet.setText(
                f"Toplam ürün: {len(rows)}  |  Stok maliyeti: {para_yaz(toplam_maliyet)}  |  Tahmini kâr/zarar: {para_yaz(toplam_kar)}"
            )

        def urun_sec():
            row = tabloUrun.currentRow()
            if row < 0:
                return
            uid = int(tabloUrun.item(row, 6).text())
            ad = tabloUrun.item(row, 0).text()
            grup = tabloUrun.item(row, 1).text()
            satis_fiyati = self._sayi_oku(tabloUrun.item(row, 2).text().replace("₺", ""))
            son_alis_tl = self._sayi_oku(tabloUrun.item(row, 3).text().replace("₺", "")) if tabloUrun.item(row, 3) else 0
            kar_adet = self._sayi_oku(tabloUrun.item(row, 4).text().replace("₺", "")) if tabloUrun.item(row, 4) else 0
            stok = self._sayi_oku(tabloUrun.item(row, 5).text())
            durum["urun"] = {
                "id": uid, "ad": ad, "grup": grup, "satis_fiyati": satis_fiyati,
                "stok": stok, "son_alis_tl": son_alis_tl, "kar_adet": kar_adet
            }
            son_alis_text = para_yaz(son_alis_tl) if son_alis_tl > 0 else "Henüz alış yok"
            kar_text = para_yaz(kar_adet) if son_alis_tl > 0 else "-"
            lblSecili.setText(
                f"Seçili Ürün: {ad}\n"
                f"Grup: {grup}  |  Stok: {stok:g}\n"
                f"Satış: {para_yaz(satis_fiyati)}\n"
                f"Son Alış TL/Birim: {son_alis_text}\n"
                f"Kâr/Adet: {kar_text}"
            )
            kar_hesapla()

        def kur_al():
            if cmbParaBirimi.currentText() != "USD":
                txtKur.setText("1")
                kar_hesapla()
                return
            if tcmb_usd_kuru_al is None:
                QMessageBox.warning(pencere, "Kur Alınamadı", "TCMB kur modülü bulunamadı. Kur alanını manuel yazabilirsiniz.")
                return
            def kur_sonucunu_yaz(sonuc):
                kur, bilgi = sonuc
                txtKur.setText(str(kur).replace(".", ","))
                QMessageBox.information(pencere, "TCMB USD Kuru", f"USD kuru alındı: {str(kur).replace('.', ',')} TL\n{bilgi}")
                kar_hesapla()

            def kur_hatasi_yaz(hata):
                QMessageBox.warning(pencere, "Kur Alınamadı", f"TCMB kuru alınamadı. Kur alanına manuel yazabilirsiniz.\n\n{str(hata).splitlines()[0]}")

            self.arka_plan_calistir(tcmb_usd_kuru_al, kur_sonucunu_yaz, kur_hatasi_yaz, "TCMB kuru arka planda alınıyor...")

        def kar_hesapla():
            urun = durum.get("urun")
            pb = cmbParaBirimi.currentText()
            if pb == "TL" and txtKur.text().strip() != "1":
                txtKur.blockSignals(True)
                txtKur.setText("1")
                txtKur.blockSignals(False)
            adet = self._sayi_oku(txtAdet.text() or "0")
            alis = self._sayi_oku(txtAlisFiyat.text() or "0")
            kur = self._sayi_oku(txtKur.text() or "1")
            if pb == "TL":
                kur = 1.0
            alis_tl = tl_karsiligi_hesapla(alis, pb, kur) if alis > 0 and kur > 0 else 0
            lblTlKarsilik.setText(f"TL Karşılığı: {para_yaz(alis_tl)}")
            if not urun:
                lblKar.setText("Önce ürün seçin. Alış fiyatı yazınca kâr karşılaştırması burada görünür.")
                return
            satis = float(urun.get("satis_fiyati") or 0)
            if alis <= 0:
                son_alis = float(urun.get("son_alis_tl") or 0)
                if son_alis > 0:
                    kar_son = satis - son_alis
                    lblKar.setText(
                        f"Satış: {para_yaz(satis)}  |  Son Alış TL/Birim: {para_yaz(son_alis)}\n"
                        f"Son Alışa Göre Kâr/Adet: {para_yaz(kar_son)}\n"
                        f"Yeni alış fiyatı yazınca güncel kâr/zarar hesaplanır."
                    )
                else:
                    lblKar.setText(f"Satış Fiyatı: {para_yaz(satis)}\nAlış fiyatını yazınca kâr/zarar hesaplanır.")
                return
            if pb == "USD" and kur <= 0:
                lblKar.setText("USD alış için kur 0'dan büyük olmalı.")
                return
            kar_birim = satis - alis_tl
            kar_toplam = kar_birim * adet if adet > 0 else 0
            durum_text = "KÂR" if kar_birim >= 0 else "ZARAR"
            lblKar.setText(
                f"Satış: {para_yaz(satis)}  |  Maliyet: {para_yaz(alis_tl)}\n"
                f"Alış: {alis:g} {pb}  |  Kur: {kur:g}\n"
                f"Birim {durum_text}: {para_yaz(kar_birim)}\n"
                f"Toplam {durum_text}: {para_yaz(kar_toplam)}"
            )

        def kaydet():
            urun = durum.get("urun")
            if not urun:
                QMessageBox.warning(pencere, "Uyarı", "Önce ürün seçin.")
                return
            tedarikci = txtTedarikci.text().strip()
            if not tedarikci:
                QMessageBox.warning(pencere, "Uyarı", "Aldığımız firma / tedarikçi boş olamaz.")
                return
            adet = self._sayi_oku(txtAdet.text())
            fiyat = self._sayi_oku(txtAlisFiyat.text())
            pb = cmbParaBirimi.currentText()
            kur = self._sayi_oku(txtKur.text() or "1")
            if pb == "TL":
                kur = 1.0
            if adet <= 0 or fiyat < 0:
                QMessageBox.warning(pencere, "Uyarı", "Adet 0'dan büyük olmalı, alış fiyatı sayısal olmalı.")
                return
            if pb == "USD" and kur <= 0:
                QMessageBox.warning(pencere, "Uyarı", "USD alışta kur 0'dan büyük olmalı. TCMB kurunu alabilir veya manuel yazabilirsiniz.")
                return
            alis_tl = tl_karsiligi_hesapla(fiyat, pb, kur)
            satis_fiyati = float(urun.get("satis_fiyati") or 0)
            kar_birim = satis_fiyati - alis_tl
            toplam = adet * alis_tl
            kar_toplam = adet * kar_birim
            tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
            aciklama = txtAciklama.toPlainText().strip()
            with db_baglan() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO urun_alislari(urun_id, urun_adi, tedarikci, tarih, adet, alis_fiyati, toplam, aciklama, satis_fiyati, kar_birim, kar_toplam, para_birimi, kur, alis_fiyati_tl, fatura_durumu)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (urun["id"], urun["ad"], tedarikci, tarih, adet, fiyat, toplam, aciklama, satis_fiyati, kar_birim, kar_toplam, pb, kur, alis_tl, cmbFaturaDurumu.currentText()))
                cur.execute("UPDATE urunler SET stok = COALESCE(stok,0) + ? WHERE id=?", (adet, urun["id"]))
            QMessageBox.information(
                pencere,
                "Kaydedildi",
                f"Ürün girişi kaydedildi ve stok artırıldı.\n\n"
                f"Ürün: {urun['ad']}\n"
                f"Giriş Adedi: {adet:g}\n"
                f"Eski Stok: {float(urun.get('stok') or 0):g}\n"
                f"Yeni Stok: {float(urun.get('stok') or 0) + adet:g}\n"
                f"Tedarikçi: {tedarikci}\n"
                f"Belge Durumu: {cmbFaturaDurumu.currentText()}\n"
                f"Toplam alış: {para_yaz(toplam)}\n"
                f"Tahmini kâr/zarar: {para_yaz(kar_toplam)}"
            )
            txtAdet.clear()
            txtAlisFiyat.clear()
            txtAciklama.clear()
            urun_listele()
            gecmis_listele()
            # Seçili ürünün güncel stokunu tekrar yükle
            durum["urun"] = None
            lblSecili.setText("Seçili Ürün: Yok")
            kar_hesapla()

        def stok_duzelt():
            urun = durum.get("urun")
            if not urun:
                QMessageBox.warning(pencere, "Uyarı", "Önce stok düzeltilecek ürünü seçin.")
                return
            yeni_stok_text, ok = QInputDialog.getText(
                pencere,
                "Stok Düzelt",
                f"{urun['ad']} için yeni stok miktarını yazın:\nMevcut stok: {float(urun.get('stok') or 0):g}"
            )
            if not ok:
                return
            yeni_stok = self._sayi_oku(yeni_stok_text)
            if yeni_stok < 0:
                QMessageBox.warning(pencere, "Hata", "Stok eksi olamaz.")
                return
            aciklama = f"Manuel stok düzeltme: eski {float(urun.get('stok') or 0):g}, yeni {yeni_stok:g}"
            tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
            fark = yeni_stok - float(urun.get('stok') or 0)
            with db_baglan() as conn:
                cur = conn.cursor()
                cur.execute("UPDATE urunler SET stok=? WHERE id=?", (yeni_stok, urun["id"]))
                cur.execute("""
                    INSERT INTO urun_alislari(urun_id, urun_adi, tedarikci, tarih, adet, alis_fiyati, toplam, aciklama, satis_fiyati, kar_birim, kar_toplam)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (urun["id"], urun["ad"], "MANUEL STOK", tarih, fark, 0, 0, aciklama, float(urun.get("satis_fiyati") or 0), 0, 0))
            QMessageBox.information(pencere, "Stok Güncellendi", f"{urun['ad']} stoku güncellendi.\nYeni stok: {yeni_stok:g}")
            urun_listele()
            gecmis_listele()
            durum["urun"] = None
            lblSecili.setText("Seçili Ürün: Yok")
            kar_hesapla()

        txtUrunAra.textChanged.connect(urun_listele)
        txtAdet.textChanged.connect(kar_hesapla)
        txtAlisFiyat.textChanged.connect(kar_hesapla)
        txtKur.textChanged.connect(kar_hesapla)
        cmbParaBirimi.currentTextChanged.connect(kar_hesapla)
        btnKurAl.clicked.connect(kur_al)
        tabloUrun.cellClicked.connect(lambda r, c: urun_sec())
        tabloUrun.cellDoubleClicked.connect(lambda r, c: urun_sec())
        btnKaydet.clicked.connect(kaydet)
        btnStokDuzelt.clicked.connect(stok_duzelt)
        txtKarAra.textChanged.connect(gecmis_listele)
        btnKarYenile.clicked.connect(gecmis_listele)
        urun_listele()
        gecmis_listele()
        pencere.setLayout(ana)
        if embedded:
            pencere.setWindowFlags(Qt.Widget)
            return pencere
        pencere.exec()

