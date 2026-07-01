"""Customer toolbar helpers."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QPushButton

DEFAULT_BUTTON_HEIGHT = 42


def make_customer_button(
    text: str,
    callback: Callable,
    *,
    object_name: str = "CustomerToolButton",
    minimum_height: int = DEFAULT_BUTTON_HEIGHT,
    enabled: bool = True,
) -> QPushButton:
    """Standart müşteri araç çubuğu butonu oluşturur."""

    button = QPushButton(text)
    button.setObjectName(object_name)
    button.setMinimumHeight(minimum_height)
    button.setEnabled(enabled)
    button.clicked.connect(callback)
    return button


def make_primary_customer_button(text: str, callback: Callable) -> QPushButton:
    """Birincil işlem butonu oluşturur."""

    return make_customer_button(
        text,
        callback,
        object_name="CustomerPrimaryButton",
    )


def make_danger_customer_button(text: str, callback: Callable) -> QPushButton:
    """Tehlikeli işlem butonu oluşturur."""

    return make_customer_button(
        text,
        callback,
        object_name="CustomerDangerButton",
    )


def make_success_customer_button(text: str, callback: Callable) -> QPushButton:
    """Başarılı işlem butonu oluşturur."""

    return make_customer_button(
        text,
        callback,
        object_name="CustomerSuccessButton",
    )
