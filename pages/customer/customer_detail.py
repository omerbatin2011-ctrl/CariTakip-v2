"""Customer detail widget helpers."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy


def make_detail_label(
    text: str = "",
    *,
    object_name: str | None = None,
    alignment: Qt.AlignmentFlag = Qt.AlignLeft | Qt.AlignTop,
    word_wrap: bool = True,
) -> QLabel:
    """Standart cari detay etiketi oluşturur."""

    label = QLabel(text)
    label.setWordWrap(word_wrap)
    label.setAlignment(alignment)
    label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    if object_name:
        label.setObjectName(object_name)

    return label
