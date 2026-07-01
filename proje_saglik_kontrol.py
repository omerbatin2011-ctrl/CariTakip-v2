r"""DAL ERP Next proje sağlık kontrolü.

CMD:
  cd /d "C:\Users\technopc\OneDrive\Masaüstü\CariTakip"
  py proje_saglik_kontrol.py

Bu kontrol gerçek kullanıcı işlemi yapmaz; kod, modül importları, veritabanı
kurulum testi ve hata logu gibi temel sağlık göstergelerini raporlar.
"""
from __future__ import annotations

import ast
import importlib
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ok(msg: str) -> None:
    print(f"[OK] {msg}")


def _warn(msg: str) -> None:
    print(f"[UYARI] {msg}")


def _fail(msg: str) -> None:
    print(f"[HATA] {msg}")


def py_syntax_kontrolu(kok: Path) -> list[str]:
    hatalar: list[str] = []
    atla = {".git", "build", "dist", "__pycache__", ".venv", "venv"}
    for py in kok.rglob("*.py"):
        if any(part in atla for part in py.parts):
            continue
        try:
            ast.parse(py.read_text(encoding="utf-8"))
        except Exception as hata:
            hatalar.append(f"{py.relative_to(kok)}: {hata}")
    return hatalar


def import_kontrolu() -> tuple[list[str], list[str]]:
    """Temel mimari modüllerinin import edilebilir olduğunu kontrol eder.

    PySide6 kurulu değilse UI modülleri doğal olarak import edilemez; bu durum
    sağlık kontrolünde uyarı olarak raporlanır. Kullanıcının programı açabildiği
    makinede PySide6 zaten kuruludur.
    """
    moduller = [
        "core.bootstrap",
        "moduller.ana_pencere",
        "moduller.ana_pencere_shell",
        "pages.dashboard.dashboard_page",
        "pages.sales.sales_page",
        "pages.customer.customer_page",
        "widgets.design_system",
        "widgets.theme_styles",
        "widgets.erp_framework",
        "reports.report_center",
        "charts.chart_center",
        "settings.settings_center",
    ]
    hatalar: list[str] = []
    uyarilar: list[str] = []
    for mod in moduller:
        try:
            importlib.import_module(mod)
        except ModuleNotFoundError as hata:
            if "PySide6" in str(hata):
                uyarilar.append(f"{mod}: PySide6 bulunamadığı için UI import testi atlandı")
            else:
                hatalar.append(f"{mod}: {type(hata).__name__}: {hata}")
        except Exception as hata:
            hatalar.append(f"{mod}: {type(hata).__name__}: {hata}")
    return hatalar, uyarilar


def temiz_db_kurulum_testi() -> tuple[bool, str]:
    from moduller.db import (
        db_ayarla,
        db_baglan,
        urun_tablolari_olustur,
        veritabani_indeksleri_olustur,
        veritabani_olustur,
    )
    from moduller.erp_ek_moduller import erp_migrasyonlarini_uygula
    from moduller.lisanslama import lisans_tablosu_olustur
    from moduller.reset_kodu import reset_kodu_tablosu_olustur
    from moduller.sistem import (
        ayarlar_tablosu_olustur,
        guvenlik_ayarlarini_olustur,
        guvenlik_tablosu_olustur,
        kullanici_tablosu_olustur,
    )
    from moduller.veritabani_bakim import (
        guvenli_sqlite_yedekle,
        kritik_indeksleri_olustur,
        veritabani_butunluk_kontrolu,
    )
    from moduller.yetki import yetki_tablolari_olustur

    def kasa_tablosu_olustur() -> None:
        with db_baglan() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS kasa_hareketleri (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tarih TEXT, tip TEXT, odeme_tipi TEXT, tutar REAL,
                    aciklama TEXT, kaynak TEXT, kaynak_id INTEGER, kullanici TEXT
                )
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_kasa_hareketleri_tarih "
                "ON kasa_hareketleri(tarih)"
            )

    with tempfile.TemporaryDirectory() as tmp:
        db_ayarla(str(Path(tmp) / "test.db"))
        veritabani_olustur()
        urun_tablolari_olustur()
        ayarlar_tablosu_olustur()
        kullanici_tablosu_olustur()
        yetki_tablolari_olustur()
        guvenlik_tablosu_olustur()
        guvenlik_ayarlarini_olustur()
        reset_kodu_tablosu_olustur()
        kasa_tablosu_olustur()
        erp_migrasyonlarini_uygula()
        veritabani_indeksleri_olustur()
        kritik_indeksleri_olustur()
        lisans_tablosu_olustur()
        yedek = guvenli_sqlite_yedekle(Path(tmp) / "yedekler", "saglik")
        ok, mesaj = veritabani_butunluk_kontrolu()
        if not yedek:
            return False, "Yedek oluşturulamadı"
        return bool(ok), str(mesaj)


def log_kontrolu() -> None:
    log = ROOT / "logs" / "hata_log.txt"
    if not log.exists() or log.stat().st_size == 0:
        _ok("Hata logu boş")
        return
    text = log.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        _ok("Hata logu boş")
        return
    print("[BILGI] Hata logunda kayıt var. Son 12 satır:")
    for line in text.splitlines()[-12:]:
        print("   ", line)


def main() -> int:
    print("DAL ERP Next v141 sağlık kontrolü başlıyor...")
    print("Klasör:", ROOT)
    hata_sayisi = 0

    syntax = py_syntax_kontrolu(ROOT)
    if syntax:
        hata_sayisi += len(syntax)
        _fail("Python sözdizimi hataları bulundu:")
        for h in syntax:
            print("  -", h)
    else:
        _ok("Python sözdizimi temiz")

    imports, import_warnings = import_kontrolu()
    if import_warnings:
        _warn("Bazı UI import testleri atlandı:")
        for h in import_warnings:
            print("  -", h)
    if imports:
        hata_sayisi += len(imports)
        _fail("Import hataları bulundu:")
        for h in imports:
            print("  -", h)
    else:
        _ok("Temel modül import kontrolü tamamlandı")

    try:
        ok, mesaj = temiz_db_kurulum_testi()
        if ok:
            _ok(f"Temiz DB + yedek testi: {mesaj}")
        else:
            hata_sayisi += 1
            _fail(f"Temiz DB + yedek testi: {mesaj}")
    except Exception as hata:
        hata_sayisi += 1
        _fail(f"Temiz DB kurulum testi hata verdi: {type(hata).__name__}: {hata}")

    log_kontrolu()

    if hata_sayisi:
        _fail(f"Kontrol tamamlandı, {hata_sayisi} sorun var.")
        return 1
    _ok("Kontrol tamamlandı, kritik sorun yok.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
