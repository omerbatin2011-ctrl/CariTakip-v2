"""CariTakip V49 çalışma zamanı profil kontrolü.

Bu araç uygulama kodunu değiştirmez; açılışta/import sırasında en pahalı modülleri ölçer.
Rapor: logs/runtime_profile_v49.json
"""

from __future__ import annotations

import importlib
import json
import sys
import time
import tracemalloc
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LOG_DIR = ROOT / "logs"
REPORT_PATH = LOG_DIR / "runtime_profile_v49.json"

MODULES = [
    "core.config",
    "moduller.db",
    "moduller.sql_performance",
    "moduller.loglama",
    "moduller.runtime_health",
    "moduller.stok_ui",
    "moduller.cari_ui",
    "moduller.urun_stok_islemler",
    "moduller.dashboard_logic",
    "core.bootstrap",
]


@dataclass(slots=True)
class ImportMetric:
    module: str
    ok: bool
    elapsed_ms: float
    memory_kb: float
    detail: str = "OK"


def profile_import(module: str) -> ImportMetric:
    tracemalloc.start()
    start = time.perf_counter()
    try:
        importlib.import_module(module)
        ok = True
        detail = "OK"
    except Exception as exc:
        ok = False
        detail = f"{type(exc).__name__}: {exc}"
    elapsed = (time.perf_counter() - start) * 1000
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return ImportMetric(module, ok, round(elapsed, 2), round(peak / 1024, 2), detail)


def main() -> int:
    print("CariTakip V49 runtime/import profil kontrolü")
    LOG_DIR.mkdir(exist_ok=True)
    metrics = [profile_import(module) for module in MODULES]
    total_ms = round(sum(item.elapsed_ms for item in metrics), 2)
    slow = [item for item in metrics if item.elapsed_ms > 500]

    for item in metrics:
        prefix = "[OK]" if item.ok else "[HATA]"
        speed = "YAVAŞ" if item.elapsed_ms > 500 else "normal"
        print(f"{prefix} {item.module}: {item.elapsed_ms} ms, peak={item.memory_kb} KB, {speed}")

    report = {
        "total_import_ms": total_ms,
        "slow_modules": [item.module for item in slow],
        "metrics": [asdict(item) for item in metrics],
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[OK] toplam_import_ms:", total_ms)
    print("[OK] rapor:", REPORT_PATH)
    return 0 if all(item.ok for item in metrics) else 1


if __name__ == "__main__":
    raise SystemExit(main())
