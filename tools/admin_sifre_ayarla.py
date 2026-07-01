from __future__ import annotations

import getpass
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "cari_takip.db"
sys.path.insert(0, str(BASE_DIR))

from moduller.guvenlik import guclu_sifre_mi, sifre_hashle  # noqa: E402


def ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS kullanicilar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_adi TEXT NOT NULL UNIQUE,
            sifre TEXT NOT NULL,
            rol TEXT NOT NULL DEFAULT 'Yönetici',
            aktif INTEGER NOT NULL DEFAULT 1,
            olusturma_tarih TEXT DEFAULT CURRENT_TIMESTAMP
        )"""
    )


def main() -> int:
    print("DAL ERP - Admin Şifre Ayarla")
    print(f"Veritabanı: {DB_PATH}")
    username = input("Kullanıcı adı [admin]: ").strip() or "admin"
    password = getpass.getpass("Yeni şifre: ")
    password2 = getpass.getpass("Yeni şifre tekrar: ")
    if password != password2:
        print("HATA: Şifreler eşleşmiyor.")
        return 1
    ok, msg = guclu_sifre_mi(password)
    if not ok:
        print(f"HATA: {msg}")
        return 1

    with sqlite3.connect(DB_PATH) as conn:
        ensure_table(conn)
        hashed = sifre_hashle(password)
        row = conn.execute("SELECT id FROM kullanicilar WHERE kullanici_adi=?", (username,)).fetchone()
        if row:
            conn.execute(
                "UPDATE kullanicilar SET sifre=?, rol='Yönetici', aktif=1 WHERE kullanici_adi=?",
                (hashed, username),
            )
        else:
            conn.execute(
                "INSERT INTO kullanicilar (kullanici_adi,sifre,rol,aktif,olusturma_tarih) VALUES (?,?,?,?,?)",
                (username, hashed, "Yönetici", 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
        conn.commit()
    print(f"OK: {username} kullanıcısı aktif ve şifresi güncellendi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
