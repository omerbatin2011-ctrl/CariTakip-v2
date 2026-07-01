"""Ortak doğrulama/çevirme yardımcıları."""
from __future__ import annotations


def tutar_oku(metin, varsayilan=None):
    """Kullanıcıdan gelen para/tutar alanlarını güvenli float değere çevirir."""
    try:
        text = str(metin).strip()
        if "," in text:
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", ".")
        return float(text)
    except (TypeError, ValueError):
        return varsayilan


def telefon_gecerli_mi(telefon):
    """Türkiye formatındaki temizlenmiş telefon değerini doğrular."""
    if not telefon:
        return True
    rakamlar = "".join(ch for ch in str(telefon) if ch.isdigit())
    return len(rakamlar) == 12 and rakamlar.startswith("90")
