import os
import sys
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut, QTextDocument
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from moduller.db import baglan, db_baglan, urun_tablolari_olustur
from moduller.sistem import firma_bilgisi_getir
from moduller.yardimci import logo_html, para_yaz
from pages.sales.sales_cart import (
    barkod_oku_ve_ekle as cart_barkod_oku_ve_ekle,
)
from pages.sales.sales_cart import (
    hesapla_toplam as cart_hesapla_toplam,
)
from pages.sales.sales_cart import (
    liste_temizle as cart_liste_temizle,
)
from pages.sales.sales_cart import (
    satir_sil as cart_satir_sil,
)
from pages.sales.sales_cart import (
    urun_sec_ve_ekle as cart_urun_sec_ve_ekle,
)
from pages.sales.sales_document import (
    belge_html as document_belge_html,
    mail_ac as document_mail_ac,
    ozet_kopyala as document_ozet_kopyala,
    ozet_metni as document_ozet_metni,
    pdf_kaydet as document_pdf_kaydet,
    satis_gecmisi as document_satis_gecmisi,
    whatsapp_proforma_ac as document_whatsapp_proforma_ac,
    yazdir as document_yazdir,
)
from pages.sales.sales_product import (
    grup_duzenle,
    grup_ekle,
    grup_sil,
    urun_duzenle,
    urun_ekle,
    urun_sil,
)
from pages.sales.sales_styles import SALES_PAGE_STYLE
from pages.sales.sales_utils import parse_sayi

BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))


class SatisMixin:

    def _satis_maliyet_kolonlarini_gizle(self, tablo):
        """Satış ekranında alış/maliyet/kâr bilgileri personel tarafında görünmemeli.
        Ürün yönetimi ve Kâr/Zarar modülleri bu bilgileri göstermeye devam eder.
        """
        gizli_anahtarlar = ("alış", "alis", "maliyet", "kâr", "kar", "profit")
        try:
            for kolon in range(tablo.columnCount()):
                baslik = tablo.horizontalHeaderItem(kolon)
                metin = baslik.text().lower() if baslik else ""
                if any(anahtar in metin for anahtar in gizli_anahtarlar):
                    tablo.setColumnHidden(kolon, True)
        except Exception:
            pass
    def urun_satis_penceresi(self, embedded=False):
        urun_tablolari_olustur()

        pencere = QWidget(self) if embedded else QDialog(self)
        if not embedded:
            pencere.setWindowTitle("Ürün Satışı / Proforma")
            pencere.resize(1420, 850)
            pencere.setMinimumSize(980, 650)
        else:
            pencere.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        pencere.setStyleSheet(SALES_PAGE_STYLE)

        ana = QVBoxLayout()
        ana.setContentsMargins(6, 6, 6, 6)
        ana.setSpacing(6)

        baslik_kutu = QFrame()
        baslik_kutu.setObjectName("HeaderPanel")
        baslik_layout = QHBoxLayout()
        baslik_layout.setContentsMargins(14, 10, 14, 10)

        baslik_sol = QVBoxLayout()
        baslik = QLabel("Satış Ekranı 2.0")
        baslik.setStyleSheet("font-size:21px;font-weight:900;color:#0F172A;")
        alt_bilgi = QLabel("Cari seç, ürünü okut, sepeti kontrol et ve kaydet")
        alt_bilgi.setStyleSheet("font-size:13px;color:#64748B;")
        baslik_sol.addWidget(baslik)
        baslik_sol.addWidget(alt_bilgi)

        lblToplam = QLabel("Genel Toplam\n0,00 ₺")
        lblToplam.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lblToplam.setStyleSheet("font-size:20px;font-weight:900;color:#047857;")
        baslik_layout.addLayout(baslik_sol, 3)
        baslik_layout.addWidget(lblToplam, 2)
        baslik_kutu.setLayout(baslik_layout)
        ana.addWidget(baslik_kutu)

        # F tuşları hem klavye hem fare ile çalışır.
        kisayol_kutu = QFrame()
        kisayol_kutu.setObjectName("RibbonPanel")
        kisayol_l = QHBoxLayout(kisayol_kutu)
        kisayol_l.setContentsMargins(10, 6, 10, 6)
        kisayol_l.setSpacing(8)
        btnF2Cari = QPushButton("F2\nCari")
        btnF3Barkod = QPushButton("F3\nBarkod")
        btnF4Proforma = QPushButton("F4\nProforma")
        btnF5Kaydet = QPushButton("F5\nKaydet")
        btnEscTemizle = QPushButton("ESC\nTemizle")
        for _b in (btnF2Cari, btnF3Barkod, btnF4Proforma, btnF5Kaydet, btnEscTemizle):
            _b.setMinimumHeight(38)
            _b.setMaximumHeight(42)
            _b.setMinimumWidth(82)
            _b.setObjectName("GreyButton")
            _b.setStyleSheet(_b.styleSheet() + "font-size:12px; line-height:14px;")
            kisayol_l.addWidget(_b)
        btnF5Kaydet.setObjectName("PrimaryButton")
        kisayol_l.addStretch(1)
        lblSatisModu = QLabel("Hızlı satış modu")
        lblSatisModu.setStyleSheet("color:#64748B;font-size:12px;font-weight:800;padding-right:6px;")
        kisayol_l.addWidget(lblSatisModu)
        ana.addWidget(kisayol_kutu)

        govde = QHBoxLayout()
        govde.setSpacing(10)
        govde_splitter = QSplitter(Qt.Horizontal)
        govde_splitter.setChildrenCollapsible(False)
        govde_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # SOL PANEL: Cari listesi
        sol_panel = QFrame()
        sol_panel.setObjectName("Panel")
        sol = QVBoxLayout()
        sol.setContentsMargins(10, 10, 10, 10)
        sol.setSpacing(7)

        lblCariBaslik = QLabel("Müşteri / Cari")
        lblCariBaslik.setStyleSheet("font-size:17px;font-weight:900;color:#0F172A;")
        sol.addWidget(lblCariBaslik)

        txtCariAra = QLineEdit()
        txtCariAra.setPlaceholderText("Müşteri adı veya telefon ara...")
        sol.addWidget(txtCariAra)

        tabloCari = QTableWidget()
        tabloCari.setColumnCount(3)
        tabloCari.setHorizontalHeaderLabels(["No", "Cari", "Bakiye"])
        tabloCari.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        tabloCari.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        tabloCari.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        tabloCari.setSelectionBehavior(QTableWidget.SelectRows)
        tabloCari.setEditTriggers(QTableWidget.NoEditTriggers)
        tabloCari.verticalHeader().setVisible(False)
        tabloCari.verticalHeader().setDefaultSectionSize(34)
        sol.addWidget(tabloCari, 1)

        lblSeciliCari = QLabel("Seçili Cari: Yok")
        lblSeciliCari.setStyleSheet("background:#F8FAFC;border:1px solid #E5E7EB;border-radius:8px;padding:9px;font-weight:800;color:#1E293B;")
        lblSeciliCari.setWordWrap(True)
        sol.addWidget(lblSeciliCari)

        btnYeniCari = QPushButton("+ Yeni Cari Ekle")
        btnYeniCari.setObjectName("PrimaryButton")
        sol.addWidget(btnYeniCari)
        sol_panel.setMinimumWidth(220)
        sol_panel.setMaximumWidth(300)
        sol_panel.setLayout(sol)
        govde_splitter.addWidget(sol_panel)

        # ORTA PANEL: Modern grup seçimi + ürün listesi
        orta_panel = QFrame()
        orta_panel.setObjectName("Panel")
        orta = QVBoxLayout()
        orta.setContentsMargins(10, 10, 10, 10)
        orta.setSpacing(7)

        # Kompakt ürün grubu filtresi: eski dikey alan çok yer kaplıyordu.
        grupFiltrePanel = QFrame()
        grupFiltrePanel.setObjectName("GrupFiltrePanel")
        grupFiltrePanel.setMaximumHeight(58)
        grupFiltrePanel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        grupFiltrePanel.setStyleSheet("""
            QFrame#GrupFiltrePanel {
                background:#F8FAFC;
                border:1px solid #E2E8F0;
                border-radius:12px
            }
        """)
        grupSatiri = QHBoxLayout(grupFiltrePanel)
        grupSatiri.setContentsMargins(8, 6, 8, 6)
        grupSatiri.setSpacing(8)

        lblGrupBaslik = QLabel("Ürün Grubu")
        lblGrupBaslik.setStyleSheet("font-size:14px;font-weight:900;color:#1E293B;")
        lblGrupBaslik.setMinimumWidth(96)
        lblGrupBaslik.setMaximumWidth(120)
        grupSatiri.addWidget(lblGrupBaslik)

        cmbGrup = QComboBox()
        cmbGrup.setMinimumHeight(36)
        cmbGrup.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        cmbGrup.setStyleSheet("""
            QComboBox {
                background:white
                border:1px solid #CBD5E1;
                border-radius:8px
                padding:8px 10px
                font-size:15px
                font-weight:800
                color:#0F172A;
            }
            QComboBox::drop-down {
                border:0
                width:28px
            }
        """)
        grupSatiri.addWidget(cmbGrup, 1)
        orta.addWidget(grupFiltrePanel)

        grupYonetim = QHBoxLayout()
        btnGrupEkle = QPushButton("+ Grup")
        btnGrupDuzenle = QPushButton("Düzenle")
        btnGrupSil = QPushButton("Sil")
        btnGrupSil.setObjectName("DangerButton")
        for b in (btnGrupEkle, btnGrupDuzenle, btnGrupSil):
            b.setMaximumHeight(38)
            b.setStyleSheet(b.styleSheet() + "padding:7px;font-size:13px;border-radius:8px;")
        grupYonetim.addWidget(btnGrupEkle)
        grupYonetim.addWidget(btnGrupDuzenle)
        grupYonetim.addWidget(btnGrupSil)
        grupYonetimWidget = QWidget()
        grupYonetimWidget.setLayout(grupYonetim)
        grupYonetimWidget.setVisible(False)
        grupYonetimWidget.setMaximumHeight(44)
        grupYonetimWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        orta.addWidget(grupYonetimWidget)

        lblUrunBaslik = QLabel("Ürün Listesi")
        lblUrunBaslik.setStyleSheet("font-size:16px;font-weight:900;color:#0F172A;margin-top:2px;")
        orta.addWidget(lblUrunBaslik)

        txtUrunAra = QLineEdit()
        txtUrunAra.setPlaceholderText("Ürün ara... Yazdıkça altta tüm ürünler listelenir")
        orta.addWidget(txtUrunAra)

        txtBarkodOku = QLineEdit()
        txtBarkodOku.setPlaceholderText("Barkod okut / yaz ve Enter'a bas")
        txtBarkodOku.setMinimumHeight(36)
        txtBarkodOku.setStyleSheet("""
            QLineEdit {
                background:#F8FAFC;
                border:1px solid #CBD5E1;
                border-radius:10px
                padding:9px 12px
                font-size:13px
                font-weight:800
                color:#0F172A;
            }
            QLineEdit:focus { border-color:#2563EB; background:#FFFFFF; }
        """)
        orta.addWidget(txtBarkodOku)

        tabloUrun = QTableWidget()
        tabloUrun.setColumnCount(4)
        tabloUrun.setHorizontalHeaderLabels(["Ürün", "Stok", "Fiyat", "ID"])
        self._satis_maliyet_kolonlarini_gizle(tabloUrun)
        tabloUrun.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        tabloUrun.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        tabloUrun.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        tabloUrun.setColumnWidth(1, 85)
        tabloUrun.setColumnWidth(2, 145)
        tabloUrun.setSelectionBehavior(QTableWidget.SelectRows)
        tabloUrun.setEditTriggers(QTableWidget.NoEditTriggers)
        tabloUrun.verticalHeader().setVisible(False)
        tabloUrun.setColumnHidden(3, True)
        tabloUrun.setMinimumHeight(190)
        tabloUrun.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        tabloUrun.verticalHeader().setDefaultSectionSize(34)
        orta.addWidget(tabloUrun, 6)

        lblUrunIpucu = QLabel("Ürün aramaya yazdıkça sonuçlar altta listelenir. Çift tıklayınca satış listesine eklenir.")
        lblUrunIpucu.setStyleSheet("font-size:12px;color:#64748B;")
        lblUrunIpucu.setWordWrap(True)
        lblUrunIpucu.setMaximumHeight(46)
        orta.addWidget(lblUrunIpucu)

        urunYonetim = QHBoxLayout()
        btnUrunEkle = QPushButton("+ Ürün")
        btnUrunDuzenle = QPushButton("Düzenle")
        btnUrunSil = QPushButton("Sil")
        btnUrunEkle.setObjectName("PrimaryButton")
        btnUrunDuzenle.setObjectName("GreyButton")
        btnUrunSil.setObjectName("OutlineDangerButton")
        for _b in (btnUrunEkle, btnUrunDuzenle, btnUrunSil):
            _b.setMinimumHeight(38)
        urunYonetim.addWidget(btnUrunEkle, 1)
        urunYonetim.addWidget(btnUrunDuzenle, 1)
        urunYonetim.addWidget(btnUrunSil, 1)
        orta.addLayout(urunYonetim)
        orta_panel.setMinimumWidth(330)
        orta_panel.setLayout(orta)
        govde_splitter.addWidget(orta_panel)

        # SAĞ PANEL: Satış kalemleri
        sag_panel = QFrame()
        sag_panel.setObjectName("Panel")
        sag = QVBoxLayout()
        sag.setContentsMargins(10, 10, 10, 10)
        sag.setSpacing(7)

        lblKalemBaslik = QLabel("Sepet / Satış Kalemleri")
        lblKalemBaslik.setStyleSheet("font-size:17px;font-weight:900;color:#0F172A;")
        sag.addWidget(lblKalemBaslik)

        # v108: Seçili cari bilgisi sepet başlığının altında net şekilde gösterilir.
        lblSepetCari = QLabel("Cari seçilmedi")
        lblSepetCari.setObjectName("SelectedCustomerBanner")
        lblSepetCari.setMinimumHeight(38)
        lblSepetCari.setWordWrap(True)
        lblSepetCari.setStyleSheet("""
            QLabel#SelectedCustomerBanner {
                background:#EFF6FF;
                border:1px solid #BFDBFE;
                border-left:4px solid #2563EB;
                border-radius:10px
                padding:9px 12px
                color:#1E3A8A;
                font-size:13px
                font-weight:800
            }
        """)
        sag.addWidget(lblSepetCari)

        tabloKalem = QTableWidget()
        tabloKalem.setColumnCount(6)
        tabloKalem.setHorizontalHeaderLabels(["Ürün", "Adet", "B. Fiyat", "Tutar", "Grup", "ID"])
        self._satis_maliyet_kolonlarini_gizle(tabloKalem)
        headerKalem = tabloKalem.horizontalHeader()
        headerKalem.setStretchLastSection(False)
        headerKalem.setSectionResizeMode(0, QHeaderView.Stretch)
        headerKalem.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        headerKalem.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        headerKalem.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        headerKalem.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        tabloKalem.setColumnWidth(1, 62)
        tabloKalem.setColumnWidth(2, 92)
        tabloKalem.setColumnWidth(3, 92)
        tabloKalem.setColumnWidth(4, 0)
        tabloKalem.setColumnHidden(4, True)
        tabloKalem.setColumnHidden(5, True)
        tabloKalem.setSelectionBehavior(QTableWidget.SelectRows)
        tabloKalem.verticalHeader().setVisible(False)
        tabloKalem.setMinimumWidth(430)
        tabloKalem.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        tabloKalem.verticalHeader().setDefaultSectionSize(36)
        tabloKalem.setMinimumHeight(210)
        sag.addWidget(tabloKalem, 3)

        sag.addWidget(QLabel("Not / Açıklama"))
        txtNot = QTextEdit()
        txtNot.setMaximumHeight(42)
        txtNot.setPlaceholderText("Örn: Proforma / ürün satış kaydı")
        sag.addWidget(txtNot)

        # v101: Responsive işlem alanı. Özet ve aksiyonlar yan yana durur;
        # küçük ekranda bile butonlar üst üste binmez, sağ taraf kesilmez.
        aksiyon_panel = QFrame()
        aksiyon_panel.setObjectName("ActionPanel")
        aksiyon_panel.setMinimumHeight(128)
        aksiyon_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        aksiyon_l = QHBoxLayout()
        aksiyon_l.setContentsMargins(10, 10, 10, 10)
        aksiyon_l.setSpacing(10)

        toplam_kart = QFrame()
        toplam_kart.setObjectName("SummaryCard")
        toplam_kart.setMinimumWidth(210)
        toplam_kart.setStyleSheet("""
            QFrame#SummaryCard {
                background:#F8FAFC;
                border:1px solid #E2E8F0;
                border-radius:14px
            }
        """)
        toplam_l = QGridLayout(toplam_kart)
        toplam_l.setContentsMargins(12, 10, 12, 10)
        toplam_l.setHorizontalSpacing(12)
        toplam_l.setVerticalSpacing(6)

        lblOzetBaslik = QLabel("İşlem Özeti")
        lblOzetBaslik.setStyleSheet("font-size:15px;font-weight:900;color:#0F172A;")
        lblAraToplam = QLabel("0,00 ₺")
        lblIskonto = QLabel("0,00 ₺")
        lblGenelToplamKart = QLabel("0,00 ₺")
        lblGenelToplamKart.setStyleSheet("font-size:19px;font-weight:900;color:#047857;")
        for _label, _row in (("Ara Toplam", 1), ("İskonto", 2), ("Genel Toplam", 3)):
            label_widget = QLabel(_label)
            label_widget.setStyleSheet("font-size:13px;font-weight:800;color:#475569;")
            toplam_l.addWidget(label_widget, _row, 0)
        toplam_l.addWidget(lblOzetBaslik, 0, 0, 1, 2)
        toplam_l.addWidget(lblAraToplam, 1, 1, alignment=Qt.AlignRight)
        toplam_l.addWidget(lblIskonto, 2, 1, alignment=Qt.AlignRight)
        toplam_l.addWidget(lblGenelToplamKart, 3, 1, alignment=Qt.AlignRight)
        aksiyon_l.addWidget(toplam_kart, 1)

        def sade_buton_stili(tur="normal"):
            if tur == "success":
                return """
                QPushButton { background:#059669;color:white;border:none;border-radius:12px;padding:10px 14px;font-size:14px;font-weight:900; }
                QPushButton:hover { background:#047857; }
                """
            if tur == "danger":
                return """
                QPushButton { background:#FFFFFF;color:#B91C1C;border:1px solid #FCA5A5;border-radius:10px;padding:8px 12px;font-weight:800; }
                QPushButton:hover { background:#FEF2F2; }
                """
            return """
                QPushButton { background:#FFFFFF;color:#334155;border:1px solid #CBD5E1;border-radius:10px;padding:8px 12px;font-weight:800; }
                QPushButton:hover { background:#F8FAFC; }
            """

        sag_aksiyonlar = QVBoxLayout()
        sag_aksiyonlar.setSpacing(8)
        sag_aksiyonlar.setContentsMargins(0, 0, 0, 0)
        satirButonlar = QHBoxLayout()
        satirButonlar.setSpacing(8)
        btnSatirSil = QPushButton("Satır Sil")
        btnTemizle = QPushButton("Temizle")
        btnSatirSil.setMinimumHeight(36)
        btnTemizle.setMinimumHeight(36)
        btnSatirSil.setStyleSheet(sade_buton_stili("danger"))
        btnTemizle.setStyleSheet(sade_buton_stili("normal"))
        satirButonlar.addWidget(btnSatirSil, 1)
        satirButonlar.addWidget(btnTemizle, 1)
        sag_aksiyonlar.addLayout(satirButonlar)

        btnProformaKaydet = QPushButton("Proforma Oluştur")
        btnProformaKaydet.setMinimumHeight(38)
        btnProformaKaydet.setStyleSheet(sade_buton_stili("normal"))
        sag_aksiyonlar.addWidget(btnProformaKaydet)

        btnKaydetCariBorc = QPushButton("Satışı Kaydet")
        btnKaydetCariBorc.setToolTip("Satışı kaydet ve cariye borç işle")
        btnKaydetCariBorc.setMinimumHeight(42)
        btnKaydetCariBorc.setStyleSheet(sade_buton_stili("success"))
        sag_aksiyonlar.addWidget(btnKaydetCariBorc)
        aksiyon_l.addLayout(sag_aksiyonlar, 1)
        aksiyon_panel.setLayout(aksiyon_l)
        sag.addWidget(aksiyon_panel, 0)

        btnOzetKopyala = QPushButton("Kopyala")
        btnMail = QPushButton("Mail")
        btnYazdir = QPushButton("Yazdır")
        btnPdfKaydet = QPushButton("PDF")
        btnGecmis = QPushButton("Satış Geçmişi")
        for _b in (btnOzetKopyala, btnMail, btnYazdir, btnPdfKaydet, btnGecmis):
            _b.setVisible(False)

        sag_panel.setLayout(sag)
        sag_panel.setMinimumWidth(480)
        govde_splitter.addWidget(sag_panel)
        govde_splitter.setStretchFactor(0, 2)
        govde_splitter.setStretchFactor(1, 4)
        govde_splitter.setStretchFactor(2, 6)
        govde_splitter.setSizes([250, 410, 600])
        govde.addWidget(govde_splitter, 1)
        ana.addLayout(govde, 1)

        alt = QHBoxLayout()
        alt.setContentsMargins(0, 0, 0, 0)
        btnYenile = QPushButton("Yenile")
        btnKapat = QPushButton("Kapat")
        btnKapat.setObjectName("GreyButton")
        btnKapat.clicked.connect(pencere.close)
        alt.addWidget(btnYenile)
        alt.addStretch()
        alt.addWidget(btnKapat)
        ana.addLayout(alt)

        durum = {"cari": None, "grup_id": None, "grup_ad": None, "urun_id": None, "urun_ad": None, "urun_fiyat": 0.0}
        belge_durumu = {"tur": "PROFORMA"}
        hesaplama_yapiliyor = {"aktif": False}

        def temizle_layout(q_layout):
            while q_layout.count():
                item = q_layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.deleteLater()

        def cari_liste_yukle_urun():
            conn = baglan()
            cur = conn.cursor()
            arama = txtCariAra.text().strip()
            if arama:
                like = f"%{arama}%"
                cur.execute("""
                    SELECT c.id, c.ad, c.telefon,
                    COALESCE(SUM(CASE WHEN h.tip='BORÇ' THEN h.tutar ELSE 0 END), 0) -
                    COALESCE(SUM(CASE WHEN h.tip='TAHSİLAT' THEN h.tutar ELSE 0 END), 0) AS bakiye
                    FROM cariler c
                                    LEFT JOIN hareketler h ON h.cari_id=c.id
                    WHERE c.ad LIKE ? OR c.telefon LIKE ?
                    GROUP BY c.id, c.ad, c.telefon
                    ORDER BY c.ad
                """, (like, like))
            else:
                cur.execute("""
                    SELECT c.id, c.ad, c.telefon,
                    COALESCE(SUM(CASE WHEN h.tip='BORÇ' THEN h.tutar ELSE 0 END), 0) -
                    COALESCE(SUM(CASE WHEN h.tip='TAHSİLAT' THEN h.tutar ELSE 0 END), 0) AS bakiye
                    FROM cariler c
                                    LEFT JOIN hareketler h ON h.cari_id=c.id
                    GROUP BY c.id, c.ad, c.telefon
                    ORDER BY c.ad
                """)
            satirlar = cur.fetchall()
            conn.close()
            tabloCari.setRowCount(len(satirlar))
            for i, (cari_id, ad, _telefon, bakiye) in enumerate(satirlar):
                degerler = [str(i + 1), ad or "", para_yaz(float(bakiye or 0))]
                for j, deger in enumerate(degerler):
                    it = QTableWidgetItem(str(deger))
                    tabloCari.setItem(i, j, it)
                tabloCari.item(i, 0).setData(1000, int(cari_id))

        def secili_cari_al():
            row = tabloCari.currentRow()
            if row < 0:
                return None
            cari_id = tabloCari.item(row, 0).data(1000)
            conn = baglan()
            cur = conn.cursor()
            cur.execute("SELECT id, ad, telefon, adres, vergi_dairesi, vergi_no FROM cariler WHERE COALESCE(aktif,1)=1 AND id=?", (int(cari_id),))
            row_db = cur.fetchone()
            conn.close()
            if row_db:
                return {
                    "id": int(row_db[0]),
                    "ad": row_db[1] or "",
                    "telefon": row_db[2] or "",
                    "adres": row_db[3] or "",
                    "vergi_dairesi": row_db[4] or "",
                    "vergi_no": row_db[5] or ""
                }
            return {"id": int(cari_id), "ad": tabloCari.item(row, 1).text() if tabloCari.item(row, 1) else "", "telefon": "", "adres": "", "vergi_dairesi": "", "vergi_no": ""}

        def cari_secildi():
            cari = secili_cari_al()
            durum["cari"] = cari
            if cari:
                lblSeciliCari.setText(f"Seçili Cari: {cari['ad']}")
                lblSepetCari.setText(f"👤 {cari['ad']}")
            else:
                lblSeciliCari.setText("Seçili Cari: Yok")
                lblSepetCari.setText("Cari seçilmedi")

        def grup_buton_stili(secili=False):
            if secili:
                return "background:#15803D;color:white;border-radius:12px;padding:16px;font-size:15px;font-weight:800;text-align:left;"
            return "background:#0D47A1;color:white;border-radius:12px;padding:16px;font-size:15px;font-weight:800;text-align:left;"

        def urun_buton_stili(secili=False):
            if secili:
                return "background:#15803D;color:white;border-radius:12px;padding:14px;font-size:14px;font-weight:800;text-align:left;"
            return "background:#2563EB;color:white;border-radius:12px;padding:14px;font-size:14px;font-weight:800;text-align:left;"

        def gruplari_yukle():
            onceki_grup_id = durum.get("grup_id")
            conn = baglan()
            cur = conn.cursor()
            cur.execute("SELECT id, ad FROM urun_gruplari ORDER BY ad")
            gruplar = cur.fetchall()
            conn.close()

            cmbGrup.blockSignals(True)
            cmbGrup.clear()

            if not gruplar:
                cmbGrup.addItem("Henüz ürün grubu yok", None)
                cmbGrup.setEnabled(False)
                durum["grup_id"] = None
                durum["grup_ad"] = None
                tabloUrun.setRowCount(0)
                lblUrunBaslik.setText("Ürün Listesi")
                cmbGrup.blockSignals(False)
                return

            cmbGrup.setEnabled(True)
            secilecek_index = 0
            for index, (grup_id, grup_ad) in enumerate(gruplar):
                cmbGrup.addItem(str(grup_ad), int(grup_id))
                if onceki_grup_id is not None and int(grup_id) == int(onceki_grup_id):
                    secilecek_index = index

            cmbGrup.setCurrentIndex(secilecek_index)
            secili_id = cmbGrup.currentData()
            secili_ad = cmbGrup.currentText().strip()
            durum["grup_id"] = int(secili_id) if secili_id is not None else None
            durum["grup_ad"] = secili_ad
            cmbGrup.blockSignals(False)
            urunleri_yukle()

        def grup_sec(grup_id, grup_ad):
            durum["grup_id"] = int(grup_id)
            durum["grup_ad"] = grup_ad
            durum["urun_id"] = None
            durum["urun_ad"] = None
            durum["urun_fiyat"] = 0.0
            for i in range(cmbGrup.count()):
                if cmbGrup.itemData(i) == int(grup_id):
                    cmbGrup.blockSignals(True)
                    cmbGrup.setCurrentIndex(i)
                    cmbGrup.blockSignals(False)
                    break
            lblUrunBaslik.setText(f"Ürün Listesi  •  {grup_ad}")
            urunleri_yukle()

        def grup_combo_degisti(index):
            if index < 0:
                return
            grup_id = cmbGrup.itemData(index)
            if grup_id is None:
                return
            grup_ad = cmbGrup.currentText().replace("📁", "").strip()
            grup_sec(grup_id, grup_ad)

        def urunleri_yukle():
            tabloUrun.setRowCount(0)
            arama = txtUrunAra.text().strip()
            conn = baglan()
            cur = conn.cursor()

            if arama:
                # Ürün arama yazıldığında sadece seçili grupta değil,
                # bütün ürün gruplarında arama yapar ve sonuçları altta listeler.
                like = f"%{arama}%"
                cur.execute("""
                    SELECT u.id, u.ad, COALESCE(u.varsayilan_fiyat, 0), COALESCE(u.stok,0),
                           COALESCE(g.id, 0), COALESCE(g.ad, '')
                    FROM urunler u
                    LEFT JOIN urun_gruplari g ON g.id = u.grup_id
                    WHERE u.ad LIKE ? OR g.ad LIKE ? OR COALESCE(u.barkod,'') LIKE ? OR CAST(u.varsayilan_fiyat AS TEXT) LIKE ?
                    ORDER BY u.ad
                    LIMIT 250
                """, (like, like, like, like))
                urunler = cur.fetchall()
                lblUrunBaslik.setText(f"3) Ürün Arama Sonuçları  •  {arama}")
            else:
                if durum["grup_id"] is None:
                    lblUrunBaslik.setText("Ürün Listesi")
                    conn.close()
                    return
                cur.execute("""
                    SELECT u.id, u.ad, COALESCE(u.varsayilan_fiyat, 0), COALESCE(u.stok,0),
                           COALESCE(g.id, 0), COALESCE(g.ad, '')
                    FROM urunler u
                    LEFT JOIN urun_gruplari g ON g.id = u.grup_id
                    WHERE u.grup_id=?
                    ORDER BY u.ad
                """, (durum["grup_id"],))
                urunler = cur.fetchall()
                lblUrunBaslik.setText(f"3) Ürün Listesi  •  {durum.get('grup_ad') or ''}")

            conn.close()

            tabloUrun.setRowCount(len(urunler))
            if not urunler:
                return

            for satir, (urun_id, urun_ad, fiyat, stok, grup_id, grup_ad) in enumerate(urunler):
                fiyat = float(fiyat or 0)
                stok = float(stok or 0)
                grup_id = int(grup_id or 0)
                grup_ad = str(grup_ad or "")

                item_ad = QTableWidgetItem(str(urun_ad))
                item_ad.setData(1000, int(urun_id))
                item_ad.setData(1001, float(fiyat))
                item_ad.setData(1002, float(stok))
                item_ad.setData(1003, grup_id)
                item_ad.setData(1004, grup_ad)

                item_stok = QTableWidgetItem(str(int(stok) if stok.is_integer() else stok))
                item_stok.setTextAlignment(Qt.AlignCenter)
                item_stok.setData(1000, int(urun_id))
                item_stok.setData(1001, float(fiyat))
                item_stok.setData(1002, float(stok))
                item_stok.setData(1003, grup_id)
                item_stok.setData(1004, grup_ad)

                item_fiyat = QTableWidgetItem(para_yaz(fiyat) if fiyat > 0 else "")
                item_fiyat.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item_fiyat.setData(1000, int(urun_id))
                item_fiyat.setData(1001, float(fiyat))
                item_fiyat.setData(1002, float(stok))
                item_fiyat.setData(1003, grup_id)
                item_fiyat.setData(1004, grup_ad)

                item_id = QTableWidgetItem(str(urun_id))
                item_id.setData(1000, int(urun_id))
                item_id.setData(1001, float(fiyat))
                item_id.setData(1002, float(stok))
                item_id.setData(1003, grup_id)
                item_id.setData(1004, grup_ad)

                tabloUrun.setItem(satir, 0, item_ad)
                tabloUrun.setItem(satir, 1, item_stok)
                tabloUrun.setItem(satir, 2, item_fiyat)
                tabloUrun.setItem(satir, 3, item_id)

                if durum.get("urun_id") == int(urun_id):
                    tabloUrun.selectRow(satir)

        def secili_urun_bilgisi():
            row = tabloUrun.currentRow()
            if row < 0 or not tabloUrun.item(row, 0):
                return None
            item = tabloUrun.item(row, 0)
            return {
                "id": int(item.data(1000)),
                "ad": item.text(),
                "fiyat": float(item.data(1001) or 0),
                "stok": float(item.data(1002) or 0),
                "grup_id": int(item.data(1003) or 0),
                "grup_ad": str(item.data(1004) or "")
            }

        def urun_satiri_secildi():
            urun = secili_urun_bilgisi()
            if not urun:
                return
            durum["urun_id"] = urun["id"]
            durum["urun_ad"] = urun["ad"]
            durum["urun_fiyat"] = urun["fiyat"]
            if urun.get("grup_id"):
                durum["grup_id"] = urun["grup_id"]
                durum["grup_ad"] = urun.get("grup_ad") or durum.get("grup_ad")

        def secili_urunu_satisa_ekle():
            urun = secili_urun_bilgisi()
            if not urun:
                QMessageBox.warning(pencere, "Uyarı", "Lütfen önce ürün listesinden bir ürün seçin.")
                return
            urun_sec_ve_ekle(urun["id"], urun["ad"], urun["fiyat"])

        def urun_sec_ve_ekle(urun_id, urun_ad, fiyat):
            return cart_urun_sec_ve_ekle(
                urun_id,
                urun_ad,
                fiyat,
                durum=durum,
                tablo_kalem=tabloKalem,
                hesapla_toplam=hesapla_toplam,
                urunleri_yukle=urunleri_yukle,
            )

        def barkod_oku_ve_ekle():
            return cart_barkod_oku_ve_ekle(
                pencere=pencere,
                txt_barkod_oku=txtBarkodOku,
                durum=durum,
                urun_sec_ve_ekle_callback=urun_sec_ve_ekle,
            )

        def hesapla_toplam():
            return cart_hesapla_toplam(
                tablo_kalem=tabloKalem,
                lbl_toplam=lblToplam,
                lbl_ara_toplam=lblAraToplam,
                lbl_genel_toplam_kart=lblGenelToplamKart,
                hesaplama_yapiliyor=hesaplama_yapiliyor,
            )

        def satir_sil():
            return cart_satir_sil(tablo_kalem=tabloKalem, hesapla_toplam=hesapla_toplam)

        def liste_temizle():
            return cart_liste_temizle(tablo_kalem=tabloKalem, hesapla_toplam=hesapla_toplam)

        def belge_html():
            return document_belge_html(
                tablo_kalem=tabloKalem,
                txt_not=txtNot,
                durum=durum,
                belge_durumu=belge_durumu,
            )

        def ozet_metni():
            return document_ozet_metni(
                tablo_kalem=tabloKalem,
                txt_not=txtNot,
                durum=durum,
                belge_durumu=belge_durumu,
            )

        def ozet_kopyala():
            return document_ozet_kopyala(pencere=pencere, ozet_metni_func=ozet_metni)

        def mail_ac():
            return document_mail_ac(ozet_metni_func=ozet_metni, belge_durumu=belge_durumu)

        def yazdir():
            return document_yazdir(
                pencere=pencere,
                tablo_kalem=tabloKalem,
                belge_html_func=belge_html,
            )

        def pdf_kaydet():
            return document_pdf_kaydet(
                pencere=pencere,
                tablo_kalem=tabloKalem,
                belge_html_func=belge_html,
                belge_durumu=belge_durumu,
            )

        def satis_gecmisi():
            return document_satis_gecmisi(pencere=pencere)

        def whatsapp_proforma_ac(cari, pdf_yolu, toplam):
            return document_whatsapp_proforma_ac(
                pencere=pencere,
                cari=cari,
                pdf_yolu=pdf_yolu,
                toplam=toplam,
            )

        def kaydet_proforma():
            belge_durumu["tur"] = "PROFORMA"
            cari = durum.get("cari") or secili_cari_al()
            if not cari:
                QMessageBox.warning(pencere, "Uyarı", "Önce müşteri/cari seçin.")
                return
            if tabloKalem.rowCount() == 0:
                QMessageBox.warning(pencere, "Uyarı", "Önce ürün ekleyin.")
                return
            toplam = hesapla_toplam()
            if toplam <= 0:
                QMessageBox.warning(pencere, "Uyarı", "Toplam tutar 0'dan büyük olmalı.")
                return
            tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
            notlar = txtNot.toPlainText().strip()
            stok_eksikleri = []
            try:
                with db_baglan() as conn_kontrol:
                    cur_kontrol = conn_kontrol.cursor()
                    for rr in range(tabloKalem.rowCount()):
                        kid_text = tabloKalem.item(rr, 5).text() if tabloKalem.columnCount() > 5 and tabloKalem.item(rr, 5) else ""
                        adet_kontrol = parse_sayi(tabloKalem.item(rr, 1).text() if tabloKalem.item(rr, 1) else "0")
                        if kid_text:
                            cur_kontrol.execute("SELECT ad, COALESCE(stok,0) FROM urunler WHERE id=?", (int(kid_text),))
                            stok_row = cur_kontrol.fetchone()
                            if stok_row and float(stok_row[1] or 0) < adet_kontrol:
                                stok_eksikleri.append(f"{stok_row[0]}: stok {float(stok_row[1] or 0):g}, istenen {adet_kontrol:g}")
            except Exception:
                stok_eksikleri = []
            if stok_eksikleri:
                QMessageBox.warning(pencere, "Stok Yetersiz", "Bazı ürünlerde yeterli stok yok:\n\n" + "\n".join(stok_eksikleri))
                return

            with db_baglan() as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO satislar(cari_id, tarih, toplam, notlar, hareket_id, belge_turu) VALUES (?, ?, ?, ?, NULL, 'PROFORMA')",
                    (cari["id"], tarih, toplam, notlar)
                )
                satis_id = cur.lastrowid
                for r in range(tabloKalem.rowCount()):
                    urun = tabloKalem.item(r, 0).text() if tabloKalem.item(r, 0) else ""
                    adet = parse_sayi(tabloKalem.item(r, 1).text() if tabloKalem.item(r, 1) else "0")
                    fiyat = parse_sayi(tabloKalem.item(r, 2).text() if tabloKalem.item(r, 2) else "0")
                    grup = tabloKalem.item(r, 4).text() if tabloKalem.item(r, 4) else ""
                    tutar = adet * fiyat
                    cur.execute(
                        "INSERT INTO satis_kalemleri(satis_id, grup_adi, urun_adi, adet, birim_fiyat, tutar) VALUES (?, ?, ?, ?, ?, ?)",
                        (satis_id, grup, urun, adet, fiyat, tutar)
                    )
            # Proforma PDF dosyasını program klasöründeki Proformalar klasörüne kaydet
            proforma_klasor = os.path.join(BASE_DIR, "Proformalar")
            os.makedirs(proforma_klasor, exist_ok=True)
            pdf_yolu = os.path.join(proforma_klasor, f"PF-{int(satis_id):05d}.pdf")

            # Aynı isimde dosya varsa üzerine yazmamak için tarih-saat ekle
            if os.path.exists(pdf_yolu):
                pdf_yolu = os.path.join(
                    proforma_klasor,
                    f"PF-{int(satis_id):05d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
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
                    f"PDF yeri:\n{pdf_yolu}"
                )
                try:
                    os.startfile(proforma_klasor)
                except Exception:
                    pass

                cevap_wp = QMessageBox.question(
                    pencere,
                    "WhatsApp",
                    "Proformayı WhatsApp Web ile göndermek ister misiniz?"
                )
                if cevap_wp == QMessageBox.Yes:
                    whatsapp_proforma_ac(cari, pdf_yolu, toplam)
            except Exception as hata:
                QMessageBox.warning(
                    pencere,
                    "PDF Hatası",
                    f"Proforma kaydedildi ama PDF oluşturulamadı:\n{hata}"
                )

        def kaydet_cariye_borc():
            belge_durumu["tur"] = "ÜRÜN SATIŞI"
            cari = durum.get("cari") or secili_cari_al()
            if not cari:
                QMessageBox.warning(pencere, "Uyarı", "Önce müşteri/cari seçin.")
                return
            if tabloKalem.rowCount() == 0:
                QMessageBox.warning(pencere, "Uyarı", "Önce ürün ekleyin.")
                return
            toplam = hesapla_toplam()
            if toplam <= 0:
                QMessageBox.warning(pencere, "Uyarı", "Toplam tutar 0'dan büyük olmalı.")
                return
            # Satış öncesi stok kontrolü
            stok_eksikleri = []
            try:
                with baglan() as conn_kontrol:
                    cur_kontrol = conn_kontrol.cursor()
                    for rr in range(tabloKalem.rowCount()):
                        kid_text = tabloKalem.item(rr, 5).text() if tabloKalem.columnCount() > 5 and tabloKalem.item(rr, 5) else ""
                        adet_kontrol = parse_sayi(tabloKalem.item(rr, 1).text() if tabloKalem.item(rr, 1) else "0")
                        if kid_text:
                            cur_kontrol.execute("SELECT ad, COALESCE(stok,0) FROM urunler WHERE id=?", (int(kid_text),))
                            stok_row = cur_kontrol.fetchone()
                            if stok_row and float(stok_row[1] or 0) < adet_kontrol:
                                stok_eksikleri.append(f"{stok_row[0]}: stok {float(stok_row[1] or 0):g}, istenen {adet_kontrol:g}")
            except Exception:
                stok_eksikleri = []

            if stok_eksikleri:
                QMessageBox.warning(pencere, "Stok Yetersiz", "Bazı ürünlerde yeterli stok yok:\n\n" + "\n".join(stok_eksikleri))
                return

            tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
            notlar = txtNot.toPlainText().strip()
            aciklama = (notlar or "Ürün satış kaydı") + "\n\n" + ozet_metni()
            with db_baglan() as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO hareketler(cari_id, tip, tutar, aciklama, tarih) VALUES (?, 'BORÇ', ?, ?, ?)",
                    (cari["id"], toplam, aciklama, tarih)
                )
                hareket_id = cur.lastrowid
                cur.execute(
                    "INSERT INTO satislar(cari_id, tarih, toplam, notlar, hareket_id, belge_turu) VALUES (?, ?, ?, ?, ?, 'SATIŞ')",
                    (cari["id"], tarih, toplam, notlar, hareket_id)
                )
                satis_id = cur.lastrowid
                for r in range(tabloKalem.rowCount()):
                    urun = tabloKalem.item(r, 0).text() if tabloKalem.item(r, 0) else ""
                    adet = parse_sayi(tabloKalem.item(r, 1).text() if tabloKalem.item(r, 1) else "0")
                    fiyat = parse_sayi(tabloKalem.item(r, 2).text() if tabloKalem.item(r, 2) else "0")
                    grup = tabloKalem.item(r, 4).text() if tabloKalem.item(r, 4) else ""
                    tutar = adet * fiyat
                    cur.execute(
                        "INSERT INTO satis_kalemleri(satis_id, grup_adi, urun_adi, adet, birim_fiyat, tutar) VALUES (?, ?, ?, ?, ?, ?)",
                        (satis_id, grup, urun, adet, fiyat, tutar)
                    )
                    kid_text = tabloKalem.item(r, 5).text() if tabloKalem.columnCount() > 5 and tabloKalem.item(r, 5) else ""
                    if kid_text:
                        cur.execute("UPDATE urunler SET stok = COALESCE(stok,0) - ? WHERE id=? AND COALESCE(stok,0) >= ?", (adet, int(kid_text), adet))
                        if cur.rowcount == 0:
                            raise ValueError("Stok güncelleme sırasında yetersiz stok algılandı.")
            QMessageBox.information(pencere, "Kaydedildi", f"Satış kaydı oluşturuldu, stok düşüldü ve {cari['ad']} carisine BORÇ işlendi.\nToplam: {para_yaz(toplam)}")
            liste_temizle()
            cari_liste_yukle_urun()
            self.ozet_yukle()

        # Performans: yazdıkça her harfte veritabanı + tablo yenileme yapmak takılma yapıyordu.
        # 220 ms bekletmeli yükleme ile kullanıcı yazmayı bitirince tek sorgu çalışır.
        cari_arama_timer = QTimer(pencere)
        cari_arama_timer.setSingleShot(True)
        cari_arama_timer.setInterval(220)
        cari_arama_timer.timeout.connect(cari_liste_yukle_urun)

        urun_arama_timer = QTimer(pencere)
        urun_arama_timer.setSingleShot(True)
        urun_arama_timer.setInterval(220)
        urun_arama_timer.timeout.connect(urunleri_yukle)

        tabloCari.cellClicked.connect(lambda r, c: cari_secildi())
        tabloCari.cellDoubleClicked.connect(lambda r, c: cari_secildi())
        txtCariAra.textChanged.connect(lambda _text: cari_arama_timer.start())
        tabloKalem.itemChanged.connect(lambda item: hesapla_toplam() if item.column() in [1, 2] and not hesaplama_yapiliyor["aktif"] else None)
        txtUrunAra.textChanged.connect(lambda _text: urun_arama_timer.start())
        txtBarkodOku.returnPressed.connect(barkod_oku_ve_ekle)
        cmbGrup.currentIndexChanged.connect(grup_combo_degisti)
        tabloUrun.itemSelectionChanged.connect(urun_satiri_secildi)
        tabloUrun.cellDoubleClicked.connect(lambda r, c: secili_urunu_satisa_ekle())
        btnYeniCari.clicked.connect(lambda: (self.yeni_cari(), cari_liste_yukle_urun()))
        btnGrupEkle.clicked.connect(lambda: grup_ekle(pencere, durum, gruplari_yukle))
        btnGrupDuzenle.clicked.connect(lambda: grup_duzenle(pencere, durum, gruplari_yukle))
        btnGrupSil.clicked.connect(lambda: grup_sil(pencere, durum, gruplari_yukle))
        btnUrunEkle.clicked.connect(lambda: urun_ekle(pencere, durum, urunleri_yukle))
        btnUrunDuzenle.clicked.connect(lambda: urun_duzenle(pencere, durum, urunleri_yukle))
        btnUrunSil.clicked.connect(lambda: urun_sil(pencere, durum, urunleri_yukle))
        btnSatirSil.clicked.connect(satir_sil)
        btnTemizle.clicked.connect(liste_temizle)
        btnProformaKaydet.clicked.connect(kaydet_proforma)
        btnKaydetCariBorc.clicked.connect(kaydet_cariye_borc)
        btnOzetKopyala.clicked.connect(ozet_kopyala)
        btnMail.clicked.connect(mail_ac)
        btnYazdir.clicked.connect(yazdir)
        btnPdfKaydet.clicked.connect(pdf_kaydet)
        btnGecmis.clicked.connect(satis_gecmisi)
        btnYenile.clicked.connect(lambda: (cari_liste_yukle_urun(), gruplari_yukle(), hesapla_toplam()))

        # Gerçek fonksiyon tuşları: odak QLineEdit içinde olsa bile çalışır.
        self._satis_shortcuts = getattr(self, "_satis_shortcuts", [])
        def _shortcut(seq, func):
            sc = QShortcut(QKeySequence(seq), pencere)
            sc.setContext(Qt.ApplicationShortcut)
            sc.activated.connect(func)
            self._satis_shortcuts.append(sc)
            return sc

        def _f2_cari():
            txtCariAra.setFocus()
            txtCariAra.selectAll()
        def _f3_barkod():
            txtBarkodOku.setFocus()
            txtBarkodOku.selectAll()
        _shortcut("F2", _f2_cari)
        _shortcut("F3", _f3_barkod)
        _shortcut("F4", kaydet_proforma)
        _shortcut("F5", kaydet_cariye_borc)
        _shortcut("Esc", liste_temizle)
        btnF2Cari.clicked.connect(_f2_cari)
        btnF3Barkod.clicked.connect(_f3_barkod)
        btnF4Proforma.clicked.connect(kaydet_proforma)
        btnF5Kaydet.clicked.connect(kaydet_cariye_borc)
        btnEscTemizle.clicked.connect(liste_temizle)
        _shortcut("Return", lambda: secili_urunu_satisa_ekle() if tabloUrun.hasFocus() else None)
        _shortcut("Enter", lambda: secili_urunu_satisa_ekle() if tabloUrun.hasFocus() else None)

        btnProformaKaydet.setShortcut(QKeySequence("F4"))
        btnKaydetCariBorc.setShortcut(QKeySequence("F5"))
        btnTemizle.setShortcut(QKeySequence("Esc"))

        cari_liste_yukle_urun()
        gruplari_yukle()
        hesapla_toplam()

        # v100: Satış ekranı gerçek responsive hale getirildi.
        # Küçük ekranlarda paneller taşmak yerine otomatik daralır, gereksiz kolon gizlenir,
        # butonlar tek satıra düşer ve sağ işlem alanı kesilmez.
        def _satis_responsive_ayarla():
            try:
                genislik = pencere.width() if pencere.width() > 0 else 1280
                kucuk = genislik < 1280
                cok_kucuk = genislik < 1120

                sol_panel.setMaximumWidth(200 if kucuk else 240)
                sol_panel.setMinimumWidth(145 if cok_kucuk else 175)
                orta_panel.setMinimumWidth(200 if cok_kucuk else 235)
                sag_panel.setMinimumWidth(250 if cok_kucuk else 280)
                if cok_kucuk:
                    kisayol_kutu.setVisible(False)
                    lblGrupBaslik.setVisible(False)
                    toplam_kart.setMinimumWidth(170)
                else:
                    kisayol_kutu.setVisible(True)
                    lblGrupBaslik.setVisible(True)
                    toplam_kart.setMinimumWidth(210)

                tabloKalem.setColumnHidden(4, True)
                tabloKalem.setColumnWidth(1, 54 if cok_kucuk else 62)
                tabloKalem.setColumnWidth(2, 82 if cok_kucuk else 92)
                tabloKalem.setColumnWidth(3, 82 if cok_kucuk else 92)
                tabloUrun.setColumnWidth(1, 58 if cok_kucuk else 70)
                tabloUrun.setColumnWidth(2, 88 if cok_kucuk else 110)

                if kucuk:
                    btnF4Proforma.setText("F4")
                    btnF5Kaydet.setText("F5")
                    btnEscTemizle.setText("ESC")
                    btnYeniCari.setText("+ Yeni Cari")
                    btnUrunDuzenle.setText("Düzenle")
                    lblUrunIpucu.setText("Çift tıkla: satış listesine ekle.")
                    txtCariAra.setPlaceholderText("Cari ara...")
                    txtUrunAra.setPlaceholderText("Ürün ara...")
                else:
                    btnF4Proforma.setText("F4 Proforma")
                    btnF5Kaydet.setText("F5 Kaydet")
                    btnEscTemizle.setText("ESC Temizle")
                    btnYeniCari.setText("+ Yeni Cari Ekle")
                    lblUrunIpucu.setText("Ürün aramaya yazdıkça sonuçlar altta listelenir. Çift tıklayınca satış listesine eklenir.")
                    txtCariAra.setPlaceholderText("Müşteri adı veya telefon ara...")
                    txtUrunAra.setPlaceholderText("Ürün ara... Yazdıkça altta tüm ürünler listelenir")

                # Ekran yüksekliği azsa tablo yüksekliğini azalt, aksiyon alanını görünür tut.
                yukseklik = pencere.height() if pencere.height() > 0 else 760
                tabloKalem.setMinimumHeight(120 if yukseklik < 760 else 160)
                tabloUrun.setMinimumHeight(120 if yukseklik < 760 else 160)
                aksiyon_panel.setMaximumHeight(175 if yukseklik < 760 else 215)
                if yukseklik < 760:
                    lblUrunIpucu.setVisible(False)
                else:
                    lblUrunIpucu.setVisible(True)
            except Exception:
                pass

        eski_resize = pencere.resizeEvent
        def _resize_event(event):
            _satis_responsive_ayarla()
            if eski_resize:
                return eski_resize(event)
        pencere.resizeEvent = _resize_event
        _satis_responsive_ayarla()

        pencere.setLayout(ana)
        if embedded:
            pencere.setWindowFlags(Qt.Widget)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll.setWidget(pencere)
            return scroll
        pencere.exec()

