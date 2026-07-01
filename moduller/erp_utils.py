# DAL ERP yardımcı formatlama fonksiyonları
from datetime import datetime

AYLAR_TR = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan",
    5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos",
    9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık",
}

def turkce_tarih_yazi(dt=None):
    dt = dt or datetime.now()
    return f"{dt.day} {AYLAR_TR.get(dt.month, dt.month)} {dt.year}"

def telefon_temizle(telefon):
    """Telefonu her durumda +905467937000 biçimine standardize eder."""
    temiz = "".join(ch for ch in str(telefon or "") if ch.isdigit())
    if temiz.startswith("0090"):
        temiz = temiz[4:]
    elif temiz.startswith("90"):
        temiz = temiz[2:]
    if temiz.startswith("0"):
        temiz = temiz[1:]
    if not temiz:
        return ""
    return "+90" + temiz
