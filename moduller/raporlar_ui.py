from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from moduller.db import db_baglan
from moduller.yardimci import para_yaz


class RaporlarMixin:
    def raporlar_sayfasi_olustur(self):
        sayfa = QFrame()
        sayfa.setStyleSheet("background:#F8FAFC;")
        layout = QVBoxLayout()
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(14)
        ust = QFrame()
        ust.setObjectName("TopBar")
        ust_l = QHBoxLayout()
        ust_l.setContentsMargins(18, 14, 18, 14)
        baslik = QLabel("📊 Raporlar")
        baslik.setStyleSheet("font-size:26px;font-weight:800;color:#0F172A;")
        ust_l.addWidget(baslik)
        ust_l.addStretch()
        btnTarih = QPushButton("📅 Tarih Aralıklı Rapor")
        btnTarih.clicked.connect(self.tarih_aralik_raporu)
        ust_l.addWidget(btnTarih)
        btnExcel = QPushButton("📤 Excel'e Aktar")
        btnExcel.clicked.connect(self.excel_aktar)
        ust_l.addWidget(btnExcel)
        btnYenile = QPushButton("Yenile")
        btnYenile.clicked.connect(self.raporlar_sayfa_yenile)
        ust_l.addWidget(btnYenile)
        ust.setLayout(ust_l)
        layout.addWidget(ust)

        self.lblRaporOzet = QLabel("Rapor özeti yükleniyor...")
        self.lblRaporOzet.setStyleSheet("background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:14px;font-size:16px;font-weight:800;color:#0F172A;")
        layout.addWidget(self.lblRaporOzet)
        kart = QFrame()
        kart.setObjectName("MainCard")
        kart_l = QVBoxLayout()
        kart_l.setContentsMargins(12, 12, 12, 12)
        self.tblRaporSayfa = QTableWidget()
        self.tblRaporSayfa.setColumnCount(5)
        self.tblRaporSayfa.setHorizontalHeaderLabels(["Cari", "Telefon", "Toplam Borç", "Toplam Tahsilat", "Bakiye"])
        self.tblRaporSayfa.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tblRaporSayfa.setSelectionBehavior(QTableWidget.SelectRows)
        self.tblRaporSayfa.setSelectionMode(QTableWidget.SingleSelection)
        self.tblRaporSayfa.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tblRaporSayfa.verticalHeader().setVisible(False)
        self.tblRaporSayfa.setAlternatingRowColors(True)
        kart_l.addWidget(self.tblRaporSayfa, 1)
        kart.setLayout(kart_l)
        layout.addWidget(kart, 1)
        sayfa.setLayout(layout)
        return sayfa

    def raporlar_sayfa_yenile(self):
        if not hasattr(self, "tblRaporSayfa"):
            return
        try:
            with db_baglan() as conn:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM cariler WHERE COALESCE(aktif,1)=1")
                toplam_cari = cur.fetchone()[0] or 0
                cur.execute("SELECT SUM(tutar) FROM hareketler WHERE tip='BORÇ'")
                toplam_borc = float(cur.fetchone()[0] or 0)
                cur.execute("SELECT SUM(tutar) FROM hareketler WHERE tip='TAHSİLAT'")
                toplam_tahsilat = float(cur.fetchone()[0] or 0)
                cur.execute("""
                    SELECT c.ad, c.telefon,
                           COALESCE(SUM(CASE WHEN h.tip='BORÇ' THEN h.tutar ELSE 0 END),0) AS borc,
                           COALESCE(SUM(CASE WHEN h.tip='TAHSİLAT' THEN h.tutar ELSE 0 END),0) AS tahsilat
                    FROM cariler c
                                    LEFT JOIN hareketler h ON h.cari_id=c.id
                    GROUP BY c.id, c.ad, c.telefon
                    ORDER BY c.ad
                """)
                rows = cur.fetchall()
        except Exception as hata:
            QMessageBox.warning(self, "Hata", f"Raporlar yüklenemedi:\n{hata}")
            return
        kalan = toplam_borc - toplam_tahsilat
        self.lblRaporOzet.setText(f"Toplam Cari: {toplam_cari}    |    Toplam Borç: {para_yaz(toplam_borc)}    |    Toplam Tahsilat: {para_yaz(toplam_tahsilat)}    |    Kalan Bakiye: {para_yaz(kalan)}")
        self.tblRaporSayfa.setRowCount(len(rows))
        for r, (ad, tel, borc, tahsilat) in enumerate(rows):
            borc = float(borc or 0)
            tahsilat = float(tahsilat or 0)
            bakiye = borc - tahsilat
            vals = [ad or "", tel or "", para_yaz(borc), para_yaz(tahsilat), para_yaz(bakiye)]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                self.tblRaporSayfa.setItem(r, c, item)

