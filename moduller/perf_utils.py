"""Performans yardımcıları - V149 Mega Performans Paketi."""
from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem


def debounce(owner, attr_name: str, callback: Callable[[], None], delay_ms: int = 260) -> Callable[[], None]:
    """Sık tetiklenen arama/filtre sinyallerini tek yenilemeye indirir."""
    timer = getattr(owner, attr_name, None)
    if timer is None:
        timer = QTimer(owner)
        timer.setSingleShot(True)
        setattr(owner, attr_name, timer)
    old_callback_attr = f"{attr_name}_callback"
    old_callback = getattr(owner, old_callback_attr, None)
    if old_callback is not None:
        try:
            timer.timeout.disconnect(old_callback)
        except (RuntimeError, TypeError):
            pass
    timer.timeout.connect(callback)
    setattr(owner, old_callback_attr, callback)

    def trigger(*_args, **_kwargs):
        timer.start(delay_ms)
    return trigger


class TTLCache:
    """Küçük ve güvenli zaman bazlı bellek cache'i.

    Ağır sorgular ve tekrar eden özet hesaplamaları için kullanılır.
    Varsayılan TTL kısa tutulur; veri değiştiğinde clear() çağrılabilir.
    """

    def __init__(self, ttl_seconds: float = 10.0, max_items: int = 128):
        import time

        self.ttl_seconds = float(ttl_seconds)
        self.max_items = int(max_items)
        self._time = time.monotonic
        self._data: dict[object, tuple[float, object]] = {}

    def get(self, key, factory: Callable[[], object]):
        now = self._time()
        item = self._data.get(key)
        if item is not None:
            expires_at, value = item
            if expires_at >= now:
                return value
            self._data.pop(key, None)
        value = factory()
        if len(self._data) >= self.max_items:
            # Basit FIFO temizliği yeterli; cache küçük tutuluyor.
            try:
                self._data.pop(next(iter(self._data)))
            except StopIteration:
                pass
        self._data[key] = (now + self.ttl_seconds, value)
        return value

    def clear(self) -> None:
        self._data.clear()


def table_set_safely(table: QTableWidget, callback: Callable[[], None]) -> None:
    """Tablo işlemlerinde repaint/sort maliyetini güvenli şekilde kapatır."""
    sorting = table.isSortingEnabled()
    table.setUpdatesEnabled(False)
    try:
        table.setSortingEnabled(False)
        callback()
    finally:
        table.setSortingEnabled(sorting)
        table.setUpdatesEnabled(True)
        try:
            table.viewport().update()
        except Exception:
            pass


def fill_table_fast(
    table: QTableWidget,
    rows: Iterable[Sequence],
    *,
    id_column: int | None = None,
    id_role: int = 1000,
    formatter: Callable[[int, int, object], object] | None = None,
    block_signals: bool = True,
) -> None:
    """QTableWidget doldururken repaint/sinyal/sort maliyetini azaltır."""
    rows = list(rows)
    sorting = table.isSortingEnabled()
    signals_blocked = False

    table.setUpdatesEnabled(False)
    if block_signals:
        signals_blocked = table.blockSignals(True)

    try:
        table.setSortingEnabled(False)
        table.clearSelection()
        table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            hidden_id = row[id_column] if id_column is not None and id_column < len(row) else None
            for c, value in enumerate(row):
                if id_column is not None and c == id_column:
                    continue
                shown_col = c if id_column is None or c < id_column else c - 1
                val = formatter(r, c, value) if formatter else value
                item = QTableWidgetItem(str(val if val is not None else ""))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if hidden_id is not None and shown_col == 0:
                    try:
                        item.setData(id_role, int(hidden_id))
                    except Exception:
                        item.setData(id_role, hidden_id)
                table.setItem(r, shown_col, item)
    finally:
        table.setSortingEnabled(sorting)
        if block_signals:
            table.blockSignals(signals_blocked)
        table.setUpdatesEnabled(True)
        try:
            table.viewport().update()
        except Exception:
            pass
