from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
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

from moduller.async_worker import VeriYukleyiciWorker
from moduller.perf_utils import debounce
from moduller.performance_profile import log_event, now_ms
from moduller.sistem import master_sifre_dogrula
from moduller.yardimci import para_yaz
from services.stok_service import stok_liste_sayfasi, stok_ozetleri


class StokMixin:

    def stok_sayfasi_olustur(self):
        sayfa = QFrame()
        sayfa.setStyleSheet("background:#F8FAFC;")
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        if not hasattr(self, "stok_sifreli_alan_acik"):
            self.stok_sifreli_alan_acik = False
        if not hasattr(self, "stok_sayfa_no"):
            self.stok_sayfa_no = 1
        if not hasattr(self, "stok_liste_limit"):
            self.stok_liste_limit = 120

        ust = QFrame()
        ust.setObjectName("TopBar")
        ust_l = QHBoxLayout()
        ust_l.setContentsMargins(18, 14, 18, 14)

        baslik = QLabel("📦 Stok Yönetimi")
        baslik.setStyleSheet("font-size:26px;font-weight:800;color:#0F172A;")
        ust_l.addWidget(baslik)
        ust_l.addStretch()

        self.txtStokAra = QLineEdit()
        self.txtStokAra.setPlaceholderText("Ürün adı / grup / barkod ara...")
        self.txtStokAra.setMinimumWidth(230)
        self.txtStokAra.setMaximumWidth(420)
        self.txtStokAra.textChanged.connect(debounce(self, "_stok_arama_timer", self._stok_sayfa_resetle, 260))
        ust_l.addWidget(self.txtStokAra)
        self.cmbStokFaturaFiltre = QComboBox()
        self.cmbStokFaturaFiltre.addItems(["Tümü", "Faturalı", "Faturasız"])
        self.cmbStokFaturaFiltre.setFixedWidth(120)
        self.cmbStokFaturaFiltre.currentIndexChanged.connect(debounce(self, "_stok_filtre_timer", self._stok_sayfa_resetle, 120))
        ust_l.addWidget(self.cmbStokFaturaFiltre)

        ust.setLayout(ust_l)
        layout.addWidget(ust)

        butonlar = QHBoxLayout()
        butonlar.setSpacing(10)

        def btn(text, func, primary=False):
            b = QPushButton(text)
            b.setMinimumHeight(42)
            b.setObjectName("PrimaryButton" if primary else "SecondaryButton")
            if primary:
                b.setStyleSheet("""
                    QPushButton#PrimaryButton {
                        background:#2563EB;
                        color:#FFFFFF;
                        border:none
                        border-radius:12px
                        padding:10px 16px
                        font-size:14px
                        font-weight:800
                    }
                    QPushButton#PrimaryButton:hover { background:#1D4ED8; }
                """)
            else:
                b.setStyleSheet("""
                    QPushButton#SecondaryButton {
                        background:#FFFFFF;
                        color:#0F172A;
                        border:1px solid #CBD5E1;
                        border-radius:12px
                        padding:10px 16px
                        font-size:14px
                        font-weight:800
                    }
                    QPushButton#SecondaryButton:hover { background:#EEF2FF; border-color:#2563EB; }
                """)
            b.clicked.connect(func)
            butonlar.addWidget(b)
            return b

        btn("Ürün Alış / Stok Girişi", lambda: self.sayfa_goster("alis"), True)
        btn("Eski Stok Raporu", self.stok_raporu_penceresi)
        btn("Yenile", self.stok_sayfa_yenile)
        self.btnStokOnceki = btn("◀ Önceki", self.stok_onceki_sayfa)
        self.lblStokSayfaNo = QLabel("Sayfa 1")
        self.lblStokSayfaNo.setStyleSheet("font-weight:800;color:#475569;padding:8px 4px;")
        butonlar.addWidget(self.lblStokSayfaNo)
        self.cmbStokSayfaLimit = QComboBox()
        self.cmbStokSayfaLimit.addItems(["100", "250", "500"])
        self.cmbStokSayfaLimit.setCurrentText(str(min(500, max(100, int(getattr(self, "stok_liste_limit", 120) or 120)))))
        self.cmbStokSayfaLimit.setFixedWidth(82)
        self.cmbStokSayfaLimit.currentTextChanged.connect(self.stok_sayfa_limiti_degisti)
        butonlar.addWidget(self.cmbStokSayfaLimit)
        self.btnStokSonraki = btn("Sonraki ▶", self.stok_sonraki_sayfa)
        btn("Sütunları Sıfırla", self.stok_tablo_ayarlari_sifirla)
        self.btnStokSifreliAlan = btn("🔒 Şifreli Alan Aç", self.stok_sifreli_alan_degistir)

        layout.addLayout(butonlar)

        # v128: Ürün/Stok özet kartları
        stok_ozet_satir = QHBoxLayout()
        stok_ozet_satir.setSpacing(10)
        self.lblStokKpiUrun = QLabel("Toplam Ürün\n0")
        self.lblStokKpiMiktar = QLabel("Toplam Stok\n0")
        self.lblStokKpiKritik = QLabel("Kritik Stok\n0")
        for lbl in (self.lblStokKpiUrun, self.lblStokKpiMiktar, self.lblStokKpiKritik):
            lbl.setMinimumHeight(64)
            lbl.setStyleSheet("background:#FFFFFF;border:1px solid #E2E8F0;border-radius:14px;padding:10px 12px;color:#0F172A;font-weight:900;")
            stok_ozet_satir.addWidget(lbl)
        layout.addLayout(stok_ozet_satir)

        kart = QFrame()
        kart.setObjectName("MainCard")
        kart_l = QVBoxLayout()
        kart_l.setContentsMargins(12, 12, 12, 12)

        ozet_satir = QHBoxLayout()
        self.lblStokOzet = QLabel("Stok Özeti")
        self.lblStokOzet.setStyleSheet("font-weight:800;color:#64748B;padding:4px;")
        ozet_satir.addWidget(self.lblStokOzet)
        ozet_satir.addStretch()
        self.lblStokSifreliAlan = QLabel("Şifreli Alan: KAPALI")
        self.lblStokSifreliAlan.setStyleSheet("font-weight:800;color:#DC2626;padding:4px;")
        ozet_satir.addWidget(self.lblStokSifreliAlan)
        kart_l.addLayout(ozet_satir)

        self.tblStokSayfa = QTableWidget()
        self.tblStokSayfa.setColumnCount(9)
        self.tblStokSayfa.setHorizontalHeaderLabels([
            "Grup", "Ürün", "Barkod", "Stok", "Satış Fiyatı",
            "Son Alış TL", "Kâr/Adet", "Fatura", "Durum"
        ])
        # Stok tablosu: kullanıcı sütunları program üzerinden sürükleyerek ayarlayabilir.
        # Grup sütunu dar, Ürün sütunu geniş, diğer alanlar okunabilir sabit genişliktedir.
        header = self.tblStokSayfa.horizontalHeader()
        # Güvenlik için maliyet/kâr kolonları sabit mantıksal sırada kalır.
        # Kullanıcı sürükleme yaparsa kolon gizleme karışmasın diye kapalı.
        header.setSectionsMovable(False)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setMinimumSectionSize(55)
        self.tblStokSayfa.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tblStokSayfa.setWordWrap(False)
        self.tblStokSayfa.setTextElideMode(Qt.ElideRight)
        self.tblStokSayfa.setColumnWidth(0, 120)  # Grup
        self.tblStokSayfa.setColumnWidth(1, 280)  # Ürün
        self.tblStokSayfa.setColumnWidth(2, 140)  # Barkod
        self.tblStokSayfa.setColumnWidth(3, 70)   # Stok
        self.tblStokSayfa.setColumnWidth(4, 125)  # Satış Fiyatı
        self.tblStokSayfa.setColumnWidth(5, 125)  # Son Alış TL
        self.tblStokSayfa.setColumnWidth(6, 125)  # Kâr/Adet
        self.tblStokSayfa.setColumnWidth(7, 110)  # Fatura
        self.tblStokSayfa.setColumnWidth(8, 95)   # Durum
        try:
            self.stok_tablo_ayarlarini_yukle()
            header.sectionResized.connect(lambda *args: self.stok_tablo_ayarlarini_kaydet())
            # Kolon taşıma kapalı; maliyet/kâr gizleme güvenliği için sectionMoved kaydı kullanılmıyor.
        except Exception:
            pass
        self.tblStokSayfa.setSelectionBehavior(QTableWidget.SelectRows)
        self.tblStokSayfa.setSelectionMode(QTableWidget.SingleSelection)
        self.tblStokSayfa.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tblStokSayfa.verticalHeader().setVisible(False)
        self.tblStokSayfa.setAlternatingRowColors(True)
        self.tblStokSayfa.setStyleSheet("""
            QTableWidget {
                background:#FFFFFF;
                alternate-background-color:#F8FAFC;
                gridline-color:#E2E8F0;
                color:#0F172A;
                selection-background-color:#2563EB;
                selection-color:#FFFFFF;
            }
            QTableWidget::item {
                padding:6px
                color:#0F172A;
            }
            QTableWidget::item:selected {
                background:#2563EB;
                color:#FFFFFF;
                border:1px solid #1D4ED8;
            }
            QHeaderView::section {
                background:#F1F5F9;
                color:#334155;
                font-weight:800
                padding:8px
                border:none
                border-right:1px solid #E2E8F0;
            }
        """)

        self.stok_sifreli_alan_guncelle()

        try:
            self.tblStokSayfa.cellDoubleClicked.connect(
                lambda r, c: self.stok_hareket_gecmisi_penceresi()
            )
        except Exception:
            pass

        kart_l.addWidget(self.tblStokSayfa, 1)
        kart.setLayout(kart_l)
        layout.addWidget(kart, 1)

        sayfa.setLayout(layout)
        return sayfa


    def stok_sifreli_alan_guncelle(self):
        """Son Alış TL ve Kâr/Adet kolonlarını ana şifre durumuna göre gösterir/gizler."""
        if not hasattr(self, "tblStokSayfa"):
            return

        acik = bool(getattr(self, "stok_sifreli_alan_acik", False))

        # 5: Son Alış TL, 6: Kâr/Adet
        # Bu iki kolon sadece ana şifre ile açılan şifreli alanda görünür.
        for col in (5, 6):
            try:
                self.tblStokSayfa.setColumnHidden(col, not acik)
            except Exception:
                pass

        if hasattr(self, "lblStokSifreliAlan"):
            self.lblStokSifreliAlan.setText("Şifreli Alan: AÇIK" if acik else "Şifreli Alan: KAPALI")
            self.lblStokSifreliAlan.setStyleSheet(
                "font-weight:800;color:#059669;padding:4px;" if acik
                else "font-weight:800;color:#DC2626;padding:4px;"
            )

        if hasattr(self, "btnStokSifreliAlan"):
            self.btnStokSifreliAlan.setText("🔓 Şifreli Alanı Kapat" if acik else "🔒 Şifreli Alan Aç")

    def stok_sifreli_alan_degistir(self):
        """Maliyet ve kâr bilgilerini yalnızca ana şifre ile açar."""
        if getattr(self, "stok_sifreli_alan_acik", False):
            self.stok_sifreli_alan_acik = False
            self.stok_sifreli_alan_guncelle()
            return

        master, ok = QInputDialog.getText(
            self,
            "Ana Şifre",
            "Son Alış TL ve Kâr/Adet bilgilerini görmek için ana şifreyi girin:",
            QLineEdit.Password
        )

        if not ok:
            return

        if not master_sifre_dogrula(master.strip()):
            QMessageBox.warning(self, "Hata", "Ana şifre yanlış.")
            return

        self.stok_sifreli_alan_acik = True
        self.stok_sifreli_alan_guncelle()

    def stok_tablo_ayarlarini_yukle(self):
        """Stok tablosu sütun genişliği/sırasını kullanıcı ayarlarından yükler."""
        if not hasattr(self, "tblStokSayfa"):
            return
        ayar = QSettings("DAL_ERP", "CariTakip")
        widths = ayar.value("stok_tablo/widths", "")
        if widths:
            try:
                for i, w in enumerate(str(widths).split(",")):
                    if i < self.tblStokSayfa.columnCount() and w.strip():
                        self.tblStokSayfa.setColumnWidth(i, max(55, int(w)))
            except Exception:
                pass

        # Kolon sırası güvenlik nedeniyle sabit tutulur.
        # Son Alış TL ve Kâr/Adet kolonlarının yanlışlıkla görünmesini engeller.

    def stok_tablo_ayarlarini_kaydet(self):
        """Kullanıcı sütunları sürükleyip genişlettiğinde ayarları kaydeder."""
        if not hasattr(self, "tblStokSayfa"):
            return
        ayar = QSettings("DAL_ERP", "CariTakip")
        header = self.tblStokSayfa.horizontalHeader()
        widths = [str(self.tblStokSayfa.columnWidth(i)) for i in range(self.tblStokSayfa.columnCount())]
        order = [str(header.logicalIndex(i)) for i in range(self.tblStokSayfa.columnCount())]
        ayar.setValue("stok_tablo/widths", ",".join(widths))
        ayar.setValue("stok_tablo/order", ",".join(order))

    def stok_tablo_ayarlari_sifirla(self):
        """Stok tablosu sütunlarını varsayılan okunabilir ölçülere döndürür."""
        if not hasattr(self, "tblStokSayfa"):
            return
        ayar = QSettings("DAL_ERP", "CariTakip")
        ayar.remove("stok_tablo/widths")
        ayar.remove("stok_tablo/order")
        header = self.tblStokSayfa.horizontalHeader()
        for visual in range(header.count()):
            logical = header.logicalIndex(visual)
            if logical != visual:
                header.moveSection(visual, logical)
        widths = [120, 280, 140, 70, 125, 125, 125, 110, 95]
        for i, w in enumerate(widths):
            self.tblStokSayfa.setColumnWidth(i, w)
        self.stok_sifreli_alan_guncelle()
        self.stok_tablo_ayarlarini_kaydet()

    def stok_sayfasi_sutun_ayarlari_butonu_ekle(self):
        pass

    def stok_onceki_sayfa(self):
        """Stok listesini bir önceki sayfaya alır."""
        self.stok_sayfa_no = max(1, int(getattr(self, "stok_sayfa_no", 1) or 1) - 1)
        self.stok_sayfa_yenile()

    def stok_sonraki_sayfa(self):
        """Stok listesini bir sonraki sayfaya alır."""
        self.stok_sayfa_no = int(getattr(self, "stok_sayfa_no", 1) or 1) + 1
        self.stok_sayfa_yenile()

    def _stok_sayfa_resetle(self):
        """Arama/filtre değişimlerinde listeyi ilk sayfaya döndürür."""
        self.stok_sayfa_no = 1
        self.stok_sayfa_yenile()

    def stok_sayfa_limiti_degisti(self, text):
        """Sayfa başına kayıt sayısı değiştiğinde listeyi ilk sayfadan yeniler."""
        try:
            self.stok_liste_limit = int(text)
        except (TypeError, ValueError):
            self.stok_liste_limit = 120
        self.stok_sayfa_no = 1
        self.stok_sayfa_yenile()

    def stok_sayfa_yenile(self):
        """V50: Stok listesini arka planda yükler; UI thread donmasını azaltır."""
        if not hasattr(self, "tblStokSayfa"):
            return

        if getattr(self, "_stok_async_yukleniyor", False):
            self._stok_async_bekleyen_yenile = True
            return

        arama = self.txtStokAra.text().strip() if hasattr(self, "txtStokAra") else ""
        fatura_filtre = self.cmbStokFaturaFiltre.currentText() if hasattr(self, "cmbStokFaturaFiltre") else "Tümü"
        limit = max(50, min(500, int(getattr(self, "stok_liste_limit", 120) or 120)))
        sayfa_no = max(1, int(getattr(self, "stok_sayfa_no", 1) or 1))
        started_ms = now_ms()

        self._stok_async_yukleniyor = True
        self._stok_async_bekleyen_yenile = False

        if hasattr(self, "lblStokOzet"):
            self.lblStokOzet.setText("Stok listesi yükleniyor...")

        for attr in ("btnStokOnceki", "btnStokSonraki", "cmbStokSayfaLimit"):
            if hasattr(self, attr):
                try:
                    getattr(self, attr).setEnabled(False)
                except Exception:
                    pass

        def yukle():
            ozet = stok_ozetleri()
            sonuc = stok_liste_sayfasi(
                arama=arama,
                fatura_filtre=fatura_filtre,
                sayfa_no=sayfa_no,
                limit=limit,
            )
            return {
                "ozet": ozet,
                "sonuc": sonuc,
                "started_ms": started_ms,
                "arama": arama,
                "fatura_filtre": fatura_filtre,
            }

        worker = VeriYukleyiciWorker(yukle)
        worker.veri_hazir.connect(self._stok_async_sonuc_isle)
        worker.hata_olustu.connect(self._stok_async_hata_isle)
        worker.bitti.connect(self._stok_async_bitti)
        self._stok_async_worker = worker
        worker.start()

    def _stok_async_sonuc_isle(self, payload):
        """V50: Arka planda gelen stok sonucunu UI tablosuna basar."""
        try:
            o = payload["ozet"]
            if hasattr(self, "lblStokKpiUrun"):
                self.lblStokKpiUrun.setText(f"Toplam Ürün\n{o['toplam_urun']}")
                self.lblStokKpiMiktar.setText(f"Toplam Stok\n{o['toplam_stok']:.0f}")
                self.lblStokKpiKritik.setText(f"Kritik Stok\n{o['kritik']}")

            self._stok_tablo_sonuc_yaz(
                payload["sonuc"],
                payload["started_ms"],
                payload["arama"],
                payload["fatura_filtre"],
            )
        except Exception as hata:
            QMessageBox.warning(self, "Hata", f"Stok listesi işlenemedi:\n{hata}")

    def _stok_async_hata_isle(self, detay):
        QMessageBox.warning(self, "Hata", f"Stok listesi yüklenemedi:\n{detay}")

    def _stok_async_bitti(self):
        self._stok_async_yukleniyor = False
        self._stok_async_worker = None

        for attr in ("cmbStokSayfaLimit",):
            if hasattr(self, attr):
                try:
                    getattr(self, attr).setEnabled(True)
                except Exception:
                    pass

        if getattr(self, "_stok_async_bekleyen_yenile", False):
            self._stok_async_bekleyen_yenile = False
            self.stok_sayfa_yenile()

    def _stok_tablo_sonuc_yaz(self, sonuc, started_ms, arama, fatura_filtre):
        rows = sonuc.rows
        toplam_kayit = sonuc.toplam_kayit
        sayfa_no = sonuc.sayfa_no
        max_sayfa = sonuc.max_sayfa
        limit = sonuc.limit
        offset = sonuc.offset
        self.stok_sayfa_no = sayfa_no

        self.tblStokSayfa.setUpdatesEnabled(False)
        self.tblStokSayfa.setSortingEnabled(False)
        self.tblStokSayfa.clearSelection()
        self.tblStokSayfa.setRowCount(len(rows))

        kritik = az = normal = 0

        try:
            for r, (grup, uid, ad, barkod, stok, satis, son_alis, fatura_durumu) in enumerate(rows):
                stok = float(stok or 0)
                satis = float(satis or 0)
                son_alis = float(son_alis or 0)
                kar = satis - son_alis if son_alis > 0 else 0

                if stok <= 5:
                    durum = "KRİTİK"
                    kritik += 1
                elif stok <= 10:
                    durum = "AZ"
                    az += 1
                else:
                    durum = "NORMAL"
                    normal += 1

                vals = [
                    grup or "-",
                    ad or "",
                    barkod or "",
                    str(stok).rstrip("0").rstrip("."),
                    para_yaz(satis),
                    para_yaz(son_alis),
                    para_yaz(kar),
                    "Faturalı" if str(fatura_durumu or "FATURALI").upper() == "FATURALI" else "Faturasız",
                    durum,
                ]

                for c, val in enumerate(vals):
                    item = QTableWidgetItem(str(val))
                    item.setData(1000, int(uid))

                    if durum == "KRİTİK":
                        item.setBackground(QColor("#FEE2E2"))
                        item.setForeground(QColor("#7F1D1D"))
                    elif durum == "AZ":
                        item.setBackground(QColor("#FEF3C7"))
                        item.setForeground(QColor("#78350F"))
                    elif str(fatura_durumu or "FATURALI").upper() == "FATURASIZ":
                        item.setBackground(QColor("#FFF7ED"))
                        item.setForeground(QColor("#7C2D12"))
                    elif str(fatura_durumu or "FATURALI").upper() == "FATURALI":
                        item.setBackground(QColor("#F0FDF4"))
                        item.setForeground(QColor("#14532D"))

                    self.tblStokSayfa.setItem(r, c, item)

        finally:
            self.tblStokSayfa.setUpdatesEnabled(True)
            self.tblStokSayfa.viewport().update()

        gosterilen = len(rows)
        baslangic = offset + 1 if toplam_kayit else 0
        bitis = offset + gosterilen
        ek = (
            f"   •   Sayfa: {sayfa_no}/{max_sayfa}   •   Gösterilen: {baslangic}-{bitis} / {toplam_kayit}"
            if toplam_kayit > gosterilen
            else f"   •   Toplam: {gosterilen}"
        )

        if hasattr(self, "lblStokSayfaNo"):
            self.lblStokSayfaNo.setText(f"Sayfa {sayfa_no}/{max_sayfa}")

        if hasattr(self, "cmbStokSayfaLimit") and self.cmbStokSayfaLimit.currentText() != str(limit):
            self.cmbStokSayfaLimit.blockSignals(True)
            self.cmbStokSayfaLimit.setCurrentText(str(limit))
            self.cmbStokSayfaLimit.blockSignals(False)

        if hasattr(self, "btnStokOnceki"):
            self.btnStokOnceki.setEnabled(sayfa_no > 1)

        if hasattr(self, "btnStokSonraki"):
            self.btnStokSonraki.setEnabled(sayfa_no < max_sayfa)

        self.lblStokOzet.setText(
            f"Kritik: {kritik}   •   Az: {az}   •   Normal: {normal}" + ek
        )
        self.stok_sifreli_alan_guncelle()

        log_event(
            "stok_sayfa_yenile_async",
            now_ms() - started_ms,
            rows=gosterilen,
            total=toplam_kayit,
            page=sayfa_no,
            limit=limit,
            filter=fatura_filtre,
            search=bool(arama),
        )

    def stok_hareket_gecmisi_penceresi(self):
        try:
            self.stok_raporu_penceresi()
        except Exception as hata:
            QMessageBox.warning(self, "Hata", f"Stok hareket geçmişi açılamadı:\n{hata}")

