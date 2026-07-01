from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
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
    QVBoxLayout,
)

from moduller.async_worker import VeriYukleyiciWorker
from moduller.perf_utils import debounce, fill_table_fast
from moduller.performance_profile import log_event, now_ms
from moduller.yardimci import para_yaz
from services.cari_service import (
    cari_cache_temizle,
    cari_detay_ozeti,
    cari_liste_sayfasi,
    cari_ozetleri,
)

DEFAULT_CARI_LIMIT = 120
MIN_CARI_LIMIT = 50
MAX_CARI_LIMIT = 500

class CustomerPageMixin:
    def cari_sayfasi_olustur(self):
        """v143: Cari Kartları vitrin ekranı.

        Ekran artık standart ERP sayfa düzenine yaklaştırıldı:
        başlık + araç çubuğu + özet kartları + liste/detay split düzeni.
        Renkler inline sabit renklerden çıkarılıp QSS tema sistemine bağlandı.
        """
        sayfa = QFrame()
        sayfa.setObjectName("CustomerPage")
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        if not hasattr(self, "cari_sayfa_no"):
            self.cari_sayfa_no = 1
        if not hasattr(self, "cari_liste_limit"):
            self.cari_liste_limit = DEFAULT_CARI_LIMIT

        # ÜST BAŞLIK
        ust = QFrame()
        ust.setObjectName("CustomerHeader")
        ust_l = QHBoxLayout()
        ust_l.setContentsMargins(18, 12, 18, 12)
        ust_l.setSpacing(10)

        baslik_blok = QVBoxLayout()
        baslik_blok.setSpacing(2)
        baslik = QLabel("Cari Kartları")
        baslik.setObjectName("CustomerTitle")
        alt = QLabel("Müşteri/tedarikçi kartları, bakiye ve hızlı işlemler")
        alt.setObjectName("CustomerSubtitle")
        baslik_blok.addWidget(baslik)
        baslik_blok.addWidget(alt)
        ust_l.addLayout(baslik_blok)
        ust_l.addStretch()

        self.txtCariSayfaAra = QLineEdit()
        self.txtCariSayfaAra.setObjectName("CustomerSearch")
        self.txtCariSayfaAra.setPlaceholderText("Cari adı, telefon veya adres ara...")
        self.txtCariSayfaAra.setMinimumWidth(260)
        self.txtCariSayfaAra.setMaximumWidth(460)
        self.txtCariSayfaAra.textChanged.connect(debounce(self, "_cari_arama_timer", self._cari_sayfa_resetle, 260))
        ust_l.addWidget(self.txtCariSayfaAra)

        btnYeniUst = QPushButton("＋ Yeni Cari")
        btnYeniUst.setObjectName("CustomerPrimaryButton")
        btnYeniUst.setMinimumWidth(140)
        btnYeniUst.setMaximumWidth(175)
        btnYeniUst.clicked.connect(lambda: self._cari_sayfa_yeni())
        ust_l.addWidget(btnYeniUst)
        ust.setLayout(ust_l)
        layout.addWidget(ust)

        # ARAÇ ÇUBUĞU
        toolbar = QFrame()
        toolbar.setObjectName("CustomerToolbar")
        butonlar = QHBoxLayout()
        butonlar.setContentsMargins(10, 8, 10, 8)
        butonlar.setSpacing(8)

        def btn(text, func, obj="CustomerToolButton"):
            b = QPushButton(text)
            b.setObjectName(obj)
            b.setMinimumHeight(36)
            b.clicked.connect(func)
            butonlar.addWidget(b)
            return b

        btn("✏ Düzenle", lambda: self._cari_sayfa_duzenle())
        btn("🗑 Sil", lambda: self._cari_sayfa_sil(), "CustomerDangerButton")
        btn("↗ Borç", lambda: self._cari_sayfa_islem("BORÇ"))
        btn("↘ Tahsilat", lambda: self._cari_sayfa_islem("TAHSİLAT"), "CustomerSuccessButton")
        btn("📄 Ekstre", lambda: self.cari_ekstre(self.tblCariSayfa))
        btn("⟳ Yenile", self.cari_sayfa_yenile)
        butonlar.addStretch()
        toolbar.setLayout(butonlar)
        layout.addWidget(toolbar)

        # ÖZET KARTLARI
        ozetler = QHBoxLayout()
        ozetler.setSpacing(10)
        self.lblCariOzetToplam = self._customer_metric_label("Toplam Cari", "0")
        self.lblCariOzetBakiye = self._customer_metric_label("Açık Bakiye", "0,00 ₺")
        self.lblCariOzetBorc = self._customer_metric_label("Borç", "0,00 ₺")
        self.lblCariOzetTahsilat = self._customer_metric_label("Tahsilat", "0,00 ₺")
        for lbl in (self.lblCariOzetToplam, self.lblCariOzetBakiye, self.lblCariOzetBorc, self.lblCariOzetTahsilat):
            ozetler.addWidget(lbl)
        layout.addLayout(ozetler)

        govde = QSplitter(Qt.Horizontal)
        govde.setObjectName("CustomerSplitter")
        govde.setChildrenCollapsible(False)

        # SOL: CARİ LİSTESİ
        kart = QFrame()
        kart.setObjectName("CustomerListCard")
        kart_l = QVBoxLayout()
        kart_l.setContentsMargins(12, 12, 12, 12)
        kart_l.setSpacing(8)

        list_header = QHBoxLayout()
        lbl_liste = QLabel("Cari Listesi")
        lbl_liste.setObjectName("CustomerSectionTitle")
        self.lblCariSayfaKayit = QLabel("Toplam Cari: 0")
        self.lblCariSayfaKayit.setObjectName("CustomerBadge")
        list_header.addWidget(lbl_liste)
        list_header.addStretch()

        self.btnCariOnceki = QPushButton("◀ Önceki")
        self.btnCariOnceki.setObjectName("CustomerToolButton")
        self.btnCariOnceki.clicked.connect(self.cari_onceki_sayfa)
        list_header.addWidget(self.btnCariOnceki)

        self.lblCariSayfaNo = QLabel("Sayfa 1/1")
        self.lblCariSayfaNo.setObjectName("CustomerBadge")
        list_header.addWidget(self.lblCariSayfaNo)

        self.btnCariSonraki = QPushButton("Sonraki ▶")
        self.btnCariSonraki.setObjectName("CustomerToolButton")
        self.btnCariSonraki.clicked.connect(self.cari_sonraki_sayfa)
        list_header.addWidget(self.btnCariSonraki)

        self.cmbCariSayfaLimit = QComboBox()
        self.cmbCariSayfaLimit.addItems(["100", "250", "500"])
        self.cmbCariSayfaLimit.setCurrentText(str(getattr(self, "cari_liste_limit", 120)))
        self.cmbCariSayfaLimit.currentTextChanged.connect(self.cari_sayfa_limiti_degisti)
        list_header.addWidget(self.cmbCariSayfaLimit)

        list_header.addWidget(self.lblCariSayfaKayit)
        kart_l.addLayout(list_header)

        self.tblCariSayfa = QTableWidget()
        self.tblCariSayfa.setObjectName("CustomerTable")
        self.tblCariSayfa.setColumnCount(5)
        self.tblCariSayfa.setHorizontalHeaderLabels(["No", "Cari Adı", "Telefon", "Adres", "Bakiye"])
        self.tblCariSayfa.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tblCariSayfa.setSelectionBehavior(QTableWidget.SelectRows)
        self.tblCariSayfa.setSelectionMode(QTableWidget.SingleSelection)
        self.tblCariSayfa.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tblCariSayfa.verticalHeader().setVisible(False)
        self.tblCariSayfa.setAlternatingRowColors(True)
        self.tblCariSayfa.setWordWrap(False)
        self.tblCariSayfa.setTextElideMode(Qt.ElideRight)
        self.tblCariSayfa.itemSelectionChanged.connect(self.cari_detay_karti_guncelle)
        self.tblCariSayfa.cellDoubleClicked.connect(lambda r, c: self.cari_detay_penceresi(self.tblCariSayfa))
        kart_l.addWidget(self.tblCariSayfa, 1)
        kart.setLayout(kart_l)
        govde.addWidget(kart)

        # SAĞ: SEÇİLİ CARİ ÖZET KARTI
        detay_scroll = QScrollArea()
        detay_scroll.setObjectName("CustomerDetailScroll")
        detay_scroll.setWidgetResizable(True)
        detay_scroll.setFrameShape(QFrame.NoFrame)

        detay = QFrame()
        detay.setObjectName("CustomerDetailCard")
        detay.setMinimumWidth(320)
        detay_l = QVBoxLayout()
        detay_l.setContentsMargins(16, 16, 16, 16)
        detay_l.setSpacing(10)

        lblDetayBaslik = QLabel("Seçili Cari")
        lblDetayBaslik.setObjectName("CustomerSectionTitle")
        detay_l.addWidget(lblDetayBaslik)

        self.lblCariDetayAd = QLabel("Henüz cari seçilmedi")
        self.lblCariDetayAd.setObjectName("CustomerSelectedName")
        self.lblCariDetayAd.setWordWrap(True)
        self.lblCariDetayAd.setMinimumHeight(58)
        detay_l.addWidget(self.lblCariDetayAd)

        self.lblCariDetayBilgi = QLabel("Listeden bir cari seçince detaylar burada görünür.")
        self.lblCariDetayBilgi.setObjectName("CustomerDetailInfo")
        self.lblCariDetayBilgi.setWordWrap(True)
        detay_l.addWidget(self.lblCariDetayBilgi)

        self.lblCariDetayBakiye = QLabel("Bakiye\n0,00 ₺")
        self.lblCariDetayBakiye.setObjectName("CustomerBalanceCard")
        self.lblCariDetayBakiye.setMinimumHeight(76)
        detay_l.addWidget(self.lblCariDetayBakiye)

        self.lblCariDetayBorcTahsilat = QLabel("Borç: 0,00 ₺\nTahsilat: 0,00 ₺")
        self.lblCariDetayBorcTahsilat.setObjectName("CustomerMiniCard")
        self.lblCariDetayBorcTahsilat.setMinimumHeight(72)
        detay_l.addWidget(self.lblCariDetayBorcTahsilat)

        btnDetaylar = QPushButton("📋 Detay Kartı")
        btnDetaylar.setObjectName("CustomerToolButton")
        btnDetaylar.clicked.connect(lambda: self.cari_detay_penceresi(self.tblCariSayfa))
        detay_l.addWidget(btnDetaylar)

        btnWhats = QPushButton("💬 WhatsApp")
        btnWhats.setObjectName("CustomerSuccessButton")
        btnWhats.clicked.connect(lambda: self.whatsapp_mesaj_gonder(self.secili_cari_bilgisi(self.tblCariSayfa)))
        detay_l.addWidget(btnWhats)
        detay_l.addStretch()
        detay.setLayout(detay_l)
        detay_scroll.setWidget(detay)
        govde.addWidget(detay_scroll)

        govde.setStretchFactor(0, 4)
        govde.setStretchFactor(1, 1)
        layout.addWidget(govde, 1)

        sayfa.setLayout(layout)
        return sayfa

    def _customer_metric_label(self, title, value):
        lbl = QLabel(f"{title}\n{value}")
        lbl.setObjectName("CustomerMetric")
        lbl.setMinimumHeight(62)
        lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        return lbl

    def cari_onceki_sayfa(self):
        self.cari_sayfa_no = max(1, int(getattr(self, "cari_sayfa_no", 1) or 1) - 1)
        self.cari_sayfa_yenile()

    def cari_sonraki_sayfa(self):
        self.cari_sayfa_no = int(getattr(self, "cari_sayfa_no", 1) or 1) + 1
        self.cari_sayfa_yenile()

    def _cari_sayfa_resetle(self):
        self.cari_sayfa_no = 1
        self.cari_sayfa_yenile()

    def cari_sayfa_limiti_degisti(self, text):
        try:
            self.cari_liste_limit = int(text)
        except (TypeError, ValueError):
            self.cari_liste_limit = DEFAULT_CARI_LIMIT
        self.cari_sayfa_no = 1
        self.cari_sayfa_yenile()

    def cari_sayfa_yenile(self):
        if not hasattr(self, "tblCariSayfa"):
            return

        if getattr(self, "_cari_async_yukleniyor", False):
            self._cari_async_bekleyen_yenile = True
            return

        secili_id = None
        try:
            row = self.tblCariSayfa.currentRow()
            item = self.tblCariSayfa.item(row, 0) if row >= 0 else None
            secili_id = item.data(1000) if item else None
        except Exception:
            secili_id = None

        arama = self.txtCariSayfaAra.text() if hasattr(self, "txtCariSayfaAra") else ""
        limit = max(MIN_CARI_LIMIT, min(MAX_CARI_LIMIT, int(getattr(self, "cari_liste_limit", DEFAULT_CARI_LIMIT) or DEFAULT_CARI_LIMIT)))
        sayfa_no = max(1, int(getattr(self, "cari_sayfa_no", 1) or 1))
        started_ms = now_ms()

        self._cari_async_yukleniyor = True
        self._cari_async_bekleyen_yenile = False

        if hasattr(self, "lblCariSayfaKayit"):
            self.lblCariSayfaKayit.setText("Yükleniyor...")

        for attr in ("btnCariOnceki", "btnCariSonraki", "cmbCariSayfaLimit"):
            if hasattr(self, attr):
                try:
                    getattr(self, attr).setEnabled(False)
                except Exception:
                    pass

        def yukle():
            return {
                "sonuc": cari_liste_sayfasi(arama=arama, sayfa_no=sayfa_no, limit=limit),
                "ozet": cari_ozetleri(),
                "secili_id": secili_id,
                "started_ms": started_ms,
                "arama": arama,
            }

        worker = VeriYukleyiciWorker(yukle)
        worker.veri_hazir.connect(self._cari_async_sonuc_isle)
        worker.hata_olustu.connect(self._cari_async_hata_isle)
        worker.bitti.connect(self._cari_async_bitti)
        self._cari_async_worker = worker
        worker.start()

    def _cari_async_sonuc_isle(self, payload):
        try:
            o = payload["ozet"]
            self.lblCariOzetToplam.setText(f"Toplam Cari\n{o['toplam']}")
            self.lblCariOzetBakiye.setText(f"Açık Bakiye\n{para_yaz(o['bakiye'])}")
            self.lblCariOzetBorc.setText(f"Borç\n{para_yaz(o['borc'])}")
            self.lblCariOzetTahsilat.setText(f"Tahsilat\n{para_yaz(o['tahsilat'])}")
            self._cari_tablo_sonuc_yaz(
                payload["sonuc"],
                payload.get("secili_id"),
                payload["started_ms"],
                payload["arama"],
            )
        except Exception as hata:
            self.lblCariSayfaKayit.setText("Yükleme hatası")
            QMessageBox.warning(self, "Hata", f"Cari listesi işlenemedi:\n{hata}")

    def _cari_async_hata_isle(self, detay):
        self.lblCariSayfaKayit.setText("Yükleme hatası")
        QMessageBox.warning(self, "Hata", f"Cari listesi yüklenemedi:\n{detay}")

    def _cari_async_bitti(self):
        self._cari_async_yukleniyor = False
        self._cari_async_worker = None

        if hasattr(self, "cmbCariSayfaLimit"):
            self.cmbCariSayfaLimit.setEnabled(True)

        if getattr(self, "_cari_async_bekleyen_yenile", False):
            self._cari_async_bekleyen_yenile = False
            self.cari_sayfa_yenile()

    def _cari_tablo_sonuc_yaz(self, sonuc, secili_id, started_ms, arama):
        rows = sonuc.rows
        self.cari_sayfa_no = sonuc.sayfa_no
        self._cari_liste_toplam_kayit = sonuc.toplam_kayit

        table_rows = (
            (cari_id, no, ad, telefon, adres, bakiye)
            for cari_id, no, ad, telefon, adres, bakiye in rows
        )

        def cari_formatter(_r, c, value):
            if c == 5:
                return para_yaz(value)
            return value

        fill_table_fast(
            self.tblCariSayfa,
            table_rows,
            id_column=0,
            id_role=1000,
            formatter=cari_formatter,
        )

        gosterilen = len(rows)
        baslangic = sonuc.offset + 1 if sonuc.toplam_kayit else 0
        bitis = sonuc.offset + gosterilen

        if sonuc.toplam_kayit > gosterilen:
            self.lblCariSayfaKayit.setText(f"Gösterilen: {baslangic}-{bitis} / {sonuc.toplam_kayit}")
        else:
            self.lblCariSayfaKayit.setText(f"Toplam Cari: {gosterilen}")

        if hasattr(self, "lblCariSayfaNo"):
            self.lblCariSayfaNo.setText(f"Sayfa {sonuc.sayfa_no}/{sonuc.max_sayfa}")

        if hasattr(self, "cmbCariSayfaLimit") and self.cmbCariSayfaLimit.currentText() != str(sonuc.limit):
            self.cmbCariSayfaLimit.blockSignals(True)
            self.cmbCariSayfaLimit.setCurrentText(str(sonuc.limit))
            self.cmbCariSayfaLimit.blockSignals(False)

        if hasattr(self, "btnCariOnceki"):
            self.btnCariOnceki.setEnabled(sonuc.sayfa_no > 1)
        if hasattr(self, "btnCariSonraki"):
            self.btnCariSonraki.setEnabled(sonuc.sayfa_no < sonuc.max_sayfa)

        if secili_id:
            self.cari_satir_sec(self.tblCariSayfa, secili_id)
        self.cari_detay_karti_guncelle()

        log_event(
            "cari_sayfa_yenile_async",
            now_ms() - started_ms,
            rows=gosterilen,
            total=sonuc.toplam_kayit,
            page=sonuc.sayfa_no,
            limit=sonuc.limit,
            search=bool(arama),
        )

    def _cari_secili_id_al(self):
        if not hasattr(self, "tblCariSayfa"):
            return None
        row = self.tblCariSayfa.currentRow()
        if row < 0:
            return None
        item = self.tblCariSayfa.item(row, 0)
        return item.data(1000) if item else None

    def _cari_detay_bos_goster(self):
        self.lblCariDetayAd.setText("Henüz cari seçilmedi")
        self.lblCariDetayBilgi.setText("Listeden bir cari seçince detaylar burada görünür.")
        self.lblCariDetayBakiye.setText("Bakiye\n0,00 ₺")
        self.lblCariDetayBorcTahsilat.setText("Borç: 0,00 ₺\nTahsilat: 0,00 ₺")

    def _cari_detay_yukleniyor_goster(self):
        self.lblCariDetayAd.setText("Detay yükleniyor...")
        self.lblCariDetayBilgi.setText("Seçili cari bilgileri hazırlanıyor.")
        self.lblCariDetayBakiye.setText("Bakiye\n...")
        self.lblCariDetayBorcTahsilat.setText("Borç: ...\nTahsilat: ...")

    def _cari_detay_yaz(self, detay):
        if detay is None:
            self._cari_detay_bos_goster()
            return
        self.lblCariDetayAd.setText(detay.ad or "-")
        self.lblCariDetayBilgi.setText(
            f"Telefon: {detay.telefon or '-'}\n"
            f"Adres: {detay.adres or '-'}\n"
            f"Vergi Dairesi: {detay.vergi_dairesi or '-'}\n"
            f"Vergi No: {detay.vergi_no or '-'}"
        )
        self.lblCariDetayBakiye.setText(f"Bakiye\n{para_yaz(detay.bakiye)}")
        self.lblCariDetayBorcTahsilat.setText(f"Borç: {para_yaz(detay.borc)}\nTahsilat: {para_yaz(detay.tahsilat)}")

    def cari_detay_karti_guncelle(self):
        if not hasattr(self, "tblCariSayfa") or not hasattr(self, "lblCariDetayAd"):
            return
        cari_id = self._cari_secili_id_al()
        if cari_id is None:
            self._cari_detay_bos_goster()
            return
        try:
            cari_id = int(cari_id)
        except (TypeError, ValueError):
            self._cari_detay_bos_goster()
            return

        token = int(getattr(self, "_cari_detay_async_token", 0) or 0) + 1
        self._cari_detay_async_token = token
        self._cari_detay_yukleniyor_goster()

        def yukle():
            return {"token": token, "cari_id": cari_id, "detay": cari_detay_ozeti(cari_id)}

        worker = VeriYukleyiciWorker(yukle)
        workers = getattr(self, "_cari_detay_async_workers", None)
        if workers is None:
            workers = {}
            self._cari_detay_async_workers = workers
        workers[token] = worker
        worker.veri_hazir.connect(self._cari_detay_async_sonuc_isle)
        worker.hata_olustu.connect(lambda _detay, t=token: self._cari_detay_async_hata_isle(t))
        worker.bitti.connect(lambda t=token: self._cari_detay_async_bitti(t))
        worker.start()

    def _cari_detay_async_sonuc_isle(self, payload):
        token = payload.get("token")
        if token != getattr(self, "_cari_detay_async_token", None):
            return
        if payload.get("cari_id") != self._cari_secili_id_al():
            return
        self._cari_detay_yaz(payload.get("detay"))

    def _cari_detay_async_hata_isle(self, token):
        if token == getattr(self, "_cari_detay_async_token", None):
            self.lblCariDetayBilgi.setText("Cari detay bilgisi yüklenemedi.")

    def _cari_detay_async_bitti(self, token):
        workers = getattr(self, "_cari_detay_async_workers", None)
        if workers is not None:
            workers.pop(token, None)

    def _cari_sayfa_yeni(self):
        yeni_id = self.yeni_cari(self.tblCariSayfa)
        cari_cache_temizle()
        self.cari_sayfa_yenile()
        if yeni_id:
            self.cari_satir_sec(self.tblCariSayfa, yeni_id)
            self.cari_detay_karti_guncelle()

    def _cari_sayfa_duzenle(self):
        self.cari_duzenle(self.tblCariSayfa)
        cari_cache_temizle()
        self.cari_sayfa_yenile()
        self.cari_detay_karti_guncelle()

    def _cari_sayfa_sil(self):
        self.cari_sil(self.tblCariSayfa)
        cari_cache_temizle()
        self.cari_sayfa_yenile()
        self.cari_detay_karti_guncelle()

    def _cari_sayfa_islem(self, tip):
        cari = self.secili_cari_bilgisi(self.tblCariSayfa)
        if cari is None:
            return
        sonuc = self.islem_ekle(self.tblCariSayfa, tip)
        if sonuc:
            cari_cache_temizle()
            self.cari_sayfa_yenile()
            self.cari_satir_sec(self.tblCariSayfa, cari["id"])
            self.cari_detay_karti_guncelle()
            self.ozet_yukle()
