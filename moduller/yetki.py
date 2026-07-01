from __future__ import annotations

from moduller.db import db_baglan
from moduller.guvenlik import gecici_sifre_uret, guclu_sifre_mi, sifre_hashle
from moduller.loglama import log_yaz

AKTIF_KULLANICI = ""

EKRANLAR = [
    ("dashboard", "Ana Ekran"),
    ("cari", "Cari Kartlar"),
    ("satis", "Satışlar"),
    ("barkotlu_satis", "Barkodlu Satış"),
    ("tahsilat", "Tahsilatlar"),
    ("stok", "Stok Yönetimi"),
    ("alis", "Ürün Alışları"),
    ("teklifler", "Teklifler"),
    ("kasa", "Kasa"),
    ("raporlar", "Raporlar"),
    ("kar_zarar", "Kâr/Zarar"),
    ("bildirimler", "Bildirimler"),
    ("siparis", "Sipariş"),
    ("satin_alma", "Satın Alma"),
    ("ayarlar", "Ayarlar"),
    ("yedekleme", "Yedekleme"),
]

# Basit aksiyon seti. Şimdilik menü/görünürlük için 'goruntule' kullanılır.
AKSIYONLAR = ("goruntule", "ekle", "duzenle", "sil")

def aktif_kullanici_ayarla(kullanici_adi: str) -> None:
    global AKTIF_KULLANICI
    AKTIF_KULLANICI = str(kullanici_adi or "")

def aktif_kullanici_getir() -> str:
    return AKTIF_KULLANICI or ""

def _kolon_var_mi(cur, tablo, kolon):
    cur.execute(f"PRAGMA table_info({tablo})")
    return kolon in {r[1] for r in cur.fetchall()}

def yetki_tablolari_olustur() -> None:
    """v77: Çok kullanıcılı yapı ve ekran bazlı yetki tablolarını hazırlar."""
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kullanicilar'")
        if cur.fetchone():
            cur.execute("PRAGMA table_info(kullanicilar)")
            kolonlar = {r[1]: r for r in cur.fetchall()}
            # Eski tabloda id CHECK(id=1) vardı; çok kullanıcı için tabloyu güvenle yeniden kur.
            if not {"aktif", "rol"}.issubset(kolonlar.keys()):
                cur.execute("SELECT id, kullanici_adi, sifre FROM kullanicilar ORDER BY id LIMIT 1")
                eski = cur.fetchone()
                cur.execute("ALTER TABLE kullanicilar RENAME TO kullanicilar_eski_v77")
                cur.execute("""
                    CREATE TABLE kullanicilar (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        kullanici_adi TEXT NOT NULL UNIQUE,
                        sifre TEXT NOT NULL,
                        rol TEXT NOT NULL DEFAULT 'Yönetici',
                        aktif INTEGER NOT NULL DEFAULT 1,
                        olusturma_tarih TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                if eski:
                    cur.execute("INSERT INTO kullanicilar(id,kullanici_adi,sifre,rol,aktif) VALUES (?,?,?,?,1)",
                                (eski[0] or 1, eski[1] or 'admin', eski[2] or '', 'Yönetici'))
                else:
                    cur.execute("INSERT INTO kullanicilar(kullanici_adi,sifre,rol,aktif) VALUES ('admin',?, 'Yönetici',1)", (sifre_hashle(gecici_sifre_uret(24)),))
        else:
            cur.execute("""
                CREATE TABLE kullanicilar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kullanici_adi TEXT NOT NULL UNIQUE,
                    sifre TEXT NOT NULL,
                    rol TEXT NOT NULL DEFAULT 'Yönetici',
                    aktif INTEGER NOT NULL DEFAULT 1,
                    olusturma_tarih TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("INSERT INTO kullanicilar(kullanici_adi,sifre,rol,aktif) VALUES ('admin',?, 'Yönetici',1)", (sifre_hashle(gecici_sifre_uret(24)),))

        cur.execute("""
            CREATE TABLE IF NOT EXISTS kullanici_yetkileri (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kullanici_id INTEGER NOT NULL,
                ekran TEXT NOT NULL,
                goruntule INTEGER NOT NULL DEFAULT 0,
                ekle INTEGER NOT NULL DEFAULT 0,
                duzenle INTEGER NOT NULL DEFAULT 0,
                sil INTEGER NOT NULL DEFAULT 0,
                UNIQUE(kullanici_id, ekran)
            )
        """)
        # Admin/Yönetici için tüm ekranları açık yap.
        cur.execute("SELECT id, kullanici_adi, rol FROM kullanicilar")
        for kid, kadi, rol in cur.fetchall():
            if (kadi or '').lower() == 'admin' or rol == 'Yönetici':
                for ekran, _ in EKRANLAR:
                    cur.execute("""
                        INSERT INTO kullanici_yetkileri(kullanici_id, ekran, goruntule, ekle, duzenle, sil)
                        VALUES (?, ?, 1, 1, 1, 1)
                        ON CONFLICT(kullanici_id, ekran) DO UPDATE SET goruntule=1, ekle=1, duzenle=1, sil=1
                    """, (kid, ekran))

def kullanici_giris_bilgisi_getir(kullanici_adi: str):
    yetki_tablolari_olustur()
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, kullanici_adi, sifre, rol, aktif FROM kullanicilar WHERE kullanici_adi=?", (kullanici_adi,))
        return cur.fetchone()

def kullanicilari_listele():
    yetki_tablolari_olustur()
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, kullanici_adi, rol, aktif FROM kullanicilar ORDER BY kullanici_adi")
        return cur.fetchall()

def kullanici_ekle(kullanici_adi, sifre, rol='Personel', aktif=1):
    yetki_tablolari_olustur()
    kullanici_adi = str(kullanici_adi or '').strip()
    if len(kullanici_adi) < 3:
        raise ValueError('Kullanıcı adı en az 3 karakter olmalı.')
    ok, mesaj = guclu_sifre_mi(sifre)
    if not ok:
        raise ValueError(mesaj)
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO kullanicilar(kullanici_adi,sifre,rol,aktif) VALUES (?,?,?,?)",
                    (kullanici_adi, sifre_hashle(sifre), rol or 'Personel', int(bool(aktif))))
        kid = cur.lastrowid
        # Personel varsayılanı: dashboard + cari görüntüleme açık.
        for ekran, _ in EKRANLAR:
            gor = 1 if ekran in ('dashboard', 'cari') else 0
            cur.execute("INSERT INTO kullanici_yetkileri(kullanici_id, ekran, goruntule, ekle, duzenle, sil) VALUES (?,?,?,?,?,?)",
                        (kid, ekran, gor, 0, 0, 0))
    log_yaz(f"Yeni kullanıcı eklendi: {kullanici_adi}")

def kullanici_guncelle(kullanici_id, rol, aktif, yeni_sifre=None):
    yetki_tablolari_olustur()
    with db_baglan() as conn:
        cur = conn.cursor()
        if yeni_sifre:
            ok, mesaj = guclu_sifre_mi(yeni_sifre)
            if not ok:
                raise ValueError(mesaj)
            cur.execute("UPDATE kullanicilar SET rol=?, aktif=?, sifre=? WHERE id=?", (rol, int(bool(aktif)), sifre_hashle(yeni_sifre), int(kullanici_id)))
        else:
            cur.execute("UPDATE kullanicilar SET rol=?, aktif=? WHERE id=?", (rol, int(bool(aktif)), int(kullanici_id)))

def kullanici_sil(kullanici_id):
    yetki_tablolari_olustur()
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("SELECT kullanici_adi FROM kullanicilar WHERE id=?", (int(kullanici_id),))
        row = cur.fetchone()
        if row and (row[0] or '').lower() == 'admin':
            raise ValueError('Admin kullanıcısı silinemez.')
        cur.execute("DELETE FROM kullanici_yetkileri WHERE kullanici_id=?", (int(kullanici_id),))
        cur.execute("DELETE FROM kullanicilar WHERE id=?", (int(kullanici_id),))

def yetkileri_getir(kullanici_id):
    yetki_tablolari_olustur()
    sonuc = {ekran: {a: 0 for a in AKSIYONLAR} for ekran, _ in EKRANLAR}
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("SELECT ekran, goruntule, ekle, duzenle, sil FROM kullanici_yetkileri WHERE kullanici_id=?", (int(kullanici_id),))
        for ekran, gor, ekle, duz, sil in cur.fetchall():
            sonuc.setdefault(ekran, {})
            sonuc[ekran].update({'goruntule': int(gor or 0), 'ekle': int(ekle or 0), 'duzenle': int(duz or 0), 'sil': int(sil or 0)})
    return sonuc

def yetkileri_kaydet(kullanici_id, yetkiler: dict):
    yetki_tablolari_olustur()
    with db_baglan() as conn:
        cur = conn.cursor()
        for ekran, _ in EKRANLAR:
            y = yetkiler.get(ekran, {})
            cur.execute("""
                INSERT INTO kullanici_yetkileri(kullanici_id, ekran, goruntule, ekle, duzenle, sil)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(kullanici_id, ekran) DO UPDATE SET
                    goruntule=excluded.goruntule, ekle=excluded.ekle, duzenle=excluded.duzenle, sil=excluded.sil
            """, (int(kullanici_id), ekran, int(bool(y.get('goruntule'))), int(bool(y.get('ekle'))), int(bool(y.get('duzenle'))), int(bool(y.get('sil')))))

def kullanici_id_getir(kullanici_adi):
    yetki_tablolari_olustur()
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM kullanicilar WHERE kullanici_adi=?", (kullanici_adi,))
        row = cur.fetchone()
        return row[0] if row else None

def yetki_var_mi(ekran: str, aksiyon: str = 'goruntule', kullanici_adi: str | None = None) -> bool:
    yetki_tablolari_olustur()
    kullanici_adi = kullanici_adi or aktif_kullanici_getir()
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, rol, aktif FROM kullanicilar WHERE kullanici_adi=?", (kullanici_adi,))
        row = cur.fetchone()
        if not row or not int(row[2] or 0):
            return False
        kid, rol, aktif = row
        if rol == 'Yönetici' or (kullanici_adi or '').lower() == 'admin':
            return True
        kolon = aksiyon if aksiyon in AKSIYONLAR else 'goruntule'
        cur.execute(f"SELECT {kolon} FROM kullanici_yetkileri WHERE kullanici_id=? AND ekran=?", (kid, ekran))
        y = cur.fetchone()
        return bool(y and int(y[0] or 0))
