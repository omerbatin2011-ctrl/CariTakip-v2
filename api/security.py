from __future__ import annotations

import os
import secrets
import time

from moduller.guvenlik import kullanici_sifre_hash_mi, sifre_dogrula
from moduller.yetki import kullanici_giris_bilgisi_getir, yetki_var_mi

_TOKEN_TTL_SECONDS = int(os.environ.get("DAL_ERP_API_TOKEN_TTL", "43200"))  # 12 saat
_ALLOW_LEGACY_PLAIN_PASSWORD = os.environ.get("DAL_ERP_ALLOW_LEGACY_PLAIN_PASSWORD", "0").strip().lower() in {"1", "true", "evet", "yes", "on"}
_TOKENS: dict[str, dict] = {}


def _cleanup_tokens() -> None:
    now = time.time()
    expired = [token for token, info in _TOKENS.items() if info.get("expires", 0) < now]
    for token in expired:
        _TOKENS.pop(token, None)


def login(kullanici_adi: str, sifre: str) -> dict | None:
    _cleanup_tokens()
    kullanici_adi = (kullanici_adi or "").strip()
    if not kullanici_adi or not sifre:
        return None

    row = kullanici_giris_bilgisi_getir(kullanici_adi)
    if not row:
        return None

    kullanici_id, db_kullanici, kayitli_sifre, rol, aktif = row
    if not int(aktif or 0):
        return None

    # Canlı sürümde düz metin eski şifreler varsayılan olarak kabul edilmez.
    # Geçici uyumluluk gerekiyorsa DAL_ERP_ALLOW_LEGACY_PLAIN_PASSWORD=1 yapılabilir.
    if kullanici_sifre_hash_mi(kayitli_sifre):
        ok = sifre_dogrula(sifre, kayitli_sifre)
    else:
        ok = _ALLOW_LEGACY_PLAIN_PASSWORD and secrets.compare_digest(sifre, kayitli_sifre or "")
    if not ok:
        return None

    token = secrets.token_urlsafe(32)
    expires = time.time() + _TOKEN_TTL_SECONDS
    _TOKENS[token] = {
        "id": kullanici_id,
        "kullanici_adi": db_kullanici,
        "rol": rol,
        "expires": expires,
    }
    return {"token": token, "kullanici_adi": db_kullanici, "rol": rol, "expires_in": _TOKEN_TTL_SECONDS}


def get_user_from_token(token: str) -> dict | None:
    _cleanup_tokens()

    # Sabit admin-token kabulü kaldırıldı. Token yalnızca login() tarafından
    # üretilen süreli oturum tokenı olabilir.
    info = _TOKENS.get(token or "")
    if not info:
        return None
    if info.get("expires", 0) < time.time():
        _TOKENS.pop(token, None)
        return None
    return info


def user_can(user: dict, ekran: str, aksiyon: str = "goruntule") -> bool:
    if not user:
        return False
    if (user.get("rol") or "") == "Yönetici" or (user.get("kullanici_adi") or "").lower() == "admin":
        return True
    try:
        return bool(yetki_var_mi(ekran, aksiyon, user.get("kullanici_adi")))
    except Exception:
        return False
