"""DAL ERP genel yapılandırma sabitleri.

Aşama 1 refaktör: dağınık sabitler ve varsayılan değerler tek yerde toplandı.
Mevcut modüller bozulmasın diye eski isimler korunmuştur.
"""
from __future__ import annotations

import os

# Uygulama kök klasörü. EXE'ye çevrildiğinde de sys.argv[0] çalışma dosyasını gösterir.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_ADI = os.path.join(BASE_DIR, "cari_takip.db")

# Uygulama geneli sabitler
OTURUM_KONTROL_MS = 30_000
GIRIS_KILIT_SANIYE = 300
GIRIS_MAKS_DENEME = 3
MAKS_TUTAR = 99_999_999.99
YEDEK_KLASOR_ADI = "Yedekler"

# Güvenlik: kod içinde sabit şifre tutulmaz ve ilk kurulum şifresi ekranda/dosyada gösterilmez.
# İlk erişim için uygulamadaki "Şifremi Unuttum" akışı ve yetkili reset kodu kullanılmalıdır.
VARSAYILAN_KULLANICI = os.environ.get("DAL_ERP_DEFAULT_USER", "admin")
VARSAYILAN_SIFRE = os.environ.get("DAL_ERP_DEFAULT_PASSWORD")
VARSAYILAN_MASTER_SIFRE = os.environ.get("DAL_ERP_DEFAULT_MASTER_PASSWORD")

VARSAYILAN_FIRMA = {
    "firma_adi": "FİRMA ADI",
    "telefon": "Telefon: 05xx xxx xx xx",
    "adres": "Adres: Firma adresi",
    "vergi_no": "Vergi No: -",
    "vergi_dairesi": "Vergi Dairesi: -",
    "eposta": "E-Posta: -",
}

# Lisans / seri numarası ayarları
# 001 seri numarası yetkili reset kodu üretici program içindir.
PROGRAM_SERI_NO = os.environ.get("DAL_ERP_SERIAL", "2026060001")
YETKILI_RESET_SERI_NO = os.environ.get("DAL_ERP_AUTH_SERIAL", "2026060001")
RESET_KODU_GECERLILIK_DAKIKA = int(os.environ.get("DAL_ERP_RESET_CODE_MINUTES", "15"))
