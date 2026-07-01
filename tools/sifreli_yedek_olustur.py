from __future__ import annotations

import base64
import getpass
import os
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "cari_takip.db"
OUT_DIR = BASE_DIR / "yedekler"


def _load_crypto():
    try:
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        return Fernet, PBKDF2HMAC, hashes
    except Exception as exc:
        raise SystemExit(
            "Sifreli yedek icin cryptography paketi gerekli. Kurulum: pip install cryptography\n"
            f"Ayrinti: {exc}"
        )


def _derive_key(password: str, salt: bytes) -> bytes:
    Fernet, PBKDF2HMAC, hashes = _load_crypto()
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390000)
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def create_plain_sqlite_copy(tmp_path: Path) -> None:
    source = sqlite3.connect(DB_PATH)
    target = sqlite3.connect(tmp_path)
    with target:
        source.backup(target)
    source.close()
    target.close()


def encrypted_backup(password: str) -> Path:
    if not DB_PATH.exists():
        raise SystemExit(f"Veritabani bulunamadi: {DB_PATH}")
    if not password or len(password) < 8:
        raise SystemExit("Yedek sifresi en az 8 karakter olmali.")

    Fernet, _, _ = _load_crypto()
    OUT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output = OUT_DIR / f"encrypted_{stamp}.dalbackup"
    salt = os.urandom(16)

    with tempfile.TemporaryDirectory() as td:
        tmp_db = Path(td) / "backup.db"
        create_plain_sqlite_copy(tmp_db)
        data = tmp_db.read_bytes()

    key = _derive_key(password, salt)
    token = Fernet(key).encrypt(data)
    output.write_bytes(b"DALERP-BACKUP-v1\n" + base64.b64encode(salt) + b"\n" + token)
    return output


def main() -> int:
    password = os.environ.get("DAL_ERP_BACKUP_PASSWORD") or getpass.getpass("Yedek sifresi: ")
    out = encrypted_backup(password)
    print(f"Sifreli yedek olusturuldu: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
