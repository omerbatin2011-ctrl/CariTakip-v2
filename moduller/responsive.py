from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHeaderView, QScrollArea, QSizePolicy, QTableWidget


def responsive_columns(width: int) -> int:
    """Ekran genişliğine göre güvenli kolon sayısı.
    v124: laptop ekranlarda kartların sıkışmaması için daha korumacı kırılımlar.
    """
    try:
        width = int(width or 1366)
    except Exception:
        width = 1366
    if width >= 1650:
        return 6
    if width >= 1280:
        return 4
    if width >= 960:
        return 3
    if width >= 680:
        return 2
    return 1


def page_scroll(widget):
    """Sayfayı taşmalara karşı ScrollArea içine alır."""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setWidget(widget)
    return scroll


def relax_widget(widget):
    """Sabit boyut etkisini azaltır."""
    try:
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    except Exception:
        pass
    return widget


def responsive_table(table: QTableWidget, min_section: int = 90):
    """Tabloları küçük ekranda taşmadan kullanılabilir hale getirir."""
    try:
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        table.setWordWrap(False)
        header = table.horizontalHeader()
        header.setMinimumSectionSize(min_section)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
    except Exception:
        pass
    return table
