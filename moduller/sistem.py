import os
import shutil
import sqlite3
from datetime import datetime

from core.config import (
    BASE_DIR,
    VARSAYILAN_FIRMA,
    VARSAYILAN_KULLANICI,
    VARSAYILAN_MASTER_SIFRE,
    VARSAYILAN_SIFRE,
)

from . import db as db_modulu
from .db import db_baglan
from .guvenlik import gecici_sifre_uret, kullanici_sifre_hash_mi, sifre_dogrula, sifre_hashle
from .loglama import log_yaz


def _ilk_kurulum_bilgisi_yaz(kullanici_sifre=None, master_sifre=None):
    """Güvenlik gereği ilk kurulum/geçici şifreleri dosyaya yazmaz.

    İlk erişim için uygulamadaki "Şifremi Unuttum" akışı ve yetkili reset kodu
    kullanılmalıdır. Böylece şifre kodda, logda veya yerel düz metin dosyada görünmez.
    """
    return None


def ayarlar_tablosu_olustur():
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS firma_ayarlari (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                firma_adi TEXT,
                telefon TEXT,
                adres TEXT,
                vergi_no TEXT,
                vergi_dairesi TEXT,
                eposta TEXT
            )
        """)
        cur.execute("SELECT COUNT(*) FROM firma_ayarlari WHERE id=1")
        var_mi = cur.fetchone()[0]
        if var_mi == 0:
            cur.execute("""
                INSERT INTO firma_ayarlari(id, firma_adi, telefon, adres, vergi_no, vergi_dairesi, eposta)
                VALUES (1, ?, ?, ?, ?, ?, ?)
            """, (
                VARSAYILAN_FIRMA["firma_adi"],
                VARSAYILAN_FIRMA["telefon"],
                VARSAYILAN_FIRMA["adres"],
                VARSAYILAN_FIRMA["vergi_no"],
                VARSAYILAN_FIRMA["vergi_dairesi"],
                VARSAYILAN_FIRMA["eposta"]
            ))


def kullanici_tablosu_olustur():
    # v77: Asıl çok kullanıcılı tablo moduller.yetki içinde migrate edilir.
    try:
        from moduller.yetki import yetki_tablolari_olustur
        yetki_tablolari_olustur()
        return
    except Exception:
        pass
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS kullanicilar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kullanici_adi TEXT NOT NULL UNIQUE,
                sifre TEXT NOT NULL,
                rol TEXT NOT NULL DEFAULT 'Yönetici',
                aktif INTEGER NOT NULL DEFAULT 1
            )
        """)
        cur.execute("SELECT COUNT(*) FROM kullanicilar")
        var_mi = cur.fetchone()[0]
        if var_mi == 0:
            gecici_sifre = VARSAYILAN_SIFRE or gecici_sifre_uret()
            cur.execute(
                "INSERT INTO kullanicilar(kullanici_adi, sifre, rol, aktif) VALUES (?, ?, 'Yönetici', 1)",
                (VARSAYILAN_KULLANICI, sifre_hashle(gecici_sifre))
            )
            if not VARSAYILAN_SIFRE:
                _ilk_kurulum_bilgisi_yaz(kullanici_sifre=gecici_sifre)


def kullanici_bilgisi_getir():
    kullanici_tablosu_olustur()
    try:
        from moduller.yetki import aktif_kullanici_getir
        aktif = aktif_kullanici_getir()
    except Exception:
        aktif = VARSAYILAN_KULLANICI
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("SELECT kullanici_adi, sifre FROM kullanicilar WHERE kullanici_adi=?", (aktif,))
        row = cur.fetchone()
        if not row:
            cur.execute("SELECT kullanici_adi, sifre FROM kullanicilar ORDER BY id LIMIT 1")
            row = cur.fetchone()
    if not row:
        return VARSAYILAN_KULLANICI, ""
    return row[0], row[1]


def kullanici_sifre_guncelle(yeni_sifre):
    kullanici_tablosu_olustur()
    try:
        from moduller.yetki import aktif_kullanici_getir
        aktif = aktif_kullanici_getir()
    except Exception:
        aktif = VARSAYILAN_KULLANICI
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE kullanicilar SET sifre=? WHERE kullanici_adi=?", (sifre_hashle(yeni_sifre), aktif))


def eski_sifreyi_hashle_gerekirse():
    """Eski düz metin kullanıcı şifresini, girişten önce tek seferlik hash'e çevirir."""
    kullanici, kayitli_sifre = kullanici_bilgisi_getir()
    if not kayitli_sifre or kullanici_sifre_hash_mi(kayitli_sifre):
        return
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE kullanicilar SET sifre=? WHERE id=1", (sifre_hashle(kayitli_sifre),))
    log_yaz("Eski düz metin kullanıcı şifresi güvenli hash formatına taşındı.")


def guvenlik_migrasyonunu_uygula():
    """Düz metin kalmış kullanıcı/master şifrelerini uygulama açılışında hash'e taşır."""
    eski_sifreyi_hashle_gerekirse()
    guvenlik_tablosu_olustur()
    try:
        with db_baglan() as conn:
            cur = conn.cursor()
            cur.execute("SELECT master_sifre_hash FROM guvenlik_ayarlari WHERE id=1")
            row = cur.fetchone()
            master = row[0] if row else None
            if master and not kullanici_sifre_hash_mi(master):
                cur.execute("UPDATE guvenlik_ayarlari SET master_sifre_hash=? WHERE id=1", (sifre_hashle(master),))
                log_yaz("Eski düz metin ana şifre güvenli hash formatına taşındı.")
    except Exception as hata:
        log_yaz(f"Güvenlik migrasyonu uygulanamadı: {hata}")


def guvenlik_tablosu_olustur():
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS guvenlik_ayarlari (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                master_sifre_hash TEXT
            )
        """)
        cur.execute("SELECT COUNT(*) FROM guvenlik_ayarlari WHERE id=1")
        var_mi = cur.fetchone()[0]
        if var_mi == 0:
            gecici_master = VARSAYILAN_MASTER_SIFRE or gecici_sifre_uret()
            cur.execute(
                "INSERT INTO guvenlik_ayarlari(id, master_sifre_hash) VALUES (1, ?)",
                (sifre_hashle(gecici_master),)
            )
            if not VARSAYILAN_MASTER_SIFRE:
                _ilk_kurulum_bilgisi_yaz(master_sifre=gecici_master)


def master_sifre_getir():
    guvenlik_tablosu_olustur()
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("SELECT master_sifre_hash FROM guvenlik_ayarlari WHERE id=1")
        row = cur.fetchone()
    if not row or not row[0]:
        master = VARSAYILAN_MASTER_SIFRE or gecici_sifre_uret()
        master_sifre_guncelle(master)
        if not VARSAYILAN_MASTER_SIFRE:
            _ilk_kurulum_bilgisi_yaz(master_sifre=master)
        return master_sifre_getir()
    return row[0]


def master_sifre_dogrula(girilen_sifre):
    return sifre_dogrula(girilen_sifre, master_sifre_getir())


def master_sifre_guncelle(yeni_master_sifre):
    guvenlik_tablosu_olustur()
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE guvenlik_ayarlari SET master_sifre_hash=? WHERE id=1",
            (sifre_hashle(yeni_master_sifre),)
        )


def veritabani_gecerli_mi(dosya_yolu):
    try:
        conn = sqlite3.connect(dosya_yolu)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablolar = {row[0] for row in cur.fetchall()}
        conn.close()
        gerekli = {"cariler", "hareketler", "firma_ayarlari", "kullanicilar"}
        return gerekli.issubset(tablolar)
    except Exception:
        return False


def firma_bilgisi_getir():
    ayarlar_tablosu_olustur()
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT firma_adi, telefon, adres, vergi_no, vergi_dairesi, eposta
            FROM firma_ayarlari
            WHERE id=1
        """)
        row = cur.fetchone()
    if not row:
        return VARSAYILAN_FIRMA.copy()
    return {
        "firma_adi": row[0] or "",
        "telefon": row[1] or "",
        "adres": row[2] or "",
        "vergi_no": row[3] or "",
        "vergi_dairesi": row[4] or "",
        "eposta": row[5] or ""
    }


def guvenlik_ayarlarini_olustur():
    ayarlar_tablosu_olustur()
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(firma_ayarlari)")
        kolonlar = {row[1] for row in cur.fetchall()}
        if "oturum_zaman_asimi" not in kolonlar:
            cur.execute("ALTER TABLE firma_ayarlari ADD COLUMN oturum_zaman_asimi INTEGER DEFAULT 0")


def oturum_zaman_asimi_getir():
    guvenlik_ayarlarini_olustur()
    try:
        with db_baglan() as conn:
            cur = conn.cursor()
            cur.execute("SELECT oturum_zaman_asimi FROM firma_ayarlari WHERE id=1")
            row = cur.fetchone()
        return int(row[0] or 0) if row else 0
    except Exception:
        return 0


def oturum_zaman_asimi_kaydet(dakika):
    guvenlik_ayarlarini_olustur()
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE firma_ayarlari SET oturum_zaman_asimi=? WHERE id=1", (int(dakika or 0),))


def ana_sifreyi_istenen_degere_ayarla():
    """Sadece ortam değişkeni verilirse kurulum/onarım için ana şifreyi ayarlar."""
    yeni = os.environ.get("DAL_ERP_DEFAULT_MASTER_PASSWORD", "").strip()
    if not yeni:
        log_yaz("Ana şifre sıfırlama atlandı: ortam değişkeni verilmedi.")
        return False
    guvenlik_tablosu_olustur()
    master_sifre_guncelle(yeni)
    log_yaz("Ana şifre ortam değişkeniyle güncellendi.")
    return True


def dosya_izinlerini_sikilastir():
    """Yerel dosya izinlerini olabildiğince sıkılaştırır. Windows'ta hata vermez."""
    try:
        db_yolu = db_modulu.DB_ADI
        if db_yolu and os.path.exists(db_yolu):
            os.chmod(db_yolu, 0o600)
        for klasor in ("logs", "yedekler", "TahsilatMakbuzlari", "Proformalar", "pdfler"):
            yol = os.path.join(BASE_DIR, klasor)
            if os.path.isdir(yol):
                try:
                    os.chmod(yol, 0o700)
                except Exception:
                    pass
    except Exception as hata:
        log_yaz(f"Dosya izinleri sıkılaştırılamadı: {hata}")


def otomatik_gunluk_yedek_olustur():
    try:
        db_yolu = db_modulu.DB_ADI
        if not db_yolu or not os.path.exists(db_yolu):
            return None
        os.makedirs(os.path.join(BASE_DIR, "yedekler"), exist_ok=True)
        tarih = datetime.now().strftime("%Y-%m-%d")
        yedek_yolu = os.path.join(BASE_DIR, "yedekler", f"auto_{tarih}.db")
        if not os.path.exists(yedek_yolu):
            shutil.copy2(db_yolu, yedek_yolu)
            log_yaz(f"Otomatik günlük yedek oluşturuldu: {os.path.basename(yedek_yolu)}")
        return yedek_yolu
    except Exception as hata:
        log_yaz(f"Otomatik yedek hatası: {hata}")
        return None
