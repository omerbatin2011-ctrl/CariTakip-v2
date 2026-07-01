import os
import re
import secrets
import socket
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from api.security import get_user_from_token
from api.security import login as login_from_db

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "cari_takip.db"
ENV_PATH = BASE_DIR / ".env"

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _sql_identifier(name: str) -> str:
    """Sadece uygulama içinden gelen tablo/kolon adlarını SQL'e güvenli sokar."""
    if not isinstance(name, str) or not _IDENTIFIER_RE.match(name):
        raise ValueError(f"Geçersiz SQL tanımlayıcı: {name!r}")
    return name


def _limit_value(value: int, default: int = 100, maximum: int = 500) -> int:
    """Mobil API liste limitlerini makul aralıkta tutar."""
    try:
        value = int(value)
    except Exception:
        return default
    if value <= 0:
        return default
    return min(value, maximum)


def _load_env_file() -> None:
    """Basit .env okuyucu. python-dotenv bağımlılığı gerektirmez."""
    if not ENV_PATH.exists():
        return
    try:
        for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except Exception:
        pass

_load_env_file()

API_ENV = os.environ.get("DAL_ERP_ENV", "development").strip().lower()
IS_PRODUCTION = API_ENV in {"prod", "production", "canli", "live"}

def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "evet", "yes", "on"}

def _allowed_origins() -> list[str]:
    """CORS origin listesi. Varsayılan olarak tamamen kapalıdır.

    Mobil/Windows Flutter uygulaması CORS'a ihtiyaç duymaz.
    Tarayıcı ile test gerekiyorsa sadece gerekli adresleri
    DAL_ERP_ALLOWED_ORIGINS ile açıkça ver.
    Örnek: http://localhost:5000,http://127.0.0.1:5000
    """
    raw = os.environ.get("DAL_ERP_ALLOWED_ORIGINS", "").strip()
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]

def local_ip() -> str:
    """Aynı Wi-Fi içindeki cihazların erişeceği yerel IP adresini bulur."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

app = FastAPI(
    title="DAL ERP Next Mobil API",
    version="3.7-guvenlik-kararlilik",
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
    openapi_url=None if IS_PRODUCTION else "/openapi.json",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_origin_regex=None,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Sabit admin-token kullanılmaz. Servis token sadece açıkça izin verilirse kabul edilir.
ADMIN_TOKEN = os.environ.get("DAL_ERP_ADMIN_TOKEN", "").strip()
ALLOW_SERVICE_TOKEN = _env_bool("DAL_ERP_ALLOW_SERVICE_TOKEN", False)
LOGIN_MAX_ATTEMPTS = int(os.environ.get("DAL_ERP_LOGIN_MAX_ATTEMPTS", "5"))
LOGIN_BLOCK_SECONDS = int(os.environ.get("DAL_ERP_LOGIN_BLOCK_SECONDS", "900"))
_LOGIN_FAILS: dict[str, list[float]] = {}

class LoginRequest(BaseModel):
    kullanici_adi: str = Field(min_length=1, max_length=80)
    sifre: str = Field(min_length=1, max_length=256)


class TahsilatRequest(BaseModel):
    cari_id: int = Field(gt=0)
    tutar: float = Field(gt=0, le=1_000_000_000)
    aciklama: str | None = Field(default="Mobil tahsilat", max_length=300)


class SiparisKalem(BaseModel):
    urun_id: int = Field(ge=0)
    urun_adi: str = Field(min_length=1, max_length=200)
    adet: float = Field(gt=0, le=1_000_000)
    birim_fiyat: float = Field(ge=0, le=1_000_000_000)
    iskonto: float = Field(default=0, ge=0, le=100)
    kdv: float = Field(default=20, ge=0, le=100)


class SiparisRequest(BaseModel):
    cari_id: int = Field(gt=0)
    notlar: str | None = Field(default="", max_length=1000)
    kalemler: list[SiparisKalem] = Field(min_length=1, max_length=200)


class SiparisGuncelleRequest(BaseModel):
    cari_id: int | None = Field(default=None, gt=0)
    notlar: str | None = Field(default=None, max_length=1000)
    durum: str | None = Field(default=None, max_length=40)
    kalemler: list[SiparisKalem] | None = Field(default=None, min_length=1, max_length=200)


class SiparisDurumRequest(BaseModel):
    durum: str = Field(min_length=1, max_length=40)


class FaturaRequest(BaseModel):
    cari_id: int = Field(gt=0)
    notlar: str | None = Field(default="", max_length=1000)
    kalemler: list[SiparisKalem] = Field(min_length=1, max_length=200)


class FirmaRequest(BaseModel):
    firma_adi: str = Field(default="DAL ERP", min_length=1, max_length=200)
    vergi_no: str | None = Field(default="", max_length=50)
    vergi_dairesi: str | None = Field(default="", max_length=100)
    adres: str | None = Field(default="", max_length=500)
    telefon: str | None = Field(default="", max_length=50)
    eposta: str | None = Field(default="", max_length=120)
    web: str | None = Field(default="", max_length=120)
    iban: str | None = Field(default="", max_length=50)
    mersis_no: str | None = Field(default="", max_length=50)
    ticaret_sicil_no: str | None = Field(default="", max_length=50)
    logo_path: str | None = Field(default="", max_length=500)

    @field_validator("logo_path")
    @classmethod
    def logo_path_sinirla(cls, value: str | None) -> str:
        value = (value or "").strip()
        if not value:
            return ""
        # API üzerinden rastgele dosya yolu yazılmasını engelle.
        # Logo yolu masaüstü uygulamasında seçilecekse yerel uygulama katmanı yönetir.
        if ".." in value or value.startswith(("/", "\\")):
            raise ValueError("Logo yolu güvenli değil")
        return value

SIPARIS_DURUMLARI = {"Bekliyor", "Onaylandı", "İrsaliye Kesildi", "Faturalandı", "Teslim Edildi", "Kapandı", "İptal"}
IRSALIYE_DURUMLARI = {"Hazırlandı", "Sevk Edildi", "Faturalandı", "Teslim Edildi", "İptal"}
FATURA_DURUMLARI = {"Kesildi", "Tahsilat Bekliyor", "Kısmi Tahsilat", "Tahsil Edildi", "İptal"}

def kalem_toplam(k: SiparisKalem) -> float:
    ara = float(k.adet) * float(k.birim_fiyat)
    iskontolu = ara - (ara * float(k.iskonto or 0) / 100)
    return round(iskontolu + (iskontolu * float(k.kdv or 0) / 100), 2)

def db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA temp_store = MEMORY")
    except sqlite3.DatabaseError:
        pass
    return conn

def column_exists(cur, table: str, column: str) -> bool:
    table = _sql_identifier(table)
    column = _sql_identifier(column)
    return any(row[1] == column for row in cur.execute(f"PRAGMA table_info({table})").fetchall())

def audit_log(event: str, user: str = "", detail: str = "", ip: str = "") -> None:
    """Hassas bilgi yazmadan basit denetim kaydı tutar."""
    try:
        safe_detail = (detail or "")[:300]
        with db() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS api_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tarih TEXT, event TEXT, kullanici TEXT, ip TEXT, detay TEXT
            )""")
            conn.execute("INSERT INTO api_audit_log (tarih,event,kullanici,ip,detay) VALUES (?,?,?,?,?)",
                         (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), event, user or "", ip or "", safe_detail))
            conn.commit()
    except Exception:
        pass

def _client_ip(request: Request | None) -> str:
    if not request or not request.client:
        return ""
    return request.client.host or ""

def _login_key(username: str, ip: str) -> str:
    return f"{(username or '').strip().lower()}|{ip or ''}"

def _check_login_rate(username: str, ip: str) -> None:
    now = time.time()
    key = _login_key(username, ip)
    fails = [t for t in _LOGIN_FAILS.get(key, []) if now - t < LOGIN_BLOCK_SECONDS]
    _LOGIN_FAILS[key] = fails
    if len(fails) >= LOGIN_MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Çok fazla başarısız giriş denemesi. Lütfen daha sonra tekrar deneyin.")

def _cleanup_login_fails(now: float | None = None) -> None:
    """Eski giriş denemelerini bellekten atar; uzun açık kalan API şişmez."""
    now = now or time.time()
    for key in list(_LOGIN_FAILS):
        kalan = [t for t in _LOGIN_FAILS.get(key, []) if now - t < LOGIN_BLOCK_SECONDS]
        if kalan:
            _LOGIN_FAILS[key] = kalan
        else:
            _LOGIN_FAILS.pop(key, None)


def _record_login_fail(username: str, ip: str) -> None:
    now = time.time()
    _cleanup_login_fails(now)
    key = _login_key(username, ip)
    _LOGIN_FAILS.setdefault(key, []).append(now)
    audit_log("login_failed", username, "Kullanıcı adı veya şifre hatalı", ip)

def _clear_login_fails(username: str, ip: str) -> None:
    _LOGIN_FAILS.pop(_login_key(username, ip), None)

def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS cariler (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT NOT NULL, telefon TEXT DEFAULT '',
        adres TEXT DEFAULT '', vergi_no TEXT DEFAULT '', aktif INTEGER DEFAULT 1
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS hareketler (
        id INTEGER PRIMARY KEY AUTOINCREMENT, cari_id INTEGER, tip TEXT, tutar REAL,
        aciklama TEXT, tarih TEXT, aktif INTEGER DEFAULT 1, FOREIGN KEY(cari_id) REFERENCES cariler(id)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS urunler (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT NOT NULL, barkod TEXT DEFAULT '',
        stok REAL DEFAULT 0, fiyat REAL DEFAULT 0, grup TEXT DEFAULT '', aktif INTEGER DEFAULT 1
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS mobil_siparisler (
        id INTEGER PRIMARY KEY AUTOINCREMENT, cari_id INTEGER, tarih TEXT, toplam REAL,
        notlar TEXT DEFAULT '', durum TEXT DEFAULT 'Bekliyor', aktif INTEGER DEFAULT 1
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS mobil_siparis_kalemleri (
        id INTEGER PRIMARY KEY AUTOINCREMENT, siparis_id INTEGER, urun_id INTEGER, urun_adi TEXT,
        adet REAL, birim_fiyat REAL, iskonto REAL DEFAULT 0, kdv REAL DEFAULT 20, tutar REAL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS mobil_irsaliyeler (
        id INTEGER PRIMARY KEY AUTOINCREMENT, siparis_id INTEGER, cari_id INTEGER, tarih TEXT, toplam REAL,
        notlar TEXT DEFAULT '', durum TEXT DEFAULT 'Hazırlandı', aktif INTEGER DEFAULT 1
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS mobil_irsaliye_kalemleri (
        id INTEGER PRIMARY KEY AUTOINCREMENT, irsaliye_id INTEGER, urun_id INTEGER, urun_adi TEXT,
        adet REAL, birim_fiyat REAL, iskonto REAL DEFAULT 0, kdv REAL DEFAULT 20, tutar REAL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS mobil_faturalar (
        id INTEGER PRIMARY KEY AUTOINCREMENT, irsaliye_id INTEGER, siparis_id INTEGER, cari_id INTEGER, tarih TEXT, toplam REAL,
        notlar TEXT DEFAULT '', durum TEXT DEFAULT 'Kesildi', aktif INTEGER DEFAULT 1
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS mobil_fatura_kalemleri (
        id INTEGER PRIMARY KEY AUTOINCREMENT, fatura_id INTEGER, urun_id INTEGER, urun_adi TEXT,
        adet REAL, birim_fiyat REAL, iskonto REAL DEFAULT 0, kdv REAL DEFAULT 20, tutar REAL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS api_audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, tarih TEXT, event TEXT, kullanici TEXT, ip TEXT, detay TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS api_migrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, applied_at TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS firma_ayarlari (
        id INTEGER PRIMARY KEY CHECK (id=1),
        firma_adi TEXT DEFAULT 'DAL ERP', vergi_no TEXT DEFAULT '', vergi_dairesi TEXT DEFAULT '',
        adres TEXT DEFAULT '', telefon TEXT DEFAULT '', eposta TEXT DEFAULT '', web TEXT DEFAULT '',
        iban TEXT DEFAULT '', mersis_no TEXT DEFAULT '', ticaret_sicil_no TEXT DEFAULT '', logo_path TEXT DEFAULT '',
        updated_at TEXT DEFAULT ''
    )""")
    # Eski veritabanlarında firma_ayarlari tablosu daha az kolonla oluşmuş olabilir.
    # Mobil API başlangıcında eksik kolonları güvenli şekilde tamamlıyoruz.
    try:
        existing_cols = [r[1] for r in cur.execute("PRAGMA table_info(firma_ayarlari)").fetchall()]
        for col_name, col_def in [
            ("web", "TEXT DEFAULT ''"),
            ("iban", "TEXT DEFAULT ''"),
            ("mersis_no", "TEXT DEFAULT ''"),
            ("ticaret_sicil_no", "TEXT DEFAULT ''"),
            ("logo_path", "TEXT DEFAULT ''"),
            ("updated_at", "TEXT DEFAULT ''"),
        ]:
            if col_name not in existing_cols:
                cur.execute(f"ALTER TABLE firma_ayarlari ADD COLUMN {_sql_identifier(col_name)} {col_def}")
    except Exception:
        pass

    cur.execute("""INSERT OR IGNORE INTO firma_ayarlari
        (id,firma_adi,vergi_no,vergi_dairesi,adres,telefon,eposta,web,iban,mersis_no,ticaret_sicil_no,logo_path,updated_at)
        VALUES (1,'DAL ERP','','','','','','','','','','',?)""", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))

    for table, column_def in [
        ("cariler", "aktif INTEGER DEFAULT 1"), ("cariler", "telefon TEXT DEFAULT ''"),
        ("cariler", "adres TEXT DEFAULT ''"), ("cariler", "vergi_no TEXT DEFAULT ''"),
        ("hareketler", "aktif INTEGER DEFAULT 1"), ("hareketler", "tip TEXT"),
        ("hareketler", "tutar REAL DEFAULT 0"), ("hareketler", "aciklama TEXT DEFAULT ''"),
        ("hareketler", "tarih TEXT"),
        ("mobil_siparisler", "durum TEXT DEFAULT 'Bekliyor'"),
        ("mobil_irsaliyeler", "durum TEXT DEFAULT 'Hazırlandı'"),
        ("mobil_faturalar", "durum TEXT DEFAULT 'Kesildi'"),
        ("mobil_faturalar", "irsaliye_id INTEGER"),
        ("mobil_faturalar", "siparis_id INTEGER"),
        ("mobil_faturalar", "cari_id INTEGER"),
        ("mobil_faturalar", "notlar TEXT DEFAULT ''"),
        ("mobil_faturalar", "aktif INTEGER DEFAULT 1"),
    ]:
        col = column_def.split()[0]
        if not column_exists(cur, table, col):
            cur.execute(f"ALTER TABLE {_sql_identifier(table)} ADD COLUMN {column_def}")

    cur.execute("CREATE INDEX IF NOT EXISTS idx_mobil_siparis_cari ON mobil_siparisler(cari_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_mobil_irsaliye_siparis ON mobil_irsaliyeler(siparis_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_mobil_fatura_irsaliye ON mobil_faturalar(irsaliye_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_mobil_fatura_siparis ON mobil_faturalar(siparis_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_mobil_siparis_aktif_durum_tarih ON mobil_siparisler(aktif, durum, tarih)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_mobil_irsaliye_aktif_durum_tarih ON mobil_irsaliyeler(aktif, durum, tarih)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_mobil_fatura_aktif_durum_tarih ON mobil_faturalar(aktif, durum, tarih)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_api_audit_tarih_event ON api_audit_log(tarih, event)")

    if cur.execute("SELECT COUNT(*) AS s FROM urunler").fetchone()["s"] == 0:
        cur.executemany("INSERT INTO urunler (ad,barkod,stok,fiyat,grup) VALUES (?,?,?,?,?)", [
            ("Örnek Ürün 1", "869000000001", 100, 120, "Genel"),
            ("Örnek Ürün 2", "869000000002", 50, 250, "Genel"),
            ("Hizmet Bedeli", "", 9999, 500, "Hizmet"),
        ])
    conn.commit()
    conn.close()

def check_auth(authorization: str | None):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token yok")
    token = authorization.replace("Bearer ", "").strip()
    user = get_user_from_token(token)
    if user:
        return user
    # İsteğe bağlı servis token: sadece env ile tanımlandıysa geçerli.
    if ALLOW_SERVICE_TOKEN and ADMIN_TOKEN and secrets.compare_digest(token, ADMIN_TOKEN):
        return {"id": 0, "kullanici_adi": "service", "rol": "Servis"}
    raise HTTPException(status_code=401, detail="Geçersiz token")

def bakiye_expr() -> str:
    return """COALESCE(SUM(CASE WHEN UPPER(h.tip) = 'BORÇ' THEN h.tutar ELSE 0 END),0)
              - COALESCE(SUM(CASE WHEN UPPER(h.tip) = 'TAHSİLAT' THEN h.tutar ELSE 0 END),0)"""

def cari_bakiye(conn, cari_id: int) -> float:
    row = conn.execute("""SELECT COALESCE(SUM(CASE WHEN UPPER(tip)='BORÇ' THEN tutar ELSE 0 END),0)
        - COALESCE(SUM(CASE WHEN UPPER(tip)='TAHSİLAT' THEN tutar ELSE 0 END),0) AS bakiye
        FROM hareketler WHERE cari_id=? AND COALESCE(aktif,1)=1""", (cari_id,)).fetchone()
    return float(row["bakiye"] or 0)

@app.on_event("startup")
def startup():
    init_db()
    _cleanup_login_fails()
    audit_log("api_start", "system", f"env={API_ENV}; ip={local_ip()}")

@app.get("/")
def root():
    return {"message": "DAL ERP Mobil API aktif", "version": "3.2-canliya-hazirlik", "env": API_ENV, "local_ip": local_ip(), "docs_enabled": not IS_PRODUCTION, "paket": "v32 Canlıya Hazırlık Toplu Paket"}

@app.get("/health")
def health():
    return {"ok": True, "db": DB_PATH.exists(), "time": datetime.now().isoformat(), "env": API_ENV, "local_ip": local_ip()}

@app.post("/login")
def login(req: LoginRequest, request: Request):
    # KRİTİK: admin/1234 hardcoded test girişi yoktur.
    # Giriş sadece veritabanındaki kullanıcı kayıtları üzerinden yapılır.
    ip = _client_ip(request)
    _check_login_rate(req.kullanici_adi, ip)
    result = login_from_db(req.kullanici_adi, req.sifre)
    if result:
        _clear_login_fails(req.kullanici_adi, ip)
        audit_log("login_success", result.get("kullanici_adi", req.kullanici_adi), "Mobil API login", ip)
        return result
    _record_login_fail(req.kullanici_adi, ip)
    raise HTTPException(status_code=401, detail="Kullanıcı adı veya şifre hatalı")

@app.get("/firma")
def firma_getir(authorization: str | None = Header(None)):
    check_auth(authorization)
    conn = db()
    row = conn.execute("SELECT * FROM firma_ayarlari WHERE id=1").fetchone()
    if not row:
        conn.execute("INSERT OR IGNORE INTO firma_ayarlari (id,firma_adi,updated_at) VALUES (1,'DAL ERP',?)", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
        conn.commit()
        row = conn.execute("SELECT * FROM firma_ayarlari WHERE id=1").fetchone()
    data = dict(row)
    conn.close()
    return data

@app.put("/firma")
def firma_guncelle(req: FirmaRequest, authorization: str | None = Header(None)):
    check_auth(authorization)
    conn = db()
    cur = conn.cursor()
    cur.execute("""UPDATE firma_ayarlari SET
        firma_adi=?, vergi_no=?, vergi_dairesi=?, adres=?, telefon=?, eposta=?, web=?,
        iban=?, mersis_no=?, ticaret_sicil_no=?, logo_path=?, updated_at=?
        WHERE id=1""", (
        req.firma_adi, req.vergi_no or '', req.vergi_dairesi or '', req.adres or '', req.telefon or '',
        req.eposta or '', req.web or '', req.iban or '', req.mersis_no or '', req.ticaret_sicil_no or '',
        req.logo_path or '', datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    if cur.rowcount == 0:
        cur.execute("""INSERT INTO firma_ayarlari
            (id,firma_adi,vergi_no,vergi_dairesi,adres,telefon,eposta,web,iban,mersis_no,ticaret_sicil_no,logo_path,updated_at)
            VALUES (1,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            req.firma_adi, req.vergi_no or '', req.vergi_dairesi or '', req.adres or '', req.telefon or '',
            req.eposta or '', req.web or '', req.iban or '', req.mersis_no or '', req.ticaret_sicil_no or '',
            req.logo_path or '', datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
    conn.commit()
    conn.close()
    return {"ok": True, "message": "Firma ayarları güncellendi"}

@app.get("/dashboard")
def dashboard(authorization: str | None = Header(None)):
    check_auth(authorization)
    conn = db()
    cur = conn.cursor()
    bugun = datetime.now().strftime("%Y-%m-%d")
    cari_sayisi = cur.execute("SELECT COUNT(*) AS s FROM cariler WHERE COALESCE(aktif,1)=1").fetchone()["s"]
    toplam_bakiye = cur.execute(f"SELECT {bakiye_expr()} AS s FROM hareketler h WHERE COALESCE(h.aktif,1)=1").fetchone()["s"]
    bugun_tahsilat = cur.execute("SELECT COALESCE(SUM(tutar),0) AS s FROM hareketler WHERE COALESCE(aktif,1)=1 AND UPPER(tip)='TAHSİLAT' AND substr(COALESCE(tarih,''),1,10)=?", (bugun,)).fetchone()["s"]
    bugun_satis = cur.execute("SELECT COALESCE(SUM(tutar),0) AS s FROM hareketler WHERE COALESCE(aktif,1)=1 AND UPPER(tip)='BORÇ' AND substr(COALESCE(tarih,''),1,10)=?", (bugun,)).fetchone()["s"]
    bekleyen_siparis = cur.execute("SELECT COUNT(*) AS s FROM mobil_siparisler WHERE COALESCE(aktif,1)=1 AND COALESCE(durum,'Bekliyor') IN ('Bekliyor','Onaylandı')").fetchone()["s"]
    bekleyen_irsaliye = cur.execute("SELECT COUNT(*) AS s FROM mobil_irsaliyeler WHERE COALESCE(aktif,1)=1 AND COALESCE(durum,'Hazırlandı') IN ('Hazırlandı','Sevk Edildi')").fetchone()["s"]
    bekleyen_fatura = cur.execute("SELECT COUNT(*) AS s FROM mobil_faturalar WHERE COALESCE(aktif,1)=1 AND COALESCE(durum,'Kesildi') IN ('Kesildi','Tahsilat Bekliyor','Kısmi Tahsilat')").fetchone()["s"]
    son = [dict(r) for r in cur.execute("""SELECT h.id,h.tarih,h.aciklama,h.tutar,h.tip,c.ad AS cari_ad
        FROM hareketler h LEFT JOIN cariler c ON c.id=h.cari_id WHERE COALESCE(h.aktif,1)=1 ORDER BY h.id DESC LIMIT 10""").fetchall()]
    conn.close()
    return {"cari_sayisi": int(cari_sayisi or 0), "bugun_satis": float(bugun_satis or 0), "bugun_tahsilat": float(bugun_tahsilat or 0), "toplam_bakiye": float(toplam_bakiye or 0), "bekleyen_siparis": int(bekleyen_siparis or 0), "bekleyen_irsaliye": int(bekleyen_irsaliye or 0), "bekleyen_fatura": int(bekleyen_fatura or 0), "son_hareketler": son}

@app.get("/cariler")
def cariler(q: str = "", limit: int = 100, authorization: str | None = Header(None)):
    check_auth(authorization)
    limit = _limit_value(limit, default=100, maximum=500)
    q = (q or "").strip()[:80]
    conn = db()
    like = f"%{q}%"
    rows = conn.execute(f"""SELECT c.id,c.ad,COALESCE(c.telefon,'') telefon,COALESCE(c.adres,'') adres,COALESCE(c.vergi_no,'') vergi_no,{bakiye_expr()} AS bakiye
        FROM cariler c LEFT JOIN hareketler h ON h.cari_id=c.id AND COALESCE(h.aktif,1)=1
        WHERE COALESCE(c.aktif,1)=1 AND (c.ad LIKE ? OR COALESCE(c.telefon,'') LIKE ?)
        GROUP BY c.id,c.ad,c.telefon,c.adres,c.vergi_no ORDER BY c.ad LIMIT ?""", (like, like, limit)).fetchall()
    conn.close()
    return {"items": [dict(r) for r in rows]}

@app.get("/cariler/{cari_id}")
def cari_detay(cari_id: int, authorization: str | None = Header(None)):
    check_auth(authorization)
    conn = db()
    row = conn.execute("SELECT id,ad,COALESCE(telefon,'') telefon,COALESCE(adres,'') adres,COALESCE(vergi_no,'') vergi_no FROM cariler WHERE id=? AND COALESCE(aktif,1)=1", (cari_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Cari bulunamadı")
    data = dict(row)
    data["bakiye"] = cari_bakiye(conn, cari_id)
    conn.close()
    return data

@app.get("/cariler/{cari_id}/hareketler")
def cari_hareketler(cari_id: int, limit: int = 100, authorization: str | None = Header(None)):
    check_auth(authorization)
    limit = _limit_value(limit, default=100, maximum=500)
    conn = db()
    rows = conn.execute("SELECT id,cari_id,tarih,aciklama,tutar,tip FROM hareketler WHERE cari_id=? AND COALESCE(aktif,1)=1 ORDER BY id DESC LIMIT ?", (cari_id, limit)).fetchall()
    conn.close()
    return {"items": [dict(r) for r in rows]}

@app.post("/tahsilat")
def tahsilat(req: TahsilatRequest, authorization: str | None = Header(None)):
    check_auth(authorization)
    if req.tutar <= 0:
        raise HTTPException(status_code=400, detail="Tutar sıfırdan büyük olmalı")
    conn = db()
    if not conn.execute("SELECT id FROM cariler WHERE id=? AND COALESCE(aktif,1)=1", (req.cari_id,)).fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Cari bulunamadı")
    conn.execute("INSERT INTO hareketler (cari_id,tip,tutar,aciklama,tarih,aktif) VALUES (?, 'TAHSİLAT', ?, ?, ?, 1)", (req.cari_id, abs(req.tutar), req.aciklama or "Mobil tahsilat", datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()
    return {"ok": True, "message": "Tahsilat kaydedildi"}

@app.get("/urunler")
def urunler(q: str = "", limit: int = 100, authorization: str | None = Header(None)):
    check_auth(authorization)
    conn = db()
    like = f"%{q}%"
    rows = conn.execute("""SELECT id,ad,COALESCE(barkod,'') barkod,COALESCE(stok,0) stok,COALESCE(fiyat, 0) fiyat,COALESCE(grup,'') grup
        FROM urunler WHERE COALESCE(aktif,1)=1 AND (ad LIKE ? OR COALESCE(barkod,'') LIKE ?) ORDER BY ad LIMIT ?""", (like, like, limit)).fetchall()
    conn.close()
    return {"items": [dict(r) for r in rows]}

@app.post("/siparis")
def siparis(req: SiparisRequest, authorization: str | None = Header(None)):
    check_auth(authorization)
    if not req.kalemler:
        raise HTTPException(status_code=400, detail="Sepet boş")
    conn = db()
    if not conn.execute("SELECT id FROM cariler WHERE id=? AND COALESCE(aktif,1)=1", (req.cari_id,)).fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Cari bulunamadı")
    toplam = sum(kalem_toplam(k) for k in req.kalemler)
    cur = conn.cursor()
    cur.execute("INSERT INTO mobil_siparisler (cari_id,tarih,toplam,notlar,durum,aktif) VALUES (?,?,?,?, 'Bekliyor',1)", (req.cari_id, datetime.now().strftime("%Y-%m-%d"), toplam, req.notlar or ""))
    sid = cur.lastrowid
    for k in req.kalemler:
        tutar = kalem_toplam(k)
        cur.execute("""INSERT INTO mobil_siparis_kalemleri (siparis_id,urun_id,urun_adi,adet,birim_fiyat,iskonto,kdv,tutar)
            VALUES (?,?,?,?,?,?,?,?)""", (sid, k.urun_id, k.urun_adi, k.adet, k.birim_fiyat, k.iskonto, k.kdv, tutar))
    conn.execute("INSERT INTO hareketler (cari_id,tip,tutar,aciklama,tarih,aktif) VALUES (?, 'BORÇ', ?, ?, ?, 1)", (req.cari_id, toplam, f"Mobil sipariş #{sid}", datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()
    return {"ok": True, "siparis_id": sid, "toplam": toplam}

@app.get("/siparisler")
def siparisler(q: str = "", limit: int = 50, authorization: str | None = Header(None)):
    check_auth(authorization)
    conn = db()
    like = f"%{q}%"
    rows = conn.execute("""SELECT s.id,s.cari_id,s.tarih,s.toplam,s.notlar,c.ad AS cari_ad,
            ('#' || s.id) AS siparis_no, COALESCE(s.durum,'Bekliyor') AS durum
        FROM mobil_siparisler s
        LEFT JOIN cariler c ON c.id=s.cari_id
        WHERE COALESCE(s.aktif,1)=1
          AND (? = '' OR CAST(s.id AS TEXT) LIKE ? OR COALESCE(c.ad,'') LIKE ? OR COALESCE(s.notlar,'') LIKE ?)
        ORDER BY s.id DESC LIMIT ?""", (q, like, like, like, limit)).fetchall()
    conn.close()
    return {"items": [dict(r) for r in rows]}

@app.get("/siparisler/{siparis_id}")
def siparis_detay(siparis_id: int, authorization: str | None = Header(None)):
    check_auth(authorization)
    conn = db()
    row = conn.execute("""SELECT s.id,s.cari_id,s.tarih,s.toplam,s.notlar,c.ad AS cari_ad,
            ('#' || s.id) AS siparis_no, COALESCE(s.durum,'Bekliyor') AS durum
        FROM mobil_siparisler s
        LEFT JOIN cariler c ON c.id=s.cari_id
        WHERE s.id=? AND COALESCE(s.aktif,1)=1""", (siparis_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı")
    data = dict(row)
    kalemler = conn.execute("""SELECT id,siparis_id,urun_id,urun_adi,adet,birim_fiyat,iskonto,kdv,tutar
        FROM mobil_siparis_kalemleri WHERE siparis_id=? ORDER BY id""", (siparis_id,)).fetchall()
    data["kalemler"] = [dict(r) for r in kalemler]
    conn.close()
    return data


@app.put("/siparisler/{siparis_id}/durum")
def siparis_durum_guncelle(siparis_id: int, req: SiparisDurumRequest, authorization: str | None = Header(None)):
    check_auth(authorization)
    izinli = SIPARIS_DURUMLARI
    if req.durum not in izinli:
        raise HTTPException(status_code=400, detail="Geçersiz durum")
    conn = db()
    cur = conn.cursor()
    cur.execute("UPDATE mobil_siparisler SET durum=? WHERE id=? AND COALESCE(aktif,1)=1", (req.durum, siparis_id))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı")
    conn.commit()
    conn.close()
    return {"ok": True, "siparis_id": siparis_id, "durum": req.durum}

@app.put("/siparisler/{siparis_id}")
def siparis_guncelle(siparis_id: int, req: SiparisGuncelleRequest, authorization: str | None = Header(None)):
    check_auth(authorization)
    conn = db()
    cur = conn.cursor()
    row = cur.execute("SELECT id,cari_id FROM mobil_siparisler WHERE id=? AND COALESCE(aktif,1)=1", (siparis_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı")

    cari_id = req.cari_id if req.cari_id is not None else row["cari_id"]
    if not cur.execute("SELECT id FROM cariler WHERE id=? AND COALESCE(aktif,1)=1", (cari_id,)).fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Cari bulunamadı")

    if req.durum is not None:
        izinli = SIPARIS_DURUMLARI
        if req.durum not in izinli:
            conn.close()
            raise HTTPException(status_code=400, detail="Geçersiz durum")

    toplam = None
    if req.kalemler is not None:
        if not req.kalemler:
            conn.close()
            raise HTTPException(status_code=400, detail="Kalemler boş olamaz")
        toplam = 0.0
        cur.execute("DELETE FROM mobil_siparis_kalemleri WHERE siparis_id=?", (siparis_id,))
        for k in req.kalemler:
            ara = k.adet * k.birim_fiyat
            iskontolu = ara - (ara * k.iskonto / 100)
            tutar = iskontolu + (iskontolu * k.kdv / 100)
            toplam += tutar
            cur.execute("""INSERT INTO mobil_siparis_kalemleri (siparis_id,urun_id,urun_adi,adet,birim_fiyat,iskonto,kdv,tutar)
                VALUES (?,?,?,?,?,?,?,?)""", (siparis_id, k.urun_id, k.urun_adi, k.adet, k.birim_fiyat, k.iskonto, k.kdv, tutar))

    updates = ["cari_id=?"]
    params = [cari_id]
    if req.notlar is not None:
        updates.append("notlar=?")
        params.append(req.notlar)
    if req.durum is not None:
        updates.append("durum=?")
        params.append(req.durum)
    if toplam is not None:
        updates.append("toplam=?")
        params.append(toplam)
    params.append(siparis_id)
    cur.execute(f"UPDATE mobil_siparisler SET {', '.join(updates)} WHERE id=? AND COALESCE(aktif,1)=1", params)
    conn.commit()
    conn.close()
    return {"ok": True, "siparis_id": siparis_id, "toplam": toplam}

@app.delete("/siparisler/{siparis_id}")
def siparis_sil(siparis_id: int, authorization: str | None = Header(None)):
    check_auth(authorization)
    conn = db()
    cur = conn.cursor()
    cur.execute("UPDATE mobil_siparisler SET aktif=0 WHERE id=? AND COALESCE(aktif,1)=1", (siparis_id,))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı")
    conn.commit()
    conn.close()
    return {"ok": True, "siparis_id": siparis_id, "message": "Sipariş silindi"}


@app.get("/irsaliyeler")
def irsaliyeler(q: str = "", limit: int = 50, authorization: str | None = Header(None)):
    check_auth(authorization)
    conn = db()
    like = f"%{q}%"
    rows = conn.execute("""SELECT i.id,i.siparis_id,i.cari_id,i.tarih,i.toplam,i.notlar,i.durum,c.ad AS cari_ad,
            ('IRS-' || i.id) AS irsaliye_no, ('#' || i.siparis_id) AS siparis_no
        FROM mobil_irsaliyeler i
        LEFT JOIN cariler c ON c.id=i.cari_id
        WHERE COALESCE(i.aktif,1)=1
          AND (?='' OR CAST(i.id AS TEXT) LIKE ? OR COALESCE(c.ad,'') LIKE ? OR COALESCE(i.notlar,'') LIKE ?)
        ORDER BY i.id DESC LIMIT ?""", (q, like, like, like, limit)).fetchall()
    conn.close()
    return {"items": [dict(r) for r in rows]}

@app.get("/irsaliyeler/{irsaliye_id}")
def irsaliye_detay(irsaliye_id: int, authorization: str | None = Header(None)):
    check_auth(authorization)
    conn = db()
    row = conn.execute("""SELECT i.id,i.siparis_id,i.cari_id,i.tarih,i.toplam,i.notlar,i.durum,c.ad AS cari_ad,
            ('IRS-' || i.id) AS irsaliye_no, ('#' || i.siparis_id) AS siparis_no
        FROM mobil_irsaliyeler i LEFT JOIN cariler c ON c.id=i.cari_id
        WHERE i.id=? AND COALESCE(i.aktif,1)=1""", (irsaliye_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="İrsaliye bulunamadı")
    data = dict(row)
    kalemler = conn.execute("""SELECT id,irsaliye_id,urun_id,urun_adi,adet,birim_fiyat,iskonto,kdv,tutar
        FROM mobil_irsaliye_kalemleri WHERE irsaliye_id=? ORDER BY id""", (irsaliye_id,)).fetchall()
    data["kalemler"] = [dict(r) for r in kalemler]
    conn.close()
    return data

@app.post("/irsaliyeler/siparisten/{siparis_id}")
def irsaliye_siparisten(siparis_id: int, authorization: str | None = Header(None)):
    check_auth(authorization)
    conn = db()
    cur = conn.cursor()
    old = cur.execute("SELECT id FROM mobil_irsaliyeler WHERE siparis_id=? AND COALESCE(aktif,1)=1", (siparis_id,)).fetchone()
    if old:
        conn.close()
        return {"ok": True, "irsaliye_id": old["id"], "message": "Bu sipariş için irsaliye zaten var"}
    sip = cur.execute("SELECT id,cari_id,toplam,notlar FROM mobil_siparisler WHERE id=? AND COALESCE(aktif,1)=1", (siparis_id,)).fetchone()
    if not sip:
        conn.close()
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı")
    kalemler = cur.execute("""SELECT urun_id,urun_adi,adet,birim_fiyat,iskonto,kdv,tutar
        FROM mobil_siparis_kalemleri WHERE siparis_id=? ORDER BY id""", (siparis_id,)).fetchall()
    if not kalemler:
        conn.close()
        raise HTTPException(status_code=400, detail="Sipariş kalemi yok")
    cur.execute("""INSERT INTO mobil_irsaliyeler (siparis_id,cari_id,tarih,toplam,notlar,durum,aktif)
        VALUES (?,?,?,?,?, 'Hazırlandı',1)""", (siparis_id, sip["cari_id"], datetime.now().strftime("%Y-%m-%d"), sip["toplam"], sip["notlar"] or ""))
    iid = cur.lastrowid
    for k in kalemler:
        cur.execute("""INSERT INTO mobil_irsaliye_kalemleri (irsaliye_id,urun_id,urun_adi,adet,birim_fiyat,iskonto,kdv,tutar)
            VALUES (?,?,?,?,?,?,?,?)""", (iid, k["urun_id"], k["urun_adi"], k["adet"], k["birim_fiyat"], k["iskonto"], k["kdv"], k["tutar"]))
    cur.execute("UPDATE mobil_siparisler SET durum='İrsaliye Kesildi' WHERE id=?", (siparis_id,))
    conn.commit()
    conn.close()
    return {"ok": True, "irsaliye_id": iid, "siparis_id": siparis_id, "message": "İrsaliye oluşturuldu"}

@app.put("/irsaliyeler/{irsaliye_id}/durum")
def irsaliye_durum_guncelle(irsaliye_id: int, req: SiparisDurumRequest, authorization: str | None = Header(None)):
    check_auth(authorization)
    izinli = {"Hazırlandı", "Sevk Edildi", "Faturalandı", "İptal"}
    if req.durum not in izinli:
        raise HTTPException(status_code=400, detail="Geçersiz durum")
    conn = db()
    cur = conn.cursor()
    cur.execute("UPDATE mobil_irsaliyeler SET durum=? WHERE id=? AND COALESCE(aktif,1)=1", (req.durum, irsaliye_id))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="İrsaliye bulunamadı")
    conn.commit()
    conn.close()
    return {"ok": True, "irsaliye_id": irsaliye_id, "durum": req.durum}

@app.delete("/irsaliyeler/{irsaliye_id}")
def irsaliye_sil(irsaliye_id: int, authorization: str | None = Header(None)):
    check_auth(authorization)
    conn = db()
    cur = conn.cursor()
    cur.execute("UPDATE mobil_irsaliyeler SET aktif=0, durum='İptal' WHERE id=? AND COALESCE(aktif,1)=1", (irsaliye_id,))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="İrsaliye bulunamadı")
    conn.commit()
    conn.close()
    return {"ok": True, "irsaliye_id": irsaliye_id, "message": "İrsaliye iptal edildi"}

@app.get("/faturalar")
def faturalar(q: str = "", limit: int = 50, authorization: str | None = Header(None)):
    check_auth(authorization)
    conn = db()
    like = f"%{q}%"
    rows = conn.execute("""SELECT f.id,f.irsaliye_id,f.siparis_id,f.cari_id,f.tarih,f.toplam,f.notlar,f.durum,c.ad AS cari_ad,
            ('FAT-' || f.id) AS fatura_no, ('IRS-' || f.irsaliye_id) AS irsaliye_no
        FROM mobil_faturalar f LEFT JOIN cariler c ON c.id=f.cari_id
        WHERE COALESCE(f.aktif,1)=1
          AND (?='' OR CAST(f.id AS TEXT) LIKE ? OR COALESCE(c.ad,'') LIKE ? OR COALESCE(f.notlar,'') LIKE ?)
        ORDER BY f.id DESC LIMIT ?""", (q, like, like, like, limit)).fetchall()
    conn.close()
    return {"items": [dict(r) for r in rows]}

@app.get("/faturalar/{fatura_id}")
def fatura_detay(fatura_id: int, authorization: str | None = Header(None)):
    check_auth(authorization)
    conn = db()
    row = conn.execute("""SELECT f.id,f.irsaliye_id,f.siparis_id,f.cari_id,f.tarih,f.toplam,f.notlar,f.durum,c.ad AS cari_ad,
            ('FAT-' || f.id) AS fatura_no, ('IRS-' || f.irsaliye_id) AS irsaliye_no
        FROM mobil_faturalar f LEFT JOIN cariler c ON c.id=f.cari_id
        WHERE f.id=? AND COALESCE(f.aktif,1)=1""", (fatura_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Fatura bulunamadı")
    data = dict(row)
    kalemler = conn.execute("""SELECT id,fatura_id,urun_id,urun_adi,adet,birim_fiyat,iskonto,kdv,tutar
        FROM mobil_fatura_kalemleri WHERE fatura_id=? ORDER BY id""", (fatura_id,)).fetchall()
    data["kalemler"] = [dict(r) for r in kalemler]
    conn.close()
    return data

@app.post("/faturalar/irsaliyeden/{irsaliye_id}")
def fatura_irsaliyeden(irsaliye_id: int, authorization: str | None = Header(None)):
    check_auth(authorization)
    conn = db()
    cur = conn.cursor()
    old = cur.execute("SELECT id FROM mobil_faturalar WHERE irsaliye_id=? AND COALESCE(aktif,1)=1", (irsaliye_id,)).fetchone()
    if old:
        conn.close()
        return {"ok": True, "fatura_id": old["id"], "message": "Bu irsaliye için fatura zaten var"}
    irs = cur.execute("SELECT id,siparis_id,cari_id,toplam,notlar FROM mobil_irsaliyeler WHERE id=? AND COALESCE(aktif,1)=1", (irsaliye_id,)).fetchone()
    if not irs:
        conn.close()
        raise HTTPException(status_code=404, detail="İrsaliye bulunamadı")
    kalemler = cur.execute("""SELECT urun_id,urun_adi,adet,birim_fiyat,iskonto,kdv,tutar
        FROM mobil_irsaliye_kalemleri WHERE irsaliye_id=? ORDER BY id""", (irsaliye_id,)).fetchall()
    if not kalemler:
        conn.close()
        raise HTTPException(status_code=400, detail="İrsaliye kalemi yok")
    cur.execute("""INSERT INTO mobil_faturalar (irsaliye_id,siparis_id,cari_id,tarih,toplam,notlar,durum,aktif)
        VALUES (?,?,?,?,?,?,'Kesildi',1)""", (irsaliye_id, irs["siparis_id"], irs["cari_id"], datetime.now().strftime("%Y-%m-%d"), irs["toplam"], irs["notlar"] or ""))
    fid = cur.lastrowid
    for k in kalemler:
        cur.execute("""INSERT INTO mobil_fatura_kalemleri (fatura_id,urun_id,urun_adi,adet,birim_fiyat,iskonto,kdv,tutar)
            VALUES (?,?,?,?,?,?,?,?)""", (fid, k["urun_id"], k["urun_adi"], k["adet"], k["birim_fiyat"], k["iskonto"], k["kdv"], k["tutar"]))
    cur.execute("UPDATE mobil_irsaliyeler SET durum='Faturalandı' WHERE id=?", (irsaliye_id,))
    conn.commit()
    conn.close()
    return {"ok": True, "fatura_id": fid, "irsaliye_id": irsaliye_id, "message": "Fatura oluşturuldu"}


@app.get("/siparisler/{siparis_id}/zincir")
def siparis_zincir(siparis_id: int, authorization: str | None = Header(None)):
    check_auth(authorization)
    conn = db()
    sip = conn.execute("""SELECT s.id,s.cari_id,s.tarih,s.toplam,s.notlar,COALESCE(s.durum,'Bekliyor') durum,c.ad AS cari_ad
        FROM mobil_siparisler s LEFT JOIN cariler c ON c.id=s.cari_id
        WHERE s.id=? AND COALESCE(s.aktif,1)=1""", (siparis_id,)).fetchone()
    if not sip:
        conn.close()
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı")
    irs = conn.execute("""SELECT id,siparis_id,cari_id,tarih,toplam,notlar,COALESCE(durum,'Hazırlandı') durum,
        ('IRS-' || id) AS irsaliye_no FROM mobil_irsaliyeler WHERE siparis_id=? AND COALESCE(aktif,1)=1 ORDER BY id DESC LIMIT 1""", (siparis_id,)).fetchone()
    fat = conn.execute("""SELECT id,irsaliye_id,siparis_id,cari_id,tarih,toplam,notlar,COALESCE(durum,'Kesildi') durum,
        ('FAT-' || id) AS fatura_no FROM mobil_faturalar WHERE siparis_id=? AND COALESCE(aktif,1)=1 ORDER BY id DESC LIMIT 1""", (siparis_id,)).fetchone()
    conn.close()
    return {"siparis": dict(sip), "irsaliye": dict(irs) if irs else None, "fatura": dict(fat) if fat else None}

@app.post("/siparisler/{siparis_id}/irsaliye")
def irsaliye_siparisten_alias(siparis_id: int, authorization: str | None = Header(None)):
    return irsaliye_siparisten(siparis_id, authorization)

@app.post("/irsaliyeler/{irsaliye_id}/fatura")
def fatura_irsaliyeden_alias(irsaliye_id: int, authorization: str | None = Header(None)):
    return fatura_irsaliyeden(irsaliye_id, authorization)

@app.post("/faturalar")
def fatura_olustur(req: FaturaRequest, authorization: str | None = Header(None)):
    check_auth(authorization)
    if not req.kalemler:
        raise HTTPException(status_code=400, detail="Fatura kalemi boş")
    conn = db()
    cur = conn.cursor()
    if not cur.execute("SELECT id FROM cariler WHERE id=? AND COALESCE(aktif,1)=1", (req.cari_id,)).fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Cari bulunamadı")
    toplam = sum(kalem_toplam(k) for k in req.kalemler)
    cur.execute("""INSERT INTO mobil_faturalar (irsaliye_id,siparis_id,cari_id,tarih,toplam,notlar,durum,aktif)
        VALUES (NULL,NULL,?,?,?,?, 'Kesildi',1)""", (req.cari_id, datetime.now().strftime("%Y-%m-%d"), toplam, req.notlar or ""))
    fid = cur.lastrowid
    for k in req.kalemler:
        cur.execute("""INSERT INTO mobil_fatura_kalemleri (fatura_id,urun_id,urun_adi,adet,birim_fiyat,iskonto,kdv,tutar)
            VALUES (?,?,?,?,?,?,?,?)""", (fid, k.urun_id, k.urun_adi, k.adet, k.birim_fiyat, k.iskonto, k.kdv, kalem_toplam(k)))
    conn.commit()
    conn.close()
    return {"ok": True, "fatura_id": fid, "toplam": toplam, "message": "Fatura oluşturuldu"}

@app.put("/faturalar/{fatura_id}/durum")
def fatura_durum_guncelle(fatura_id: int, req: SiparisDurumRequest, authorization: str | None = Header(None)):
    check_auth(authorization)
    if req.durum not in FATURA_DURUMLARI:
        raise HTTPException(status_code=400, detail="Geçersiz durum")
    conn = db()
    cur = conn.cursor()
    cur.execute("UPDATE mobil_faturalar SET durum=? WHERE id=? AND COALESCE(aktif,1)=1", (req.durum, fatura_id))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Fatura bulunamadı")
    conn.commit()
    conn.close()
    return {"ok": True, "fatura_id": fatura_id, "durum": req.durum}

@app.delete("/faturalar/{fatura_id}")
def fatura_sil(fatura_id: int, authorization: str | None = Header(None)):
    check_auth(authorization)
    conn = db()
    cur = conn.cursor()
    cur.execute("UPDATE mobil_faturalar SET aktif=0, durum='İptal' WHERE id=? AND COALESCE(aktif,1)=1", (fatura_id,))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Fatura bulunamadı")
    conn.commit()
    conn.close()
    return {"ok": True, "fatura_id": fatura_id, "message": "Fatura iptal edildi"}

@app.get("/cariler/{cari_id}/ekstre")
def cari_ekstre(cari_id: int, limit: int = 200, authorization: str | None = Header(None)):
    check_auth(authorization)
    conn = db()
    if not conn.execute("SELECT id FROM cariler WHERE id=? AND COALESCE(aktif,1)=1", (cari_id,)).fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Cari bulunamadı")
    rows = []
    for r in conn.execute("SELECT tarih,tip,aciklama,tutar,id FROM hareketler WHERE cari_id=? AND COALESCE(aktif,1)=1", (cari_id,)).fetchall():
        rows.append({"tarih": r["tarih"], "tip": r["tip"], "aciklama": r["aciklama"], "tutar": r["tutar"], "kaynak": "hareket", "id": r["id"]})
    for r in conn.execute("SELECT id,tarih,toplam,durum FROM mobil_siparisler WHERE cari_id=? AND COALESCE(aktif,1)=1", (cari_id,)).fetchall():
        rows.append({"tarih": r["tarih"], "tip": "SİPARİŞ", "aciklama": f"Mobil sipariş #{r['id']} - {r['durum']}", "tutar": r["toplam"], "kaynak": "siparis", "id": r["id"]})
    for r in conn.execute("SELECT id,tarih,toplam,durum FROM mobil_irsaliyeler WHERE cari_id=? AND COALESCE(aktif,1)=1", (cari_id,)).fetchall():
        rows.append({"tarih": r["tarih"], "tip": "İRSALİYE", "aciklama": f"İrsaliye IRS-{r['id']} - {r['durum']}", "tutar": r["toplam"], "kaynak": "irsaliye", "id": r["id"]})
    for r in conn.execute("SELECT id,tarih,toplam,durum FROM mobil_faturalar WHERE cari_id=? AND COALESCE(aktif,1)=1", (cari_id,)).fetchall():
        rows.append({"tarih": r["tarih"], "tip": "FATURA", "aciklama": f"Fatura FAT-{r['id']} - {r['durum']}", "tutar": r["toplam"], "kaynak": "fatura", "id": r["id"]})
    conn.close()
    rows.sort(key=lambda x: (x.get("tarih") or "", x.get("id") or 0), reverse=True)
    return {"items": rows[:limit]}


@app.get("/raporlar/ozet")
def raporlar_ozet(authorization: str | None = Header(None)):
    check_auth(authorization)
    conn = db()
    cur = conn.cursor()
    rows = {}
    rows["cari_sayisi"] = cur.execute("SELECT COUNT(*) AS s FROM cariler WHERE COALESCE(aktif,1)=1").fetchone()["s"] or 0
    rows["urun_sayisi"] = cur.execute("SELECT COUNT(*) AS s FROM urunler WHERE COALESCE(aktif,1)=1").fetchone()["s"] or 0
    rows["stok_degeri"] = cur.execute("SELECT COALESCE(SUM(COALESCE(stok,0)*COALESCE(fiyat,0)),0) AS s FROM urunler WHERE COALESCE(aktif,1)=1").fetchone()["s"] or 0
    rows["siparis_toplam"] = cur.execute("SELECT COALESCE(SUM(toplam),0) AS s FROM mobil_siparisler WHERE COALESCE(aktif,1)=1").fetchone()["s"] or 0
    rows["irsaliye_toplam"] = cur.execute("SELECT COALESCE(SUM(toplam),0) AS s FROM mobil_irsaliyeler WHERE COALESCE(aktif,1)=1").fetchone()["s"] or 0
    rows["fatura_toplam"] = cur.execute("SELECT COALESCE(SUM(toplam),0) AS s FROM mobil_faturalar WHERE COALESCE(aktif,1)=1").fetchone()["s"] or 0
    rows["tahsilat_toplam"] = cur.execute("SELECT COALESCE(SUM(tutar),0) AS s FROM hareketler WHERE COALESCE(aktif,1)=1 AND UPPER(tip)='TAHSİLAT'").fetchone()["s"] or 0
    rows["bakiye_toplam"] = cur.execute(f"SELECT {bakiye_expr()} AS s FROM hareketler h WHERE COALESCE(h.aktif,1)=1").fetchone()["s"] or 0
    durumlar = {
        "siparis": [dict(r) for r in cur.execute("SELECT COALESCE(durum,'Bekliyor') AS durum, COUNT(*) AS adet, COALESCE(SUM(toplam),0) AS toplam FROM mobil_siparisler WHERE COALESCE(aktif,1)=1 GROUP BY COALESCE(durum,'Bekliyor')").fetchall()],
        "irsaliye": [dict(r) for r in cur.execute("SELECT COALESCE(durum,'Hazırlandı') AS durum, COUNT(*) AS adet, COALESCE(SUM(toplam),0) AS toplam FROM mobil_irsaliyeler WHERE COALESCE(aktif,1)=1 GROUP BY COALESCE(durum,'Hazırlandı')").fetchall()],
        "fatura": [dict(r) for r in cur.execute("SELECT COALESCE(durum,'Kesildi') AS durum, COUNT(*) AS adet, COALESCE(SUM(toplam),0) AS toplam FROM mobil_faturalar WHERE COALESCE(aktif,1)=1 GROUP BY COALESCE(durum,'Kesildi')").fetchall()],
    }
    son_faturalar = [dict(r) for r in cur.execute("""SELECT f.id,('FAT-' || f.id) AS belge_no,f.tarih,f.toplam,f.durum,c.ad AS cari_ad
        FROM mobil_faturalar f LEFT JOIN cariler c ON c.id=f.cari_id
        WHERE COALESCE(f.aktif,1)=1 ORDER BY f.id DESC LIMIT 8""").fetchall()]
    conn.close()
    return {"ozet": rows, "durumlar": durumlar, "son_faturalar": son_faturalar}

@app.get("/bildirimler")
def bildirimler(authorization: str | None = Header(None)):
    check_auth(authorization)
    conn = db()
    cur = conn.cursor()
    items = []
    bekleyen_siparis = cur.execute("SELECT COUNT(*) AS s FROM mobil_siparisler WHERE COALESCE(aktif,1)=1 AND COALESCE(durum,'Bekliyor') IN ('Bekliyor','Onaylandı')").fetchone()["s"] or 0
    bekleyen_irsaliye = cur.execute("SELECT COUNT(*) AS s FROM mobil_irsaliyeler WHERE COALESCE(aktif,1)=1 AND COALESCE(durum,'Hazırlandı') IN ('Hazırlandı','Sevk Edildi')").fetchone()["s"] or 0
    bekleyen_fatura = cur.execute("SELECT COUNT(*) AS s FROM mobil_faturalar WHERE COALESCE(aktif,1)=1 AND COALESCE(durum,'Kesildi') IN ('Kesildi','Tahsilat Bekliyor','Kısmi Tahsilat')").fetchone()["s"] or 0
    dusuk_stok = cur.execute("SELECT COUNT(*) AS s FROM urunler WHERE COALESCE(aktif,1)=1 AND COALESCE(stok,0) <= 5").fetchone()["s"] or 0
    if bekleyen_siparis:
        items.append({"tip":"siparis", "baslik":"Bekleyen sipariş", "mesaj":f"{bekleyen_siparis} sipariş işlem bekliyor.", "seviye":"uyari"})
    if bekleyen_irsaliye:
        items.append({"tip":"irsaliye", "baslik":"Sevk / irsaliye takibi", "mesaj":f"{bekleyen_irsaliye} irsaliye tamamlanmayı bekliyor.", "seviye":"bilgi"})
    if bekleyen_fatura:
        items.append({"tip":"fatura", "baslik":"Tahsilat bekleyen fatura", "mesaj":f"{bekleyen_fatura} fatura tahsilat sürecinde.", "seviye":"uyari"})
    if dusuk_stok:
        items.append({"tip":"stok", "baslik":"Düşük stok", "mesaj":f"{dusuk_stok} ürün kritik stok seviyesinde.", "seviye":"kritik"})
    if not items:
        items.append({"tip":"ok", "baslik":"Her şey yolunda", "mesaj":"Şu anda kritik uyarı bulunmuyor.", "seviye":"basarili"})
    conn.close()
    return {"items": items, "adet": len(items), "time": datetime.now().isoformat()}

@app.get("/senkron/durum")
def senkron_durum(authorization: str | None = Header(None)):
    check_auth(authorization)
    return {"ok": True, "sunucu_saati": datetime.now().isoformat(), "mesaj": "API erişilebilir. Mobil cihaz çevrimdışı kayıtları tekrar bağlanınca gönderebilir."}

@app.get("/canli/kontrol")
def canli_kontrol(authorization: str | None = Header(None)):
    user = check_auth(authorization)
    conn = db()
    cur = conn.cursor()
    tables = ["cariler", "urunler", "mobil_siparisler", "mobil_irsaliyeler", "mobil_faturalar", "firma_ayarlari"]
    counts = {}
    for table in tables:
        try:
            counts[table] = cur.execute(f"SELECT COUNT(*) AS s FROM {_sql_identifier(table)}").fetchone()["s"]
        except Exception:
            counts[table] = None
    firma = cur.execute("SELECT firma_adi, updated_at FROM firma_ayarlari WHERE id=1").fetchone()
    conn.close()
    return {
        "ok": True,
        "paket": "v40 Kararlı Release Candidate",
        "env": API_ENV,
        "local_ip": local_ip(),
        "docs_enabled": not IS_PRODUCTION,
        "service_token_enabled": bool(ALLOW_SERVICE_TOKEN and ADMIN_TOKEN),
        "user": {"kullanici_adi": user.get("kullanici_adi"), "rol": user.get("rol")},
        "firma": dict(firma) if firma else None,
        "tablolar": counts,
        "time": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    uvicorn.run("api.server:app", host=os.environ.get("DAL_ERP_API_HOST", "0.0.0.0"), port=int(os.environ.get("DAL_ERP_API_PORT", "8000")), reload=False)

