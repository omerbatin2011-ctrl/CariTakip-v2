"""DAL ERP ek ticari/güvenlik altyapısı.

Bu modül mevcut uygulamayı bozmadan profesyonel ERP ihtiyaçları için
migration, audit log, yetki, soft-delete, sipariş, satın alma, bildirim,
kâr/zarar, cari yaşlandırma ve entegrasyon iskeleti sağlar.
"""
from __future__ import annotations

import json
from datetime import date, datetime

from .db import db_baglan


def _kolonlar(cur, tablo):
    cur.execute(f"PRAGMA table_info({tablo})")
    return {r[1] for r in cur.fetchall()}


def _tablo_var_mi(cur, tablo):
    cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (tablo,))
    return cur.fetchone() is not None


def audit_yaz(islem, tablo=None, kayit_id=None, detay=None, kullanici=None):
    try:
        with db_baglan() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tarih TEXT NOT NULL,
                    kullanici TEXT,
                    islem TEXT NOT NULL,
                    tablo TEXT,
                    kayit_id INTEGER,
                    detay TEXT
                )
            """)
            cur.execute("""
                INSERT INTO audit_log(tarih, kullanici, islem, tablo, kayit_id, detay)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), kullanici or "sistem", islem, tablo, kayit_id,
                  json.dumps(detay, ensure_ascii=False) if isinstance(detay, (dict, list)) else detay))
    except Exception:
        pass


def erp_migrasyonlarini_uygula():
    """Tek seferlik/veri kayıpsız migration'ları uygular."""
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kod TEXT NOT NULL UNIQUE,
                aciklama TEXT,
                uygulama_tarihi TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tarih TEXT NOT NULL,
                kullanici TEXT,
                islem TEXT NOT NULL,
                tablo TEXT,
                kayit_id INTEGER,
                detay TEXT
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_tarih ON audit_log(tarih)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_tablo ON audit_log(tablo)")

        for tablo in ("cariler", "urunler", "satislar", "hareketler"):
            if _tablo_var_mi(cur, tablo) and "aktif" not in _kolonlar(cur, tablo):
                cur.execute(f"ALTER TABLE {tablo} ADD COLUMN aktif INTEGER DEFAULT 1")

        # Rol/yetki sistemi
        cur.execute("""
            CREATE TABLE IF NOT EXISTS roller (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rol_adi TEXT NOT NULL UNIQUE,
                aciklama TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS yetkiler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rol_id INTEGER NOT NULL,
                modul TEXT NOT NULL,
                okuma INTEGER DEFAULT 1,
                ekleme INTEGER DEFAULT 0,
                duzenleme INTEGER DEFAULT 0,
                silme INTEGER DEFAULT 0,
                FOREIGN KEY(rol_id) REFERENCES roller(id) ON DELETE CASCADE,
                UNIQUE(rol_id, modul)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS kullanici_rolleri (
                kullanici_id INTEGER NOT NULL,
                rol_id INTEGER NOT NULL,
                PRIMARY KEY(kullanici_id, rol_id)
            )
        """)
        roller = [
            ("Süper Admin", "Tüm modüllerde tam yetki"),
            ("Yönetici", "Operasyonel yönetim"),
            ("Muhasebe", "Cari, kasa, rapor ve tahsilat"),
            ("Satış", "Satış, teklif ve cari görüntüleme"),
            ("Depo", "Stok ve mal kabul"),
            ("Sadece Görüntüleme", "Raporlama ve izleme"),
        ]
        for rol, aciklama in roller:
            cur.execute("INSERT OR IGNORE INTO roller(rol_adi, aciklama) VALUES (?, ?)", (rol, aciklama))
        moduller = ["Cari", "Stok", "Satış", "Sipariş", "Satın Alma", "Kasa", "Tahsilat", "Raporlar", "Ayarlar"]
        cur.execute("SELECT id, rol_adi FROM roller")
        for rol_id, rol_adi in cur.fetchall():
            for modul in moduller:
                full = 1 if rol_adi in ("Süper Admin", "Yönetici") else 0
                okuma = 1
                ekleme = duzenleme = silme = full
                if rol_adi == "Muhasebe" and modul in ("Cari", "Kasa", "Tahsilat", "Raporlar"):
                    ekleme = duzenleme = 1
                    silme = 0
                if rol_adi == "Satış" and modul in ("Cari", "Satış", "Sipariş", "Raporlar"):
                    ekleme = duzenleme = 1
                    silme = 0
                if rol_adi == "Depo" and modul in ("Stok", "Satın Alma", "Sipariş"):
                    ekleme = duzenleme = 1
                    silme = 0
                if rol_adi == "Sadece Görüntüleme":
                    ekleme = duzenleme = silme = 0
                cur.execute("""
                    INSERT OR IGNORE INTO yetkiler(rol_id, modul, okuma, ekleme, duzenleme, silme)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (rol_id, modul, okuma, ekleme, duzenleme, silme))

        # Sipariş modülü
        cur.execute("""
            CREATE TABLE IF NOT EXISTS siparisler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                siparis_no TEXT UNIQUE,
                tur TEXT NOT NULL DEFAULT 'ALINAN',
                cari_id INTEGER,
                tarih TEXT NOT NULL,
                teslim_tarihi TEXT,
                durum TEXT DEFAULT 'AÇIK',
                toplam REAL DEFAULT 0,
                aciklama TEXT,
                aktif INTEGER DEFAULT 1,
                FOREIGN KEY(cari_id) REFERENCES cariler(id) ON DELETE SET NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS siparis_kalemleri (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                siparis_id INTEGER NOT NULL,
                urun_id INTEGER,
                urun_adi TEXT NOT NULL,
                miktar REAL NOT NULL,
                birim_fiyat REAL NOT NULL,
                tutar REAL NOT NULL,
                teslim_edilen REAL DEFAULT 0,
                FOREIGN KEY(siparis_id) REFERENCES siparisler(id) ON DELETE CASCADE,
                FOREIGN KEY(urun_id) REFERENCES urunler(id) ON DELETE SET NULL
            )
        """)

        # Satın alma / mal kabul
        cur.execute("""
            CREATE TABLE IF NOT EXISTS satin_alma_faturalari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                belge_no TEXT UNIQUE,
                tedarikci_id INTEGER,
                tedarikci_adi TEXT,
                tarih TEXT NOT NULL,
                vade_tarihi TEXT,
                toplam REAL DEFAULT 0,
                durum TEXT DEFAULT 'AÇIK',
                aciklama TEXT,
                aktif INTEGER DEFAULT 1,
                FOREIGN KEY(tedarikci_id) REFERENCES cariler(id) ON DELETE SET NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS satin_alma_kalemleri (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fatura_id INTEGER NOT NULL,
                urun_id INTEGER,
                urun_adi TEXT NOT NULL,
                miktar REAL NOT NULL,
                alis_fiyati REAL NOT NULL,
                tutar REAL NOT NULL,
                FOREIGN KEY(fatura_id) REFERENCES satin_alma_faturalari(id) ON DELETE CASCADE,
                FOREIGN KEY(urun_id) REFERENCES urunler(id) ON DELETE SET NULL
            )
        """)

        # Entegrasyon/otomatik güncelleme iskeletleri
        cur.execute("""
            CREATE TABLE IF NOT EXISTS entegrasyon_ayarlari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entegrasyon TEXT NOT NULL UNIQUE,
                aktif INTEGER DEFAULT 0,
                endpoint TEXT,
                kullanici TEXT,
                api_anahtari TEXT,
                son_durum TEXT,
                guncelleme_tarihi TEXT
            )
        """)
        cur.execute("INSERT OR IGNORE INTO entegrasyon_ayarlari(entegrasyon, aktif, son_durum) VALUES ('E-Fatura/E-Arşiv', 0, 'Servis bilgileri bekleniyor')")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS surum_guncellemeleri (
                id INTEGER PRIMARY KEY CHECK(id=1),
                mevcut_surum TEXT,
                kontrol_url TEXT,
                son_kontrol TEXT,
                son_durum TEXT
            )
        """)
        cur.execute("INSERT OR IGNORE INTO surum_guncellemeleri(id, mevcut_surum, son_durum) VALUES (1, 'v75', 'Kurulum tamamlandı')")

        # Cari risk/vade takibi için veri kayıpsız alanlar
        if _tablo_var_mi(cur, "cariler"):
            kolonlar = _kolonlar(cur, "cariler")
            if "risk_limiti" not in kolonlar:
                cur.execute("ALTER TABLE cariler ADD COLUMN risk_limiti REAL DEFAULT 0")
            if "vade_gunu" not in kolonlar:
                cur.execute("ALTER TABLE cariler ADD COLUMN vade_gunu INTEGER DEFAULT 0")
            if "eposta" not in kolonlar:
                cur.execute("ALTER TABLE cariler ADD COLUMN eposta TEXT")
            if "notlar" not in kolonlar:
                cur.execute("ALTER TABLE cariler ADD COLUMN notlar TEXT")
        if _tablo_var_mi(cur, "hareketler") and "vade_tarihi" not in _kolonlar(cur, "hareketler"):
            cur.execute("ALTER TABLE hareketler ADD COLUMN vade_tarihi TEXT")

        # Kritik rapor ve performans indeksleri
        for sql in [
            "CREATE INDEX IF NOT EXISTS idx_cariler_risk ON cariler(risk_limiti)",
            "CREATE INDEX IF NOT EXISTS idx_hareketler_vade ON hareketler(vade_tarihi)",
            "CREATE INDEX IF NOT EXISTS idx_siparisler_durum ON siparisler(durum)",
            "CREATE INDEX IF NOT EXISTS idx_satin_alma_tarih ON satin_alma_faturalari(tarih)",
        ]:
            try:
                cur.execute(sql)
            except Exception:
                pass

        cur.execute("INSERT OR IGNORE INTO schema_migrations(kod, aciklama, uygulama_tarihi) VALUES (?, ?, ?)",
                    ("v106_risk_vade_performans", "Cari risk/vade alanları ve ek indeksler", datetime.now().isoformat(timespec='seconds')))
        cur.execute("INSERT OR IGNORE INTO schema_migrations(kod, aciklama, uygulama_tarihi) VALUES (?, ?, ?)",
                    ("v75_erp_ekleri", "Audit, yetki, soft-delete, sipariş, satın alma, rapor altyapısı", datetime.now().isoformat(timespec='seconds')))


def cari_yaslandirma_ozeti():
    today = date.today()
    buckets = {"0-30": 0.0, "31-60": 0.0, "61-90": 0.0, "90+": 0.0}
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT tarih, tip, tutar FROM hareketler
            WHERE COALESCE(aktif,1)=1
        """)
        for tarih, tip, tutar in cur.fetchall():
            try:
                d = datetime.strptime(str(tarih)[:10], "%Y-%m-%d").date()
            except Exception:
                d = today
            gun = max(0, (today - d).days)
            tutar = float(tutar or 0)
            if str(tip).upper() in ("ALACAK", "TAHSİLAT", "TAHSILAT"):
                tutar = -tutar
            if gun <= 30:
                buckets["0-30"] += tutar
            elif gun <= 60:
                buckets["31-60"] += tutar
            elif gun <= 90:
                buckets["61-90"] += tutar
            else:
                buckets["90+"] += tutar
    return buckets


def kar_zarar_ozeti():
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(SUM(toplam),0) FROM satislar WHERE COALESCE(aktif,1)=1 AND belge_turu!='TEKLİF'")
        satis = float(cur.fetchone()[0] or 0)
        cur.execute("SELECT COALESCE(SUM(toplam),0) FROM satin_alma_faturalari WHERE COALESCE(aktif,1)=1")
        alis = float(cur.fetchone()[0] or 0)
        cur.execute("SELECT COALESCE(SUM(kar_toplam),0) FROM urun_alislari")
        kayitli_kar = float(cur.fetchone()[0] or 0)
    return {"satis": satis, "alis": alis, "brut_kar": satis - alis, "kayitli_kar": kayitli_kar}


def bildirimler():
    sonuc = []
    with db_baglan() as conn:
        cur = conn.cursor()
        if _tablo_var_mi(cur, "urunler"):
            cur.execute("SELECT ad, COALESCE(stok,0) FROM urunler WHERE COALESCE(aktif,1)=1 AND COALESCE(stok,0) <= 5 ORDER BY stok ASC LIMIT 20")
            sonuc += [("Kritik stok", f"{ad}: {stok:g} adet") for ad, stok in cur.fetchall()]
        if _tablo_var_mi(cur, "siparisler"):
            cur.execute("SELECT siparis_no, teslim_tarihi FROM siparisler WHERE COALESCE(aktif,1)=1 AND durum='AÇIK' AND teslim_tarihi IS NOT NULL AND teslim_tarihi <= date('now') LIMIT 20")
            sonuc += [("Geciken sipariş", f"{no or '-'} teslim: {tarih}") for no, tarih in cur.fetchall()]
        cur.execute("SELECT COUNT(*) FROM audit_log WHERE date(tarih)=date('now')")
        sonuc.append(("Audit", f"Bugün {cur.fetchone()[0]} işlem kaydı var"))
    return sonuc

