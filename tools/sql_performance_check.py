"""CariTakip SQLite performans kontrolü.

Kullanım:
    python tools/sql_performance_check.py
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.config import DB_ADI  # noqa: E402
from moduller.db import db_ayarla  # noqa: E402
from moduller.sql_performance import kritik_sql_indeksleri_olustur, sqlite_optimize  # noqa: E402


def main() -> int:
    db_ayarla(DB_ADI)
    db_path = Path(DB_ADI)
    if not db_path.exists():
        print("[UYARI] DB dosyası bulunamadı:", db_path)
        return 0

    with sqlite3.connect(db_path, timeout=30) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        once = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'").fetchone()[0]
        hazir = kritik_sql_indeksleri_olustur(conn)
        sqlite_optimize(conn)
        sonra = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'").fetchone()[0]
        quick = conn.execute("PRAGMA quick_check").fetchone()[0]

    print("CariTakip V45 SQL performans kontrolü")
    print("DB:", db_path)
    print(f"[OK] sqlite_quick_check: {quick}")
    print(f"[OK] indeks_sayisi: {once} -> {sonra}")
    print(f"[OK] v45_indeks_seti: {hazir} indeks kontrol edildi")
    return 0 if str(quick).lower() == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
