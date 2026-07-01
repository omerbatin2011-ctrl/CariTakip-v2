"""CariTakip V49 büyük veri performans testi.

Güvenli çalışma prensibi:
- Gerçek cari_takip.db dosyasına dokunmaz.
- Veritabanını geçici klasöre kopyalar.
- Test kayıtlarını kopya DB üzerinde üretir.
- Sonuçları logs/big_data_performance_v49.json dosyasına yazar.

Örnekler:
    python tools/big_data_performance_test.py --quick
    python tools/big_data_performance_test.py --cariler 100000 --urunler 100000 --hareketler 1000000
"""

from __future__ import annotations

import argparse
import gc
import json
import shutil
import sqlite3
import statistics
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DB = ROOT / "cari_takip.db"
LOG_DIR = ROOT / "logs"
REPORT_PATH = LOG_DIR / "big_data_performance_v49.json"


@dataclass(slots=True)
class Metric:
    name: str
    ok: bool
    elapsed_ms: float
    detail: str


def now_ms() -> float:
    return time.perf_counter() * 1000


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=60)
    conn.execute("PRAGMA journal_mode=MEMORY")
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA cache_size=-64000")
    return conn


def measure(name: str, fn, warn_ms: float) -> Metric:
    start = now_ms()
    try:
        detail = str(fn())
        elapsed = now_ms() - start
        return Metric(name, elapsed <= warn_ms, round(elapsed, 2), detail)
    except Exception as exc:
        elapsed = now_ms() - start
        return Metric(name, False, round(elapsed, 2), f"{type(exc).__name__}: {exc}")


def prepare_db() -> tuple[tempfile.TemporaryDirectory, Path]:
    if not SOURCE_DB.exists():
        raise FileNotFoundError(f"DB bulunamadı: {SOURCE_DB}")
    tmp = tempfile.TemporaryDirectory(prefix="caritakip_v49_perf_")
    dst = Path(tmp.name) / "cari_takip_perf.db"
    shutil.copy2(SOURCE_DB, dst)
    return tmp, dst


def seed_data(conn: sqlite3.Connection, cariler: int, urunler: int, hareketler: int) -> list[Metric]:
    metrics: list[Metric] = []

    def seed_cariler() -> str:
        conn.executemany(
            """
            INSERT INTO cariler(ad, telefon, adres, aktif, bakiye)
            VALUES (?, ?, ?, 1, ?)
            """,
            (
                (f"PERF Cari {i:06d}", f"05{i % 1000000000:09d}", "Performans test adresi", float(i % 25000))
                for i in range(cariler)
            ),
        )
        conn.commit()
        return f"{cariler} cari eklendi"

    def seed_urunler() -> str:
        conn.execute("INSERT OR IGNORE INTO urun_gruplari(ad) VALUES ('PERF TEST')")
        grup_id = conn.execute("SELECT id FROM urun_gruplari WHERE ad='PERF TEST'").fetchone()[0]
        conn.executemany(
            """
            INSERT INTO urunler(grup_id, ad, varsayilan_fiyat, stok, barkod, aktif, fiyat, grup)
            VALUES (?, ?, ?, ?, ?, 1, ?, 'PERF TEST')
            """,
            (
                (
                    grup_id,
                    f"PERF Ürün {i:06d}",
                    float((i % 5000) + 1),
                    float(i % 1000),
                    f"869PERF{i:09d}",
                    float((i % 5000) + 1),
                )
                for i in range(urunler)
            ),
        )
        conn.commit()
        return f"{urunler} ürün eklendi"

    def seed_hareketler() -> str:
        max_cari_id = conn.execute("SELECT COALESCE(MAX(id), 1) FROM cariler").fetchone()[0]
        min_cari_id = max(1, max_cari_id - max(cariler, 1) + 1)
        cari_range = max(1, max_cari_id - min_cari_id + 1)
        conn.executemany(
            """
            INSERT INTO hareketler(cari_id, tip, tutar, aciklama, tarih, aktif, vade_tarihi)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            """,
            (
                (
                    min_cari_id + (i % cari_range),
                    "BORÇ" if i % 2 == 0 else "ALACAK",
                    float((i % 10000) + 1),
                    "PERF hareket",
                    f"2026-06-{(i % 28) + 1:02d}",
                    f"2026-07-{(i % 28) + 1:02d}",
                )
                for i in range(hareketler)
            ),
        )
        conn.commit()
        return f"{hareketler} hareket eklendi"

    metrics.append(measure("seed_cariler", seed_cariler, max(3000, cariler * 0.2)))
    metrics.append(measure("seed_urunler", seed_urunler, max(3000, urunler * 0.2)))
    metrics.append(measure("seed_hareketler", seed_hareketler, max(5000, hareketler * 0.05)))
    return metrics


def query_tests(conn: sqlite3.Connection) -> list[Metric]:
    tests = [
        (
            "cari_arama_like",
            lambda: conn.execute(
                "SELECT id, ad, telefon, bakiye FROM cariler WHERE aktif=1 AND ad LIKE ? ORDER BY ad LIMIT 50",
                ("PERF Cari 09%",),
            ).fetchall(),
            250,
        ),
        (
            "urun_arama_like",
            lambda: conn.execute(
                "SELECT id, ad, stok, fiyat FROM urunler WHERE aktif=1 AND ad LIKE ? ORDER BY ad LIMIT 50",
                ("PERF Ürün 09%",),
            ).fetchall(),
            250,
        ),
        (
            "hareket_cari_ozet",
            lambda: conn.execute(
                """
                SELECT cari_id,
                       SUM(CASE WHEN tip='BORÇ' THEN tutar ELSE 0 END) borc,
                       SUM(CASE WHEN tip='ALACAK' THEN tutar ELSE 0 END) alacak
                FROM hareketler
                WHERE aktif=1 AND cari_id IN (SELECT id FROM cariler WHERE ad LIKE 'PERF Cari 00%' LIMIT 500)
                GROUP BY cari_id
                LIMIT 500
                """
            ).fetchall(),
            750,
        ),
        (
            "dashboard_toplamlar",
            lambda: conn.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM cariler WHERE aktif=1) AS cari_sayisi,
                    (SELECT COUNT(*) FROM urunler WHERE aktif=1) AS urun_sayisi,
                    (SELECT COALESCE(SUM(tutar), 0) FROM hareketler WHERE aktif=1 AND tip='BORÇ') AS toplam_borc,
                    (SELECT COALESCE(SUM(tutar), 0) FROM hareketler WHERE aktif=1 AND tip='ALACAK') AS toplam_alacak
                """
            ).fetchone(),
            1000,
        ),
    ]
    metrics = []
    for name, fn, warn_ms in tests:
        elapsed_values = []
        last_len = 0
        for _ in range(3):
            start = now_ms()
            rows = fn()
            elapsed_values.append(now_ms() - start)
            try:
                last_len = len(rows)
            except TypeError:
                last_len = 1
        avg = statistics.mean(elapsed_values)
        metrics.append(Metric(name, avg <= warn_ms, round(avg, 2), f"ortalama=3 tekrar, satır={last_len}"))
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser(description="CariTakip büyük veri performans testi")
    parser.add_argument("--quick", action="store_true", help="Hızlı test: 1.000 cari, 1.000 ürün, 5.000 hareket")
    parser.add_argument("--cariler", type=int, default=10000)
    parser.add_argument("--urunler", type=int, default=10000)
    parser.add_argument("--hareketler", type=int, default=50000)
    args = parser.parse_args()

    if args.quick:
        args.cariler, args.urunler, args.hareketler = 1000, 1000, 5000

    print("CariTakip V49 büyük veri performans testi")
    print("Gerçek DB değişmez; test kopya DB üzerinde yapılır.")
    print(f"Hedef: cariler={args.cariler}, urunler={args.urunler}, hareketler={args.hareketler}")

    LOG_DIR.mkdir(exist_ok=True)
    tmp, test_db = prepare_db()
    try:
        with connect(test_db) as conn:
            metrics = []
            metrics.extend(seed_data(conn, args.cariler, args.urunler, args.hareketler))
            conn.execute("ANALYZE")
            conn.commit()
            metrics.extend(query_tests(conn))
            db_size_mb = test_db.stat().st_size / (1024 * 1024)

        report = {
            "db_copy": str(test_db),
            "db_size_mb": round(db_size_mb, 2),
            "settings": vars(args),
            "metrics": [asdict(item) for item in metrics],
        }
        REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        for item in metrics:
            prefix = "[OK]" if item.ok else "[UYARI]"
            print(f"{prefix} {item.name}: {item.elapsed_ms} ms - {item.detail}")
        print("[OK] rapor:", REPORT_PATH)
        return 0 if all(item.ok for item in metrics) else 1
    finally:
        gc.collect()
        time.sleep(0.25)
        try:
            tmp.cleanup()
        except PermissionError as exc:
            gc.collect()
            time.sleep(1.0)
            try:
                tmp.cleanup()
            except PermissionError:
                print(f"UYARI: Temp klasor silinemedi: {exc}")
                print(f"UYARI: Elle silinebilir: {tmp.name}")


if __name__ == "__main__":
    raise SystemExit(main())
