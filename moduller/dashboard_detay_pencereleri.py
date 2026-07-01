from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
)

from moduller.perf_utils import table_set_safely

try:
    from dialogs.erp_dialogs import ERPDialog
except Exception:
    ERPDialog = None


class DashboardDetayMixin:
    def _detay_pencere_olustur(self, baslik, genislik=980, yukseklik=620):
        if ERPDialog is not None:
            dlg = ERPDialog(baslik, "Detaylar ana Dashboard yerine ayrı pencerede gösterilir.", self, genislik, yukseklik)
            return dlg, dlg.root
        dlg = QDialog(self)
        dlg.setWindowTitle(baslik)
        dlg.resize(genislik, yukseklik)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(12)
        ust = QHBoxLayout()
        lbl = QLabel(baslik)
        lbl.setStyleSheet('font-size:22px;font-weight:900;')
        btn = QPushButton('Kapat')
        btn.setMaximumWidth(120)
        btn.clicked.connect(dlg.accept)
        ust.addWidget(lbl, 1)
        ust.addWidget(btn)
        lay.addLayout(ust)
        return dlg, lay

    def dashboard_grafik_penceresi_ac(self):
        dlg, lay = self._detay_pencere_olustur('Grafik Merkezi', 1120, 700)
        try:
            from charts.chart_center import build_chart_center
            lay.addWidget(build_chart_center(self), 1)
        except Exception:
            bilgi = QLabel('Grafik Merkezi yüklenemedi.')
            bilgi.setAlignment(Qt.AlignCenter)
            lay.addWidget(bilgi, 1)
        dlg.exec()


    def _tablo_penceresi_ac(self, baslik, kaynak_attr, kolonlar, genislik=1000, yukseklik=620):
        dlg, lay = self._detay_pencere_olustur(baslik, genislik, yukseklik)
        tbl = QTableWidget()
        tbl.setColumnCount(len(kolonlar))
        tbl.setHorizontalHeaderLabels(kolonlar)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        try:
            kaynak = getattr(self, kaynak_attr, None)
            if kaynak:
                from PySide6.QtWidgets import QTableWidgetItem

                row_count = kaynak.rowCount()
                col_count = min(kaynak.columnCount(), len(kolonlar))

                def _doldur():
                    tbl.setRowCount(row_count)
                    for r in range(row_count):
                        for c in range(col_count):
                            item = kaynak.item(r, c)
                            tbl.setItem(r, c, QTableWidgetItem(item.text() if item else ""))

                table_set_safely(tbl, _doldur)
        except Exception:
            pass
        lay.addWidget(tbl, 1)
        dlg.exec()

    def dashboard_son_islemler_penceresi_ac(self):
        self._tablo_penceresi_ac('Son İşlemler Detayı', 'tblDashboardSonIslemler', ['Tarih', 'İşlem', 'Açıklama', 'Tutar'], 1000, 620)

    def dashboard_son_satislar_penceresi_ac(self):
        self._tablo_penceresi_ac('Son Satışlar', 'tblDashboardSonSatislar', ['Tarih', 'Cari', 'Belge', 'Toplam'], 1000, 620)

    def dashboard_kritik_stok_penceresi_ac(self):
        self._tablo_penceresi_ac('Kritik Stoklar', 'tblDashboardKritikStok', ['Ürün', 'Stok', 'Fiyat'], 900, 600)

    def dashboard_cok_satanlar_penceresi_ac(self):
        self._tablo_penceresi_ac('En Çok Satanlar', 'tblDashboardCokSatan', ['Ürün', 'Adet', 'Toplam'], 900, 600)

    def dashboard_rapor_penceresi_ac(self):
        dlg, lay = self._detay_pencere_olustur('Rapor Merkezi', 1120, 720)
        try:
            from reports.report_center import build_report_center
            lay.addWidget(build_report_center(self), 1)
        except Exception:
            bilgi = QLabel('Rapor Merkezi yüklenemedi.')
            bilgi.setStyleSheet('font-size:14px;font-weight:700;')
            lay.addWidget(bilgi)
        dlg.exec()

    def dashboard_ayarlar_penceresi_ac(self):
        dlg, lay = self._detay_pencere_olustur('Ayarlar Merkezi', 1040, 680)
        try:
            from settings.settings_center import build_settings_center
            lay.addWidget(build_settings_center(self), 1)
        except Exception:
            bilgi = QLabel('Ayarlar Merkezi yüklenemedi.')
            bilgi.setStyleSheet('font-size:14px;font-weight:700;')
            lay.addWidget(bilgi)
        dlg.exec()
