"""Cari listesi tablo bileşeni.

Bu modül, cari kartları ekranında kullanılan QTableWidget ayarlarını tek
noktadan yönetir. Amaç aynı tablo davranışının farklı ekranlarda tekrar eden
kod yazmadan kullanılmasını sağlamaktır.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView, QTableWidget

CUSTOMER_TABLE_COLUMNS = ("No", "Cari Adı", "Telefon", "Adres", "Bakiye")
DEFAULT_OBJECT_NAME = "CustomerTable"


def create_customer_table(object_name: str = DEFAULT_OBJECT_NAME) -> QTableWidget:
    """Cari listesi için standart tablo bileşeni oluşturur."""
    table = QTableWidget()
    table.setObjectName(object_name)
    table.setColumnCount(len(CUSTOMER_TABLE_COLUMNS))
    table.setHorizontalHeaderLabels(list(CUSTOMER_TABLE_COLUMNS))
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    table.setSelectionBehavior(QTableWidget.SelectRows)
    table.setSelectionMode(QTableWidget.SingleSelection)
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    table.verticalHeader().setVisible(False)
    table.setAlternatingRowColors(True)
    table.setWordWrap(False)
    table.setTextElideMode(Qt.ElideRight)
    return table
