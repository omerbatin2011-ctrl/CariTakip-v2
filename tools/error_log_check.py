"""CariTakip V46 hata/log kalite kontrol aracı."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    print("CariTakip V46 hata/log kontrolü")
    from moduller.loglama import hata_json_yaz, hata_kodu_uret, hata_yaz

    log_dir = ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    kod = hata_kodu_uret()
    hata_yaz(f"V46 test log kaydı | token=ABC123 | sifre=gizli | kod={kod}")
    hata_json_yaz(kod, "V46 test", "TestError", "token=ABC123 sifre=gizli")

    txt = log_dir / "islem_logu.txt"
    jsonl = log_dir / "hata_log.jsonl"
    ok_txt = txt.exists() and txt.stat().st_size > 0
    ok_json = jsonl.exists() and jsonl.stat().st_size > 0
    son_json = None
    if ok_json:
        lines = [line for line in jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
        son_json = json.loads(lines[-1])
    mask_ok = son_json is None or "ABC123" not in json.dumps(son_json, ensure_ascii=False)

    checks = [
        ("txt_log", ok_txt, "işlem logu yazılabiliyor"),
        ("json_error_log", ok_json, "JSONL hata logu yazılabiliyor"),
        ("masking", mask_ok, "hassas alanlar maskeleniyor"),
    ]
    for name, ok, msg in checks:
        print(("[OK]" if ok else "[HATA]"), f"{name}: {msg}")
    return 0 if all(ok for _, ok, _ in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
