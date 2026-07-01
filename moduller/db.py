import sqlite3
from contextlib import contextmanager

DB_ADI = None


class KapananBaglanti(sqlite3.Connection):
    """`with baglan() as conn` kullanımında bağlantıyı gerçekten kapatır.

    sqlite3.Connection normalde context manager çıkışında sadece commit/rollback
    yapar; dosya tanıtıcısını kapatmaz. Windows'ta bu durum geçici test DB
    dosyalarının silinememesine ([WinError 32]) sebep olur.
    """
    def __exit__(self, exc_type, exc, tb):
        try:
            return super().__exit__(exc_type, exc, tb)
        finally:
            self.close()


def db_ayarla(db_yolu):
    global DB_ADI
    DB_ADI = db_yolu


def baglan():
    if not DB_ADI:
        raise RuntimeError("DB_ADI ayarlanmamış")
    # Güvenlik: SQLite bağlantısı her açıldığında koruyucu PRAGMA'lar uygulanır.
    # - foreign_keys: ilişkisel bütünlük
    # - busy_timeout: kilitlenme/yarım işlem riskini azaltır
    # - trusted_schema=OFF: destekleyen SQLite sürümlerinde şema içi zararlı fonksiyon kullanımını kısıtlar
    conn = sqlite3.connect(DB_ADI, timeout=30, isolation_level=None, factory=KapananBaglanti)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA wal_autocheckpoint = 1000")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA temp_store = MEMORY")
    try:
        conn.execute("PRAGMA trusted_schema = OFF")
    except sqlite3.DatabaseError:
        pass
    return conn


@contextmanager
def db_baglan():
    conn = baglan()
    try:
        conn.execute("BEGIN")
        yield conn
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()


def veritabani_olustur():
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cariler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad TEXT NOT NULL,
                telefon TEXT,
                adres TEXT,
                vergi_dairesi TEXT,
                vergi_no TEXT,
                aktif INTEGER DEFAULT 1
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS hareketler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cari_id INTEGER NOT NULL,
                tarih TEXT NOT NULL,
                tip TEXT NOT NULL,
                tutar REAL NOT NULL,
                aciklama TEXT,
                aktif INTEGER DEFAULT 1,
                FOREIGN KEY (cari_id) REFERENCES cariler(id) ON DELETE CASCADE
            )
        """)
        cur.execute("PRAGMA table_info(cariler)")
        cari_kolonlari = {row[1] for row in cur.fetchall()}
        if "vergi_dairesi" not in cari_kolonlari:
            cur.execute("ALTER TABLE cariler ADD COLUMN vergi_dairesi TEXT")
        if "vergi_no" not in cari_kolonlari:
            cur.execute("ALTER TABLE cariler ADD COLUMN vergi_no TEXT")
        if "aktif" not in cari_kolonlari:
            cur.execute("ALTER TABLE cariler ADD COLUMN aktif INTEGER DEFAULT 1")

        cur.execute("PRAGMA table_info(hareketler)")
        hareket_kolonlari = {row[1] for row in cur.fetchall()}
        if "aktif" not in hareket_kolonlari:
            cur.execute("ALTER TABLE hareketler ADD COLUMN aktif INTEGER DEFAULT 1")


def veritabani_indeksleri_olustur():
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("CREATE INDEX IF NOT EXISTS idx_cariler_ad ON cariler(ad)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_cariler_telefon ON cariler(telefon)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_hareketler_cari_id ON hareketler(cari_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_hareketler_tarih ON hareketler(tarih)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_hareketler_tip ON hareketler(tip)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_hareketler_cari_tip ON hareketler(cari_id, tip)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_hareketler_tarih_tip ON hareketler(tarih, tip)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_cariler_aktif_ad ON cariler(aktif, ad)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_cariler_aktif_tel ON cariler(aktif, telefon)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_cariler_aktif_vergi ON cariler(aktif, vergi_no)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_hareketler_aktif_cari_tip ON hareketler(aktif, cari_id, tip)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_hareketler_cari_aktif_tip ON hareketler(cari_id, aktif, tip)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_hareketler_aktif_tarih_tip ON hareketler(aktif, tarih, tip)")
        try:
            cur.execute("ANALYZE")
            cur.execute("PRAGMA optimize")
        except Exception:
            pass


def urun_tablolari_olustur():
    """Ürün grupları, ürün kartları ve satış/proforma kayıtları için tabloları oluşturur."""
    with db_baglan() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS urun_gruplari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad TEXT NOT NULL UNIQUE
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS urunler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grup_id INTEGER NOT NULL,
                ad TEXT NOT NULL,
                varsayilan_fiyat REAL DEFAULT 0,
                stok REAL DEFAULT 0,
                barkod TEXT,
                aktif INTEGER DEFAULT 1,
                FOREIGN KEY (grup_id) REFERENCES urun_gruplari(id) ON DELETE CASCADE
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS satislar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cari_id INTEGER NOT NULL,
                tarih TEXT NOT NULL,
                toplam REAL NOT NULL,
                notlar TEXT,
                hareket_id INTEGER,
                belge_turu TEXT DEFAULT 'SATIŞ',
                FOREIGN KEY (cari_id) REFERENCES cariler(id) ON DELETE CASCADE,
                FOREIGN KEY (hareket_id) REFERENCES hareketler(id) ON DELETE SET NULL
            )
        """)
        cur.execute("PRAGMA table_info(satislar)")
        satis_kolonlari = {row[1] for row in cur.fetchall()}
        if "belge_turu" not in satis_kolonlari:
            cur.execute("ALTER TABLE satislar ADD COLUMN belge_turu TEXT DEFAULT 'SATIŞ'")
        if "teklif_no" not in satis_kolonlari:
            cur.execute("ALTER TABLE satislar ADD COLUMN teklif_no TEXT")
        if "teklif_durumu" not in satis_kolonlari:
            cur.execute("ALTER TABLE satislar ADD COLUMN teklif_durumu TEXT DEFAULT 'BEKLEMEDE'")
        if "teklif_gecerlilik" not in satis_kolonlari:
            cur.execute("ALTER TABLE satislar ADD COLUMN teklif_gecerlilik TEXT")
        if "pdf_yolu" not in satis_kolonlari:
            cur.execute("ALTER TABLE satislar ADD COLUMN pdf_yolu TEXT")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS satis_kalemleri (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                satis_id INTEGER NOT NULL,
                grup_adi TEXT,
                urun_adi TEXT NOT NULL,
                adet REAL NOT NULL,
                birim_fiyat REAL NOT NULL,
                tutar REAL NOT NULL,
                FOREIGN KEY (satis_id) REFERENCES satislar(id) ON DELETE CASCADE
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_urunler_grup_id ON urunler(grup_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_satislar_cari_id ON satislar(cari_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_satislar_tarih ON satislar(tarih)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_satislar_cari_tarih ON satislar(cari_id, tarih)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_satislar_belge_turu ON satislar(belge_turu)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_satislar_teklif_durumu ON satislar(teklif_durumu)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_satis_kalemleri_satis_id ON satis_kalemleri(satis_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_satis_kalemleri_urun_adi ON satis_kalemleri(urun_adi)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_urunler_ad ON urunler(ad)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_cariler_ad ON cariler(ad)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_hareketler_cari_id ON hareketler(cari_id)")

        # Tahsilat makbuzu kayıtları
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tahsilat_makbuzlari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cari_id INTEGER NOT NULL,
                tarih TEXT NOT NULL,
                tutar REAL NOT NULL,
                aciklama TEXT,
                hareket_id INTEGER,
                pdf_yolu TEXT,
                FOREIGN KEY (cari_id) REFERENCES cariler(id) ON DELETE CASCADE,
                FOREIGN KEY (hareket_id) REFERENCES hareketler(id) ON DELETE SET NULL
            )
        """)

        # Ürün alış / tedarikçi giriş kayıtları
        cur.execute("""
            CREATE TABLE IF NOT EXISTS urun_alislari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                urun_id INTEGER NOT NULL,
                urun_adi TEXT NOT NULL,
                tedarikci TEXT NOT NULL,
                tarih TEXT NOT NULL,
                adet REAL NOT NULL,
                alis_fiyati REAL NOT NULL,
                toplam REAL NOT NULL,
                aciklama TEXT,
                FOREIGN KEY (urun_id) REFERENCES urunler(id) ON DELETE CASCADE
            )
        """)

        # Ürün stok alanı yoksa ekle
        cur.execute("PRAGMA table_info(urunler)")
        urun_kolonlari = {row[1] for row in cur.fetchall()}
        if "stok" not in urun_kolonlari:
            cur.execute("ALTER TABLE urunler ADD COLUMN stok REAL DEFAULT 0")
        if "barkod" not in urun_kolonlari:
            cur.execute("ALTER TABLE urunler ADD COLUMN barkod TEXT")
        if "aktif" not in urun_kolonlari:
            cur.execute("ALTER TABLE urunler ADD COLUMN aktif INTEGER DEFAULT 1")

        # Alış kayıtlarında satış fiyatı / kâr karşılaştırma alanları yoksa ekle
        cur.execute("PRAGMA table_info(urun_alislari)")
        alis_kolonlari = {row[1] for row in cur.fetchall()}
        if "satis_fiyati" not in alis_kolonlari:
            cur.execute("ALTER TABLE urun_alislari ADD COLUMN satis_fiyati REAL DEFAULT 0")
        if "kar_birim" not in alis_kolonlari:
            cur.execute("ALTER TABLE urun_alislari ADD COLUMN kar_birim REAL DEFAULT 0")
        if "kar_toplam" not in alis_kolonlari:
            cur.execute("ALTER TABLE urun_alislari ADD COLUMN kar_toplam REAL DEFAULT 0")
        if "para_birimi" not in alis_kolonlari:
            cur.execute("ALTER TABLE urun_alislari ADD COLUMN para_birimi TEXT DEFAULT 'TL'")
        if "kur" not in alis_kolonlari:
            cur.execute("ALTER TABLE urun_alislari ADD COLUMN kur REAL DEFAULT 1")
        if "alis_fiyati_tl" not in alis_kolonlari:
            cur.execute("ALTER TABLE urun_alislari ADD COLUMN alis_fiyati_tl REAL DEFAULT 0")
        if "fatura_durumu" not in alis_kolonlari:
            cur.execute("ALTER TABLE urun_alislari ADD COLUMN fatura_durumu TEXT DEFAULT 'FATURALI'")

        cur.execute("CREATE INDEX IF NOT EXISTS idx_urun_alislari_urun_id ON urun_alislari(urun_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_urun_alislari_urun_id_id ON urun_alislari(urun_id, id DESC)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_urunler_barkod ON urunler(barkod)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_urunler_aktif_ad ON urunler(aktif, ad)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_urunler_aktif_barkod ON urunler(aktif, barkod)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_satislar_aktif_belge_tarih ON satislar(aktif, belge_turu, tarih)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_satislar_aktif_belge_id ON satislar(aktif, belge_turu, id DESC)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_satis_kalemleri_urun_adet ON satis_kalemleri(urun_adi, adet)")
        try:
            cur.execute("ANALYZE")
            cur.execute("PRAGMA optimize")
        except Exception:
            pass


def wal_durumunu_dogrula():
    """SQLite WAL modunun açık olup olmadığını döndürür."""
    with baglan() as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode")
        return (cur.fetchone() or [""])[0]
