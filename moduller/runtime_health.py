"""Açılış öncesi/sonrası hafif sağlık kontrolleri.

Bu modül uygulamayı durdurmak için değil, üretimde sorun çıkarabilecek
klasör/izin/bağımlılık/disk alanı problemlerini erken fark etmek için vardır.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from core.config import BASE_DIR

LogFunc = Callable[[str, str], None]


@dataclass(slots=True)
class SaglikSonucu:
    ad: str
    basarili: bool
    mesaj: str = "OK"


ZORUNLU_KLASORLER = (
    "logs",
    "yedekler",
    "reports",
)

ZORUNLU_BAGIMLILIKLAR = (
    "PySide6",
    "cryptography",
    "matplotlib",
    "openpyxl",
    "reportlab",
)

API_BAGIMLILIKLARI = (
    "fastapi",
    "uvicorn",
    "pydantic",
)


def _logla(log_func: LogFunc | None, sonuc: SaglikSonucu) -> None:
    if not log_func:
        return
    try:
        durum = "OK" if sonuc.basarili else "UYARI"
        log_func(f"Sağlık kontrolü [{sonuc.ad}] {durum}: {sonuc.mesaj}", "SAGLIK")
    except Exception:
        pass


def _yazilabilir_mi(klasor: Path) -> tuple[bool, str]:
    try:
        klasor.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=klasor, delete=False) as tmp:
            tmp.write("ok")
            tmp_yolu = Path(tmp.name)
        tmp_yolu.unlink(missing_ok=True)
        return True, "OK"
    except Exception as exc:
        return False, f"Yazma izni yok: {exc}"


def klasorleri_kontrol_et() -> list[SaglikSonucu]:
    sonuclar: list[SaglikSonucu] = []
    for ad in ZORUNLU_KLASORLER:
        yol = Path(BASE_DIR) / ad
        ok, mesaj = _yazilabilir_mi(yol)
        sonuclar.append(SaglikSonucu(f"klasor:{ad}", ok, mesaj))
    return sonuclar


def disk_alani_kontrol_et(minimum_mb: int = 250) -> SaglikSonucu:
    try:
        kullanim = shutil.disk_usage(BASE_DIR)
        bos_mb = kullanim.free // (1024 * 1024)
        if bos_mb < minimum_mb:
            return SaglikSonucu("disk", False, f"Boş alan düşük: {bos_mb} MB")
        return SaglikSonucu("disk", True, f"Boş alan: {bos_mb} MB")
    except Exception as exc:
        return SaglikSonucu("disk", False, str(exc))


def bagimliliklari_kontrol_et(api_dahil: bool = False) -> list[SaglikSonucu]:
    paketler = list(ZORUNLU_BAGIMLILIKLAR)
    if api_dahil:
        paketler.extend(API_BAGIMLILIKLARI)
    sonuclar: list[SaglikSonucu] = []
    for paket in paketler:
        bulundu = importlib.util.find_spec(paket) is not None
        mesaj = "yüklü" if bulundu else "eksik"
        sonuclar.append(SaglikSonucu(f"bagimlilik:{paket}", bulundu, mesaj))
    return sonuclar


def veritabani_dosyasini_kontrol_et(db_yolu: str | os.PathLike | None) -> SaglikSonucu:
    if not db_yolu:
        return SaglikSonucu("veritabani", False, "DB yolu ayarlanmamış")
    yol = Path(db_yolu)
    if not yol.exists():
        return SaglikSonucu("veritabani", False, "DB dosyası henüz oluşmamış")
    try:
        with sqlite3.connect(yol, timeout=10) as conn:
            sonuc = conn.execute("PRAGMA quick_check").fetchone()
        mesaj = str(sonuc[0] if sonuc else "bilinmiyor")
        return SaglikSonucu("veritabani", mesaj.lower() == "ok", mesaj)
    except Exception as exc:
        return SaglikSonucu("veritabani", False, str(exc))


def saglik_raporu_yaz(sonuclar: list[SaglikSonucu]) -> None:
    """Son sağlık kontrolünü JSON olarak logs klasörüne yazar.

    Bu dosya kullanıcı işlem yaparken hata vermek yerine destek/servis
    sürecinde hızlı teşhis için kullanılır. Yazılamazsa uygulama açılışı
    engellenmez.
    """
    try:
        logs = Path(BASE_DIR) / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        payload = {
            "python": sys.version.split()[0],
            "base_dir": str(BASE_DIR),
            "sonuclar": [asdict(sonuc) for sonuc in sonuclar],
        }
        (logs / "saglik_raporu.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass


def calisma_ortami_saglik_kontrolu(
    log_func: LogFunc | None = None,
    db_yolu: str | os.PathLike | None = None,
    api_dahil: bool = False,
) -> list[SaglikSonucu]:
    """Açılışta hızlı, yan etkisi düşük sağlık kontrollerini çalıştırır."""
    sonuclar: list[SaglikSonucu] = []
    sonuclar.extend(klasorleri_kontrol_et())
    sonuclar.append(disk_alani_kontrol_et())
    sonuclar.extend(bagimliliklari_kontrol_et(api_dahil=api_dahil))
    if db_yolu:
        sonuclar.append(veritabani_dosyasini_kontrol_et(db_yolu))

    for sonuc in sonuclar:
        if not sonuc.basarili or sonuc.ad in {"disk", "veritabani"}:
            _logla(log_func, sonuc)
    saglik_raporu_yaz(sonuclar)
    return sonuclar
