"""Sales page calculation and parsing helpers."""

from __future__ import annotations


def parse_sayi(text: object) -> float:
    """Turkish formatted money/number text into float."""

    value = str(text or "").strip().replace("₺", "").replace(" ", "")
    if not value:
        return 0.0
    if "," in value:
        value = value.replace(".", "").replace(",", ".")
    return float(value)
