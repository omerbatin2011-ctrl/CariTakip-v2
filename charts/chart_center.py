from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_MATPLOTLIB_CACHE = None

def _matplotlib_backend():
    """Matplotlib'i Grafik Merkezi açılınca yükler."""
    global _MATPLOTLIB_CACHE
    if _MATPLOTLIB_CACHE is not None:
        return _MATPLOTLIB_CACHE
    try:
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.figure import Figure
        _MATPLOTLIB_CACHE = (True, FigureCanvas, Figure)
    except Exception:
        _MATPLOTLIB_CACHE = (False, None, None)
    return _MATPLOTLIB_CACHE


class ChartCenter(QWidget):
    """v118 Grafik Merkezi: grafikler Dashboard dışında, kullanıcı isteyince yüklenir."""
    def __init__(self, parent_app=None, parent=None):
        super().__init__(parent)
        self.parent_app = parent_app
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        title = QLabel("Grafik türü")
        title.setObjectName("DialogSubtitle")
        self.cmbTur = QComboBox()
        self.cmbTur.addItems(["Satış Grafiği", "Tahsilat Grafiği", "Stok Özeti", "Kasa Özeti"])
        self.cmbAralik = QComboBox()
        self.cmbAralik.addItems(["Son 7 gün", "Son 30 gün", "Bu ay", "Bu yıl"])
        btnYenile = QPushButton("Yenile")
        btnYenile.setObjectName("PrimaryButton")
        btnYenile.clicked.connect(self.grafik_yukle)
        toolbar.addWidget(title)
        toolbar.addWidget(self.cmbTur)
        toolbar.addWidget(self.cmbAralik)
        toolbar.addStretch(1)
        toolbar.addWidget(btnYenile)
        root.addLayout(toolbar)

        self.panel = QFrame()
        self.panel.setObjectName("MainCard")
        panel_l = QVBoxLayout(self.panel)
        panel_l.setContentsMargins(14, 12, 14, 12)
        panel_l.setSpacing(8)
        root.addWidget(self.panel, 1)

        matplotlib_var, FigureCanvas, Figure = _matplotlib_backend()
        if matplotlib_var:
            self.fig = Figure(figsize=(8.5, 4.5), dpi=100)
            self.canvas = FigureCanvas(self.fig)
            panel_l.addWidget(self.canvas, 1)
        else:
            self.fig = None
            self.canvas = None
            self.lblInfo = QLabel("Grafik motoru yüklenemedi. Matplotlib kurulumu kontrol edilmeli.")
            self.lblInfo.setAlignment(Qt.AlignCenter)
            self.lblInfo.setObjectName("DialogSubtitle")
            panel_l.addWidget(self.lblInfo, 1)
        self.grafik_yukle()

    def grafik_yukle(self):
        if self.fig is None or self.canvas is None:
            return
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_title(f"{self.cmbTur.currentText()} - {self.cmbAralik.currentText()}", fontsize=12, fontweight="bold")
        labels = ["1", "5", "10", "15", "20", "25", "30"]
        vals = [0, 0, 0, 0, 0, 0, 0]
        try:
            # Ana uygulamadaki mevcut satış grafik fonksiyonu varsa onu ayrı canvas üzerinde kullan.
            if self.parent_app and hasattr(self.parent_app, "satis_grafik_guncelle") and self.cmbTur.currentText() == "Satış Grafiği":
                eski_fig = getattr(self.parent_app, "figSatis", None)
                eski_canvas = getattr(self.parent_app, "canvasSatis", None)
                self.parent_app.figSatis = self.fig
                self.parent_app.canvasSatis = self.canvas
                self.parent_app.satis_grafik_guncelle()
                self.parent_app.figSatis = eski_fig
                self.parent_app.canvasSatis = eski_canvas
                return
        except Exception:
            pass
        ax.plot(labels, vals, marker="o")
        ax.grid(True, alpha=0.25)
        ax.set_ylabel("Tutar / Adet")
        self.canvas.draw_idle()


def build_chart_center(parent_app=None):
    return ChartCenter(parent_app=parent_app)
