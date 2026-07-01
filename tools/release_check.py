"""CariTakip V46 release kontrol aracı.

Kullanım:
    python tools/release_check.py

Bu araç canlıya çıkmadan önce hızlı ve güvenli kontroller yapar:
- Python dosyaları sözdizimi kontrolü
- Kritik modüllerin import kontrolü
- Gerekli klasörlerin yazılabilirliği
- SQLite bütünlük kontrolü
- Paket bağımlılık kontrolü
- Log boyutu kontrolü
"""

from __future__ import annotations

import ast
import importlib.util
import json
import sqlite3
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SKIP_DIRS = {".git", ".venv", "venv", "build", "dist", "__pycache__", "yedekler", "logs"}
REQUIRED_DIRS = ("logs", "yedekler", "reports")
REQUIRED_PACKAGES = ("PySide6", "cryptography", "matplotlib", "openpyxl", "reportlab")
OPTIONAL_API_PACKAGES = ("fastapi", "uvicorn", "pydantic")
CRITICAL_MODULES = (
    "core.bootstrap",
    "core.config",
    "moduller.db",
    "moduller.sistem",
    "moduller.veritabani_bakim",
    "moduller.runtime_health",
    "moduller.stok_ui",
    "moduller.urun_stok_islemler",
    "moduller.cari_ui",
)


@dataclass(slots=True)
class CheckResult:
    name: str
    ok: bool
    message: str = "OK"


def _print(result: CheckResult) -> None:
    prefix = "[OK]" if result.ok else "[HATA]"
    print(f"{prefix} {result.name}: {result.message}")


def iter_python_files(root: Path):
    for path in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def syntax_check() -> CheckResult:
    errors: list[str] = []
    for path in iter_python_files(ROOT):
        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{path.relative_to(ROOT)} -> {exc}")
    if errors:
        return CheckResult("python_syntax", False, "; ".join(errors[:8]))
    return CheckResult("python_syntax", True, "Tüm Python dosyaları okunabilir")


def dependency_check(include_api: bool = True) -> CheckResult:
    packages = list(REQUIRED_PACKAGES)
    if include_api:
        packages.extend(OPTIONAL_API_PACKAGES)
    missing = [pkg for pkg in packages if importlib.util.find_spec(pkg) is None]
    if missing:
        return CheckResult("dependencies", False, "Eksik paketler: " + ", ".join(missing))
    return CheckResult("dependencies", True, "Zorunlu paketler yüklü")


def import_check() -> CheckResult:
    failed: list[str] = []
    for module in CRITICAL_MODULES:
        try:
            __import__(module)
        except Exception as exc:
            failed.append(f"{module}: {type(exc).__name__}: {exc}")
    if failed:
        return CheckResult("critical_imports", False, " | ".join(failed[:5]))
    return CheckResult("critical_imports", True, "Kritik modüller import edilebilir")


def writable_dirs_check() -> CheckResult:
    failed: list[str] = []
    for name in REQUIRED_DIRS:
        folder = ROOT / name
        try:
            folder.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=folder, delete=False) as tmp:
                tmp.write("ok")
                tmp_path = Path(tmp.name)
            tmp_path.unlink(missing_ok=True)
        except Exception as exc:
            failed.append(f"{name}: {exc}")
    if failed:
        return CheckResult("writable_dirs", False, " | ".join(failed))
    return CheckResult("writable_dirs", True, "Gerekli klasörler yazılabilir")


def sqlite_check() -> CheckResult:
    candidates = [ROOT / "cari_takip.db", ROOT / "data" / "cari_takip.db"]
    db_path = next((path for path in candidates if path.exists()), None)
    if db_path is None:
        return CheckResult("sqlite", True, "DB dosyası henüz yok; ilk açılışta oluşabilir")
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            quick = conn.execute("PRAGMA quick_check").fetchone()
            integrity = conn.execute("PRAGMA integrity_check").fetchone()
        quick_msg = quick[0] if quick else "bilinmiyor"
        integrity_msg = integrity[0] if integrity else "bilinmiyor"
        ok = str(quick_msg).lower() == "ok" and str(integrity_msg).lower() == "ok"
        return CheckResult("sqlite", ok, f"quick={quick_msg}, integrity={integrity_msg}")
    except Exception as exc:
        return CheckResult("sqlite", False, str(exc))



def sqlite_performance_check() -> CheckResult:
    try:
        from core.config import DB_ADI
        from moduller.db import db_ayarla
        from moduller.sql_performance import kritik_sql_indeksleri_olustur, sqlite_optimize

        db_ayarla(DB_ADI)
        db_path = Path(DB_ADI)
        if not db_path.exists():
            return CheckResult("sqlite_perf", True, "DB dosyası ilk açılışta oluşabilir")
        with sqlite3.connect(db_path, timeout=30) as conn:
            once = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'").fetchone()[0]
            hazir = kritik_sql_indeksleri_olustur(conn)
            sqlite_optimize(conn)
            after = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'").fetchone()[0]
        return CheckResult("sqlite_perf", True, f"indeks={once}->{after}, v45_set={hazir}")
    except Exception as exc:
        return CheckResult("sqlite_perf", False, str(exc))

def log_size_check(max_mb: int = 10) -> CheckResult:
    log_dir = ROOT / "logs"
    if not log_dir.exists():
        return CheckResult("logs", True, "Log klasörü yok; uygulama oluşturacak")
    large: list[str] = []
    for path in log_dir.glob("*.txt"):
        mb = path.stat().st_size / (1024 * 1024)
        if mb > max_mb:
            large.append(f"{path.name}: {mb:.1f} MB")
    if large:
        return CheckResult("logs", False, "Büyük log dosyaları: " + ", ".join(large))
    return CheckResult("logs", True, "Log boyutları normal")



def error_logging_check() -> CheckResult:
    try:
        from moduller.loglama import hata_json_yaz, hata_kodu_uret

        log_dir = ROOT / "logs"
        log_dir.mkdir(exist_ok=True)
        kod = hata_kodu_uret()
        hata_json_yaz(kod, "release_check", "TestError", "token=ABC123 sifre=gizli")
        jsonl = log_dir / "hata_log.jsonl"
        if not jsonl.exists() or jsonl.stat().st_size == 0:
            return CheckResult("error_logging", False, "hata_log.jsonl yazılamadı")
        son = jsonl.read_text(encoding="utf-8").splitlines()[-1]
        if "ABC123" in son or "gizli" in son:
            return CheckResult("error_logging", False, "hassas veri maskeleme başarısız")
        return CheckResult("error_logging", True, "JSON hata logu ve maskeleme aktif")
    except Exception as exc:
        return CheckResult("error_logging", False, str(exc))

def main() -> int:
    print("CariTakip V46 release kontrolü")
    print("Klasör:", ROOT)
    results = [
        syntax_check(),
        dependency_check(include_api=True),
        import_check(),
        writable_dirs_check(),
        sqlite_check(),
        sqlite_performance_check(),
        error_logging_check(),
        log_size_check(),
    ]
    for result in results:
        _print(result)

    report_path = ROOT / "logs" / "release_check_v49.json"
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps([asdict(result) for result in results], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print("[OK] rapor:", report_path)
    except Exception as exc:
        print("[UYARI] Rapor yazılamadı:", exc)

    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
