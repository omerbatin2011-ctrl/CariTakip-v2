from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from .db import db_baglan
from .erp_ek_moduller import audit_yaz, bildirimler, cari_yaslandirma_ozeti, kar_zarar_ozeti


def _panel(title):
    w = QFrame()
    w.setObjectName("MainCard")
    w.setStyleSheet("QFrame#MainCard{background:#FFFFFF;border-radius:12px;border:1px solid #E2E8F0;}")
    layout = QVBoxLayout()
    layout.setContentsMargins(18,18,18,18)
    layout.setSpacing(12)
    b = QLabel(title)
    b.setStyleSheet("font-size:22px;font-weight:800;color:#0F172A;")
    layout.addWidget(b)
    w.setLayout(layout)
    return w, layout

class ErpEkMixin:
    def siparis_sayfasi_olustur(self):
        sayfa, layout = _panel("📋 Sipariş Yönetimi")
        sayfa.setStyleSheet("""
            QFrame#MainCard{background:#FFFFFF;border-radius:12px;border:1px solid #E2E8F0;}
            QLineEdit,QComboBox{background:#FFFFFF;border:1px solid #D8E0EA;border-radius:12px;padding:8px 10px;min-height:30px;}
            QPushButton{background:#FFFFFF;color:#0F172A;border:1px solid #D8E0EA;border-radius:12px;padding:8px 12px;font-weight:800;}
            QPushButton:hover{background:#F8FAFC;border-color:#2563EB;}
            QPushButton#PrimaryButton{background:#2563EB;color:white;border:none;}
            QPushButton#DangerButton{background:#FFF1F2;color:#BE123C;border:1px solid #FDA4AF;}
            QTableWidget{background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;gridline-color:#E2E8F0;selection-background-color:#DBEAFE;selection-color:#0F172A;}
            QHeaderView::section{background:#F1F5F9;color:#334155;border:none;padding:8px;font-weight:800;}
        """)
        filtre = QHBoxLayout()
        filtre.setSpacing(10)
        self.cmbSiparisTur = QComboBox()
        self.cmbSiparisTur.addItems(["ALINAN", "VERİLEN"])
        self.txtSiparisCari = QLineEdit()
        self.txtSiparisCari.setPlaceholderText("Cari / tedarikçi ara veya yaz")
        self.txtSiparisTutar = QLineEdit()
        self.txtSiparisTutar.setPlaceholderText("Toplam tutar")
        self.cmbSiparisFatura = QComboBox()
        self.cmbSiparisFatura.addItems(["FATURALI", "FATURASIZ"])
        self.btnSiparisEkle = QPushButton("➕ Yeni Sipariş")
        self.btnSiparisEkle.setObjectName("PrimaryButton")
        self.btnSiparisEkle.clicked.connect(self.siparis_ekle)
        for w in (self.cmbSiparisTur, self.txtSiparisCari, self.txtSiparisTutar, self.cmbSiparisFatura, self.btnSiparisEkle):
            filtre.addWidget(w)
        layout.addLayout(filtre)

        aksiyon = QHBoxLayout()
        aksiyon.setSpacing(8)
        for text in ("📄 Detay", "Düzenle", "🚚 Teslim Et", "🖨 Yazdır", "Yenile"):
            b = QPushButton(text)
            if "Yenile" in text:
                b.clicked.connect(self.siparis_sayfa_yenile)
            aksiyon.addWidget(b)
        bSil = QPushButton("🗑 İptal / Sil")
        bSil.setObjectName("DangerButton")
        aksiyon.addWidget(bSil)
        aksiyon.addStretch()
        layout.addLayout(aksiyon)

        self.tblSiparis = QTableWidget(0,7)
        self.tblSiparis.setHorizontalHeaderLabels(["No","Tür","Cari / Tedarikçi","Tarih","Durum","Fatura","Toplam"])
        self.tblSiparis.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tblSiparis.verticalHeader().setVisible(False)
        self.tblSiparis.setAlternatingRowColors(True)
        self.tblSiparis.setSelectionBehavior(QTableWidget.SelectRows)
        self.tblSiparis.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tblSiparis.customContextMenuRequested.connect(self.siparis_sag_tik_menu)
        self.tblSiparis.cellDoubleClicked.connect(lambda *_: self.siparis_detay_goster())
        layout.addWidget(self.tblSiparis, 1)

        self.lblSiparisOzet = QLabel("Toplam: 0 kayıt")
        self.lblSiparisOzet.setStyleSheet("background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:8px;font-weight:800;color:#334155;")
        layout.addWidget(self.lblSiparisOzet)
        self.siparis_sayfa_yenile()
        return sayfa

    def siparis_sag_tik_menu(self, pos):
        menu = QMenu(self)
        for text in ("📄 Detayı Aç", "Düzenle", "🚚 Teslim Et", "🖨 Yazdır", "📋 Satırı Kopyala", "Yenile"):
            act = menu.addAction(text)
            if "Detay" in text:
                act.triggered.connect(self.siparis_detay_goster)
            if "Yenile" in text:
                act.triggered.connect(self.siparis_sayfa_yenile)
        menu.exec(self.tblSiparis.viewport().mapToGlobal(pos))

    def siparis_detay_goster(self):
        row = self.tblSiparis.currentRow() if hasattr(self, "tblSiparis") else -1
        if row < 0:
            QMessageBox.information(self, "Sipariş", "Önce bir sipariş seçin.")
            return
        vals = [self.tblSiparis.item(row, c).text() if self.tblSiparis.item(row, c) else "" for c in range(self.tblSiparis.columnCount())]
        QMessageBox.information(self, "Sipariş Detayı", "\n".join([f"{h}: {v}" for h, v in zip(["No","Tür","Cari","Tarih","Durum","Fatura","Toplam"], vals)]))

    def siparis_ekle(self):
        try:
            toplam=float((self.txtSiparisTutar.text() or "0").replace(",","."))
        except Exception:
            QMessageBox.warning(self,"Hata","Tutar geçersiz.")
            return
        cari=self.txtSiparisCari.text().strip() or "Genel"
        no="SP-"+datetime.now().strftime("%Y%m%d%H%M%S")
        with db_baglan() as conn:
            cur=conn.cursor()
            cur.execute("INSERT INTO cariler(ad, aktif) VALUES(?,1)", (cari,))
            cari_id=cur.lastrowid
            cur.execute("INSERT INTO siparisler(siparis_no,tur,cari_id,tarih,toplam,durum) VALUES(?,?,?,?,?,?)",(no,self.cmbSiparisTur.currentText(),cari_id,datetime.now().strftime("%Y-%m-%d"),toplam,"AÇIK"))
        audit_yaz("siparis_eklendi","siparisler",None,{"no":no,"toplam":toplam})
        self.txtSiparisCari.clear()
        self.txtSiparisTutar.clear()
        self.siparis_sayfa_yenile()

    def siparis_sayfa_yenile(self):
        if not hasattr(self,"tblSiparis"):
            return
        with db_baglan() as conn:
            cur=conn.cursor()
            cur.execute("""SELECT s.siparis_no,s.tur,COALESCE(c.ad,''),s.tarih,s.durum,'FATURALI',s.toplam FROM siparisler s LEFT JOIN cariler c ON c.id=s.cari_id WHERE COALESCE(s.aktif,1)=1 ORDER BY s.id DESC LIMIT 200""")
            rows=cur.fetchall()
        self.tblSiparis.setRowCount(0)
        toplam = 0.0
        for r,row in enumerate(rows):
            self.tblSiparis.insertRow(r)
            for c,v in enumerate(row):
                item = QTableWidgetItem(str(v))
                if c == 4:
                    item.setBackground(Qt.GlobalColor.transparent)
                self.tblSiparis.setItem(r,c,item)
            try:
                toplam += float(row[-1] or 0)
            except Exception:
                pass
        if hasattr(self, "lblSiparisOzet"):
            self.lblSiparisOzet.setText(f"Toplam: {len(rows)} kayıt   •   Tutar: {toplam:,.2f} ₺".replace(',', 'X').replace('.', ',').replace('X','.'))

    def satin_alma_sayfasi_olustur(self):
        sayfa, layout = _panel("📥 Satın Alma / Mal Kabul")
        ust=QHBoxLayout()
        self.txtSaTedarikci=QLineEdit()
        self.txtSaTedarikci.setPlaceholderText("Tedarikçi")
        self.txtSaTutar=QLineEdit()
        self.txtSaTutar.setPlaceholderText("Fatura toplamı")
        btn=QPushButton("➕ Alış Faturası Ekle")
        btn.clicked.connect(self.satin_alma_ekle)
        for w in (self.txtSaTedarikci,self.txtSaTutar,btn):
            ust.addWidget(w)
        layout.addLayout(ust)
        self.tblSatinAlma=QTableWidget(0,5)
        self.tblSatinAlma.setHorizontalHeaderLabels(["Belge No","Tedarikçi","Tarih","Durum","Toplam"])
        self.tblSatinAlma.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tblSatinAlma,1)
        self.satin_alma_sayfa_yenile()
        return sayfa

    def satin_alma_ekle(self):
        try:
            toplam=float((self.txtSaTutar.text() or "0").replace(",","."))
        except Exception:
            QMessageBox.warning(self,"Hata","Tutar geçersiz.")
            return
        ted=self.txtSaTedarikci.text().strip() or "Genel Tedarikçi"
        no="SA-"+datetime.now().strftime("%Y%m%d%H%M%S")
        with db_baglan() as conn:
            conn.execute("INSERT INTO satin_alma_faturalari(belge_no,tedarikci_adi,tarih,toplam,durum) VALUES(?,?,?,?,?)",(no,ted,datetime.now().strftime("%Y-%m-%d"),toplam,"AÇIK"))
        audit_yaz("satin_alma_eklendi","satin_alma_faturalari",None,{"no":no,"toplam":toplam})
        self.txtSaTedarikci.clear()
        self.txtSaTutar.clear()
        self.satin_alma_sayfa_yenile()

    def satin_alma_sayfa_yenile(self):
        if not hasattr(self,"tblSatinAlma"):
            return
        with db_baglan() as conn:
            rows=conn.execute("SELECT belge_no,tedarikci_adi,tarih,durum,toplam FROM satin_alma_faturalari WHERE COALESCE(aktif,1)=1 ORDER BY id DESC LIMIT 200").fetchall()
        self.tblSatinAlma.setRowCount(0)
        for r,row in enumerate(rows):
            self.tblSatinAlma.insertRow(r)
            for c,v in enumerate(row):
                self.tblSatinAlma.setItem(r,c,QTableWidgetItem(str(v)))

    def kar_zarar_sayfasi_olustur(self):
        sayfa, layout = _panel("📈 Kâr/Zarar ve Cari Yaşlandırma")
        self.lblKarZarar=QLabel()
        self.lblKarZarar.setStyleSheet("font-size:16px;color:#334155;")
        layout.addWidget(self.lblKarZarar)
        self.tblYaslandirma=QTableWidget(0,2)
        self.tblYaslandirma.setHorizontalHeaderLabels(["Vade Aralığı","Net Bakiye"])
        self.tblYaslandirma.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tblYaslandirma)
        btn=QPushButton("Yenile")
        btn.clicked.connect(self.kar_zarar_sayfa_yenile)
        layout.addWidget(btn)
        self.kar_zarar_sayfa_yenile()
        return sayfa

    def kar_zarar_sayfa_yenile(self):
        o=kar_zarar_ozeti()
        self.lblKarZarar.setText(f"Satış: {o['satis']:.2f} TL | Satın Alma: {o['alis']:.2f} TL | Brüt Kâr/Zarar: {o['brut_kar']:.2f} TL | Kayıtlı Ürün Kârı: {o['kayitli_kar']:.2f} TL")
        b=cari_yaslandirma_ozeti()
        self.tblYaslandirma.setRowCount(0)
        for r,(k,v) in enumerate(b.items()):
            self.tblYaslandirma.insertRow(r)
            self.tblYaslandirma.setItem(r,0,QTableWidgetItem(k+" gün"))
            self.tblYaslandirma.setItem(r,1,QTableWidgetItem(f"{v:.2f} TL"))

    def bildirim_sayfasi_olustur(self):
        sayfa, layout = _panel("🔔 Bildirim Merkezi")
        self.tblBildirim=QTableWidget(0,2)
        self.tblBildirim.setHorizontalHeaderLabels(["Tür","Mesaj"])
        self.tblBildirim.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tblBildirim,1)
        btn=QPushButton("🔄 Bildirimleri Yenile")
        btn.clicked.connect(self.bildirim_sayfa_yenile)
        layout.addWidget(btn)
        self.bildirim_sayfa_yenile()
        return sayfa

    def bildirim_sayfa_yenile(self):
        if not hasattr(self,"tblBildirim"):
            return
        rows=bildirimler()
        self.tblBildirim.setRowCount(0)
        for r,(tur,msg) in enumerate(rows):
            self.tblBildirim.insertRow(r)
            self.tblBildirim.setItem(r,0,QTableWidgetItem(tur))
            self.tblBildirim.setItem(r,1,QTableWidgetItem(msg))

