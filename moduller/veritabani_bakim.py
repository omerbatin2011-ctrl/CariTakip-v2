from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path

from core.config import BASE_DIR

from . import db as db_modulu
from .db import baglan, db_baglan
from .loglama import log_yaz
from .sql_performance import kritik_sql_indeksleri_olustur, sqlite_optimize


def veritabani_butunluk_kontrolu() -> tuple[bool, str]:
    """SQLite integrity_check sonucunu döndürür."""
    try:
        # baglan() artık context çıkışında kapanır; closing eski sürümlerle de güvenli olsun.
        with closing(baglan()) as conn:
            sonuc = conn.execute("PRAGMA integrity_check").fetchone()
            mesaj = str(sonuc[0] if sonuc else "bilinmiyor")
            return mesaj.lower() == "ok", mesaj
    except Exception as hata:
        return False, str(hata)


def guvenli_sqlite_yedekle(hedef_klasor: str | os.PathLike | None = None, etiket: str = "manual") -> str | None:
    """Çalışan SQLite veritabanını backup API ile tutarlı şekilde yedekler."""
    db_yolu = db_modulu.DB_ADI
    if not db_yolu or not os.path.exists(db_yolu):
        return None
    hedef = Path(hedef_klasor or Path(BASE_DIR) / "yedekler")
    hedef.mkdir(parents=True, exist_ok=True)
    dosya = hedef / f"{etiket}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    kaynak = sqlite3.connect(db_yolu)
    yedek = sqlite3.connect(dosya)
    try:
        kaynak.backup(yedek)
        yedek.commit()
        log_yaz(f"Güvenli SQLite yedeği oluşturuldu: {dosya.name}", "YEDEK")
        return str(dosya)
    finally:
        try:
            yedek.close()
        finally:
            kaynak.close()


def eski_yedekleri_temizle(hedef_klasor: str | os.PathLike | None = None, gun: int = 30) -> int:
    """Belirtilen günden eski otomatik yedekleri siler."""
    hedef = Path(hedef_klasor or Path(BASE_DIR) / "yedekler")
    if not hedef.exists():
        return 0
    sinir = datetime.now() - timedelta(days=int(gun or 30))
    sayi = 0
    for dosya in hedef.glob("auto_*.db"):
        try:
            if datetime.fromtimestamp(dosya.stat().st_mtime) < sinir:
                dosya.unlink()
                sayi += 1
        except Exception:
            pass
    if sayi:
        log_yaz(f"{sayi} eski otomatik yedek temizlendi.", "YEDEK")
    return sayi


def kritik_indeksleri_olustur() -> None:
    """Sık kullanılan ekranlar için ek performans indeksleri."""
    with db_baglan() as conn:
        cur = conn.cursor()
        for sql in [
            "CREATE INDEX IF NOT EXISTS idx_cariler_aktif_tel ON cariler(aktif, telefon)",
            "CREATE INDEX IF NOT EXISTS idx_urunler_aktif_ad ON urunler(aktif, ad)",
            "CREATE INDEX IF NOT EXISTS idx_satislar_aktif_tarih ON satislar(aktif, tarih)",
            "CREATE INDEX IF NOT EXISTS idx_hareketler_cari_tarih ON hareketler(cari_id, tarih)",
            "CREATE INDEX IF NOT EXISTS idx_tahsilat_makbuzlari_tarih ON tahsilat_makbuzlari(tarih)",
            "CREATE INDEX IF NOT EXISTS idx_urun_alislari_tarih ON urun_alislari(tarih)",
        ]:
            try:
                cur.execute(sql)
            except Exception:
                # İlgili tablo henüz yoksa uygulama açılışı kırılmasın.
                pass

        # V45: tablo/kolon varlığını kontrol eden güvenli ek indeks seti.
        try:
            olusan = kritik_sql_indeksleri_olustur(conn)
            sqlite_optimize(conn)
            if olusan:
                log_yaz(f"SQLite performans indeksleri hazır: {olusan}", "DB")
        except Exception as hata:
            log_yaz(f"SQLite indeks optimizasyonu uyarısı: {hata}", "DB")
