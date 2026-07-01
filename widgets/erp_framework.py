"""DAL ERP Next v138 - ERP Widget Library + Design System 1.0.

Bu modül yeni ekranlarda kullanılacak ortak UI bileşenlerini tek merkezde toplar.
Amaç, doğrudan Qt widget üretimini azaltıp bütün uygulamada aynı tema, ölçü,
responsive davranış ve yaşam döngüsünü kullanmaktır.
"""

from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTableWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

FRAMEWORK_VERSION = "v138"

try:
    from .design_system import (
        BUTTON_HEIGHT,
        INPUT_HEIGHT,
        KPI_ICON_SIZE,
        KPI_MAX_WIDTH,
        KPI_MIN_HEIGHT,
        KPI_MIN_WIDTH,
        SPACING_LG,
        SPACING_MD,
        TOOL_BUTTON_HEIGHT,
    )
except Exception:
    BUTTON_HEIGHT = 40
    TOOL_BUTTON_HEIGHT = 36
    INPUT_HEIGHT = 40
    KPI_MIN_WIDTH = 205
    KPI_MAX_WIDTH = 260
    KPI_MIN_HEIGHT = 86
    KPI_ICON_SIZE = 38
    SPACING_MD = 12
    SPACING_LG = 16


class ERPPage(QWidget):
    """Tüm yeni modül sayfaları için ortak yaşam döngüsü."""

    pageRefreshed = Signal()

    def __init__(self, title: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.title = title
        self.setObjectName("ERPPage")
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(SPACING_LG, 14, SPACING_LG, 14)
        self.root_layout.setSpacing(12)

    def load_data(self):
        return None

    def refresh(self):
        self.pageRefreshed.emit()

    def apply_theme(self, dark: bool = False):
        return None

    def before_show(self):
        return None

    def before_close(self):
        return True

    def add_title(self, title: str, subtitle: str = "") -> QLabel:
        box = QVBoxLayout()
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(2)
        title_label = QLabel(title)
        title_label.setObjectName("ERPPageTitle")
        box.addWidget(title_label)
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("ERPPageSubtitle")
            box.addWidget(subtitle_label)
        self.root_layout.addLayout(box)
        return title_label


class ERPPanel(QFrame):
    """Standart panel/kart gövdesi."""

    def __init__(self, title: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("ERPPanel")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(SPACING_LG, 14, SPACING_LG, 14)
        self.layout.setSpacing(10)
        if title:
            lbl = QLabel(title)
            lbl.setObjectName("ERPPanelTitle")
            self.layout.addWidget(lbl)

    def add_row(self, *widgets: QWidget, stretch_last: bool = True) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        for i, widget in enumerate(widgets):
            row.addWidget(widget, 1 if stretch_last and i == len(widgets) - 1 else 0)
        self.layout.addLayout(row)
        return row


class ERPCard(ERPPanel):
    """Kart görünümü için panel türevi."""

    def __init__(self, title: str = "", parent: QWidget | None = None):
        super().__init__(title, parent)
        self.setObjectName("ERPCard")


class ERPButton(QPushButton):
    """Standart buton. primary=True ise ana işlem butonu olarak görünür."""

    def __init__(self, text: str, primary: bool = False, danger: bool = False, parent: QWidget | None = None):
        super().__init__(text, parent)
        if danger:
            obj = "ERPDangerButton"
        elif primary:
            obj = "ERPPrimaryButton"
        else:
            obj = "ERPButton"
        self.setObjectName(obj)
        self.setMinimumHeight(BUTTON_HEIGHT)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)


class ERPToolButton(ERPButton):
    """Toolbar içinde kullanılan kompakt buton."""

    def __init__(self, text: str, primary: bool = False, parent: QWidget | None = None):
        super().__init__(text, primary=primary, parent=parent)
        self.setObjectName("ERPToolButtonPrimary" if primary else "ERPToolButton")
        self.setMinimumHeight(TOOL_BUTTON_HEIGHT)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)


class ERPStatCard(QFrame):
    """KPI kartı için ortak bileşen."""

    clicked = Signal()

    def __init__(
        self,
        title: str,
        value: str = "0,00",
        subtitle: str = "",
        icon: str = "•",
        accent: str = "#2563EB",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("ERPStatCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(KPI_MIN_WIDTH, KPI_MIN_HEIGHT)
        self.setMaximumWidth(KPI_MAX_WIDTH)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        row = QHBoxLayout(self)
        row.setContentsMargins(14, 12, 14, 12)
        row.setSpacing(12)

        self.icon_label = QLabel(icon)
        self.icon_label.setObjectName("ERPStatIcon")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(KPI_ICON_SIZE, KPI_ICON_SIZE)
        self.icon_label.setStyleSheet(
            f"background:{accent};color:white;border-radius:11px;font-size:18px;font-weight:900;"
        )

        text_box = QVBoxLayout()
        text_box.setContentsMargins(0, 0, 0, 0)
        text_box.setSpacing(1)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("ERPStatTitle")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("ERPStatValue")
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("ERPStatSubtitle")
        for lbl in (self.title_label, self.value_label, self.subtitle_label):
            lbl.setWordWrap(False)
            lbl.setTextInteractionFlags(Qt.NoTextInteraction)
        text_box.addWidget(self.title_label)
        text_box.addWidget(self.value_label)
        text_box.addWidget(self.subtitle_label)

        row.addWidget(self.icon_label)
        row.addLayout(text_box, 1)
        self._auto_fit_value_font()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def set_value(self, value: str):
        self.value_label.setText(str(value))
        self._auto_fit_value_font()

    def _auto_fit_value_font(self):
        text_len = len(self.value_label.text() or "")
        if text_len > 18:
            size = 14
        elif text_len > 15:
            size = 15
        elif text_len > 12:
            size = 17
        else:
            size = 20
        self.value_label.setStyleSheet(f"font-size:{size}px;font-weight:900;")


class ERPToolbar(QFrame):
    """Sayfa içi işlem çubuğu."""

    def __init__(self, title: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("ERPToolbar")
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(12, 8, 12, 8)
        self.layout.setSpacing(8)
        if title:
            lbl = QLabel(title)
            lbl.setObjectName("ERPToolbarTitle")
            self.layout.addWidget(lbl, 1)
        else:
            self.layout.addStretch(1)

    def add_button(self, text: str, callback=None, primary: bool = False) -> ERPButton:
        btn = ERPToolButton(text, primary=primary)
        if callback:
            btn.clicked.connect(callback)
        self.layout.addWidget(btn)
        return btn

    def add_spacer(self):
        self.layout.addSpacerItem(QSpacerItem(12, 1, QSizePolicy.Expanding, QSizePolicy.Minimum))


class ERPResponsiveGrid(QWidget):
    """Maksimum kart genişliğine göre otomatik kolon hesaplayan grid."""

    def __init__(self, min_card_width: int = 210, max_columns: int = 6, parent: QWidget | None = None):
        super().__init__(parent)
        self.min_card_width = int(min_card_width)
        self.max_columns = int(max_columns)
        self.items: list[QWidget] = []
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(12)

    def set_widgets(self, widgets: Iterable[QWidget]):
        self.items = list(widgets)
        self.reflow()

    def resizeEvent(self, event):
        self.reflow()
        return super().resizeEvent(event)

    def columns_for_width(self, width: int) -> int:
        usable = max(self.min_card_width, int(width or self.width() or 1))
        cols = max(1, usable // self.min_card_width)
        return min(self.max_columns, cols)

    def reflow(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item and item.widget():
                item.widget().setParent(None)
        cols = self.columns_for_width(self.width())
        for i, widget in enumerate(self.items):
            self.grid.addWidget(widget, i // cols, i % cols)
        for c in range(self.max_columns):
            self.grid.setColumnStretch(c, 0)


class ERPTable(QTableWidget):
    """Tüm yeni liste/tablo ekranları için ortak tablo bileşeni."""

    def __init__(self, headers: list[str] | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("ERPTable")
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setWordWrap(False)
        self.setTextElideMode(Qt.ElideRight)
        self.horizontalHeader().setMinimumSectionSize(64)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        if headers:
            self.set_headers(headers)

    def set_headers(self, headers: list[str]):
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

    def stretch_columns(self):
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def fit_last_column(self):
        header = self.horizontalHeader()
        for idx in range(max(0, self.columnCount() - 1)):
            header.setSectionResizeMode(idx, QHeaderView.ResizeToContents)
        if self.columnCount() > 0:
            header.setSectionResizeMode(self.columnCount() - 1, QHeaderView.Stretch)


class ERPSearchBox(QLineEdit):
    """Standart arama kutusu."""

    def __init__(self, placeholder: str = "Ara...", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("ERPSearchBox")
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(BUTTON_HEIGHT)
        self.setClearButtonEnabled(True)


class ERPLineEdit(QLineEdit):
    """Standart tek satır metin girişi."""

    def __init__(self, placeholder: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("ERPLineEdit")
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(BUTTON_HEIGHT)
        self.setClearButtonEnabled(True)


class ERPTextEdit(QTextEdit):
    """Standart çok satırlı metin alanı."""

    def __init__(self, placeholder: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("ERPTextEdit")
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(90)


class ERPComboBox(QComboBox):
    """Standart seçim kutusu."""

    def __init__(self, items: Iterable[str] | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("ERPComboBox")
        self.setMinimumHeight(BUTTON_HEIGHT)
        if items:
            self.addItems(list(items))


class ERPDateEdit(QDateEdit):
    """Standart tarih girişi."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("ERPDateEdit")
        self.setMinimumHeight(BUTTON_HEIGHT)
        self.setCalendarPopup(True)
        self.setDisplayFormat("dd.MM.yyyy")
        self.setDate(QDate.currentDate())


class ERPForm(ERPPanel):
    """Basit form satırları oluşturmak için ortak panel."""

    def __init__(self, title: str = "", parent: QWidget | None = None):
        super().__init__(title, parent)
        self.setObjectName("ERPForm")
        self.form_grid = QGridLayout()
        self.form_grid.setContentsMargins(0, 0, 0, 0)
        self.form_grid.setHorizontalSpacing(10)
        self.form_grid.setVerticalSpacing(8)
        self.layout.addLayout(self.form_grid)
        self._row = 0

    def add_field(self, label: str, widget: QWidget) -> QWidget:
        lbl = QLabel(label)
        lbl.setObjectName("ERPFormLabel")
        self.form_grid.addWidget(lbl, self._row, 0)
        self.form_grid.addWidget(widget, self._row, 1)
        self.form_grid.setColumnStretch(1, 1)
        self._row += 1
        return widget


class ERPDialog(QDialog):
    """Standart dialog iskeleti."""

    def __init__(self, title: str = "DAL ERP", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("ERPDialog")
        self.setWindowTitle(title)
        self.resize(760, 520)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(SPACING_LG, 14, SPACING_LG, 14)
        self.root_layout.setSpacing(12)

    def add_buttons(self, ok_text: str = "Tamam", cancel_text: str = "İptal") -> QDialogButtonBox:
        box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        box.button(QDialogButtonBox.Ok).setText(ok_text)
        box.button(QDialogButtonBox.Cancel).setText(cancel_text)
        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)
        self.root_layout.addWidget(box)
        return box


class ERPStatusBar(QFrame):
    """Uygulama alt durum çubuğu için ortak bileşen."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("ERPStatusBar")
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(12, 4, 12, 4)
        self.layout.setSpacing(12)
        self.labels: dict[str, QLabel] = {}

    def set_item(self, key: str, text: str):
        if key not in self.labels:
            lbl = QLabel(text)
            lbl.setObjectName("ERPStatusItem")
            self.labels[key] = lbl
            self.layout.addWidget(lbl)
        else:
            self.labels[key].setText(text)
