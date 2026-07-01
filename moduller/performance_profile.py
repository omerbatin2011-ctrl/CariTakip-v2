"""V49 lightweight runtime performance logging helpers."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
PROFILE_PATH = LOG_DIR / "performance_profile.jsonl"


def now_ms() -> float:
    """Return a monotonic millisecond timestamp."""
    return time.perf_counter() * 1000


def log_event(name: str, elapsed_ms: float, **fields: Any) -> None:
    """Append a small JSONL performance event without interrupting the UI."""
    try:
        LOG_DIR.mkdir(exist_ok=True)
        payload = {
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "name": name,
            "elapsed_ms": round(float(elapsed_ms), 2),
            **fields,
        }
        with PROFILE_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
    except Exception:
        # Profil logu üretilemezse uygulamanın akışını asla bozma.
        pass
