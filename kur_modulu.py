"""TCMB kur ve para birimi yardımcı modülü."""
from __future__ import annotations

import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

TCMB_GUNLUK_XML = "https://www.tcmb.gov.tr/kurlar/today.xml"


def _to_float_tr(value: str) -> float:
    return float(str(value).strip().replace(",", "."))


def tcmb_usd_kuru_al() -> tuple[float, str]:
    """TCMB günlük USD döviz satış kurunu alır.

    Dönüş: (kur, bilgi_metni)
    İnternet yoksa veya TCMB erişilemezse exception yükseltir; program manuel kur girişi yaptırır.
    """
    with urllib.request.urlopen(TCMB_GUNLUK_XML, timeout=10) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)
    tarih = root.attrib.get("Tarih") or root.attrib.get("Date") or datetime.now().strftime("%d.%m.%Y")

    for currency in root.findall("Currency"):
        if currency.attrib.get("CurrencyCode") == "USD":
            forex_selling = currency.findtext("ForexSelling") or currency.findtext("BanknoteSelling")
            if not forex_selling:
                raise RuntimeError("TCMB USD satış kuru bulunamadı.")
            kur = _to_float_tr(forex_selling)
            return kur, f"TCMB günlük USD satış kuru - Tarih: {tarih}"

    raise RuntimeError("TCMB XML içinde USD kuru bulunamadı.")


def tl_karsiligi_hesapla(tutar: float, para_birimi: str = "TL", kur: float = 1) -> float:
    tutar = float(tutar or 0)
    kur = float(kur or 1)
    return tutar if str(para_birimi).upper() == "TL" else tutar * kur
