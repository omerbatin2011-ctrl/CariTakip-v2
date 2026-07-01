from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from core.config import BASE_DIR

from .loglama import log_yaz

SURUM_DOSYASI = Path(BASE_DIR) / "VERSIYON.txt"
GUNCELLEME_DOSYASI = Path(BASE_DIR) / "guncelleme.json"


def mevcut_surum() -> str:
    try:
        return SURUM_DOSYASI.read_text(encoding="utf-8").strip() or "bilinmiyor"
    except Exception:
        return "bilinmiyor"


def guncelleme_manifestini_oku(path: str | os.PathLike | None = None) -> dict:
    dosya = Path(path) if path else GUNCELLEME_DOSYASI
    if not dosya.exists():
        return {"durum": "manifest_yok", "mevcut_surum": mevcut_surum()}
    try:
        data = json.loads(dosya.read_text(encoding="utf-8"))
        data.setdefault("mevcut_surum", mevcut_surum())
        return data
    except Exception as hata:
        return {"durum": "manifest_hatasi", "hata": str(hata), "mevcut_surum": mevcut_surum()}


def guncelleme_var_mi(path: str | os.PathLike | None = None) -> tuple[bool, dict]:
    data = guncelleme_manifestini_oku(path)
    yeni = str(data.get("son_surum", "")).strip()
    mevcut = mevcut_surum()
    return bool(yeni and yeni != mevcut), data


def klasorden_guncelle(kaynak_klasor: str | os.PathLike) -> str:
    """Offline güncelleme: seçilen klasördeki dosyaları uygulama klasörüne kopyalar."""
    kaynak = Path(kaynak_klasor)
    if not kaynak.exists() or not kaynak.is_dir():
        raise FileNotFoundError("Güncelleme klasörü bulunamadı")
    yedek = Path(BASE_DIR) / "guncelleme_yedekleri" / datetime.now().strftime("%Y%m%d_%H%M%S")
    yedek.mkdir(parents=True, exist_ok=True)
    for item in kaynak.rglob("*"):
        if item.is_file():
            rel = item.relative_to(kaynak)
            hedef = Path(BASE_DIR) / rel
            if hedef.exists():
                (yedek / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(hedef, yedek / rel)
            hedef.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, hedef)
    log_yaz(f"Offline güncelleme uygulandı. Önceki dosyalar: {yedek}", "GUNCELLEME")
    return str(yedek)
