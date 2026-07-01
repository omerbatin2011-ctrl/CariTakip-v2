import hashlib
import hmac
import os
import secrets
import string

HASH_PREFIX = "pbkdf2_sha256$"
DEFAULT_ITERATIONS = 600_000
PBKDF2_ITERATIONS = DEFAULT_ITERATIONS  # Geriye dönük uyumluluk için korunur.


_GECICI_SIFRE_OZEL_KARAKTERLER = "!@#$%^&*"


def sifre_hashle(sifre, iterations: int = DEFAULT_ITERATIONS) -> str:
    """Şifreyi PBKDF2-SHA256 ile güvenli şekilde hash'ler.

    Not: Eski çağrıları bozmamak için string dışı değerler güvenli biçimde
    metne çevrilir. None değeri ise boş şifre üretmemek için reddedilir.
    """
    if sifre is None:
        raise ValueError("Şifre boş olamaz.")
    sifre = str(sifre)
    iterations = int(iterations or DEFAULT_ITERATIONS)
    if iterations < 100_000:
        iterations = DEFAULT_ITERATIONS

    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", sifre.encode("utf-8"), salt, iterations)
    return f"{HASH_PREFIX}{iterations}${salt.hex()}${dk.hex()}"


def sifre_dogrula(girilen_sifre, kayitli_sifre) -> bool:
    """Girilen şifreyi kayıtlı PBKDF2-SHA256 hash değeriyle doğrular.

    Düz metin şifre karşılaştırması yapılmaz. Bozuk/eski format güvenli şekilde
    False döndürür.
    """
    if girilen_sifre is None or not kayitli_sifre:
        return False

    girilen_sifre = str(girilen_sifre)
    kayitli_sifre = str(kayitli_sifre)

    if not kayitli_sifre.startswith(HASH_PREFIX):
        return False

    try:
        _, iterations, salt_hex, hash_hex = kayitli_sifre.split("$")
        salt = bytes.fromhex(salt_hex)
        beklenen = bytes.fromhex(hash_hex)
        yeni_hash = hashlib.pbkdf2_hmac(
            "sha256",
            girilen_sifre.encode("utf-8"),
            salt,
            int(iterations),
        )
        return hmac.compare_digest(yeni_hash, beklenen)
    except (ValueError, TypeError, OverflowError):
        return False


def kullanici_sifre_hash_mi(sifre) -> bool:
    return str(sifre or "").startswith(HASH_PREFIX)


def gecici_sifre_uret(uzunluk: int = 14) -> str:
    """İlk kurulum için güçlü, kriptografik olarak güvenli geçici şifre üretir."""
    try:
        uzunluk = int(uzunluk or 14)
    except (TypeError, ValueError):
        uzunluk = 14
    if uzunluk < 10:
        uzunluk = 14

    alphabet = string.ascii_letters + string.digits + _GECICI_SIFRE_OZEL_KARAKTERLER
    while True:
        sifre = "".join(secrets.choice(alphabet) for _ in range(uzunluk))
        if (
            any(c.islower() for c in sifre)
            and any(c.isupper() for c in sifre)
            and any(c.isdigit() for c in sifre)
            and any(c in _GECICI_SIFRE_OZEL_KARAKTERLER for c in sifre)
        ):
            return sifre


def guclu_sifre_mi(sifre) -> tuple[bool, str]:
    """Temel şifre politikası: 8+ karakter, harf ve rakam şart.

    Müşteri kullanım kolaylığı için özel karakter zorunlu tutulmaz; geçici
    kurulum şifrelerinde özel karakter zaten otomatik üretilir.
    """
    sifre = str(sifre or "")
    if len(sifre) < 8:
        return False, "Şifre en az 8 karakter olmalı."
    if not any(ch.isalpha() for ch in sifre):
        return False, "Şifre en az 1 harf içermeli."
    if not any(ch.isdigit() for ch in sifre):
        return False, "Şifre en az 1 rakam içermeli."

    zayiflar = {
        "1234", "123456", "12345678", "admin", "admin123",
        "master123", "password", "qwerty", "11111111", "asdfghjk",
        "123456789", "00000000",
    }
    if sifre.lower() in zayiflar:
        return False, "Bu şifre çok kolay tahmin edilir; lütfen daha güçlü bir şifre seçin."
    return True, ""
