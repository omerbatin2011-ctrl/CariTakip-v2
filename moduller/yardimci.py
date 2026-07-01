import base64
import os
import sys
import traceback

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))


def para_yaz(tutar):
    try:
        tutar = float(tutar or 0)
        return f"{tutar:,.2f} ₺".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0,00 ₺"


def logo_html(max_width=190):
    logo_yolu = os.path.join(BASE_DIR, "logo.png")
    if not os.path.exists(logo_yolu):
        return ""
    try:
        with open(logo_yolu, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("ascii")
        return (
            f"<div style='text-align:center;margin-bottom:8px;'>"
            f"<img src='data:image/png;base64,{encoded}' "
            f"style='max-width:{max_width}px; max-height:90px; height:auto;'>"
            f"</div>"
        )
    except Exception:
        return ""


def hata_metni_olustur(exc_type, exc_value, exc_traceback):
    return "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
