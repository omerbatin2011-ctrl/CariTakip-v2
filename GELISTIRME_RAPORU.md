DAL ERP Next v143 - Cari Ekranı UX

# CariTakip Geliştirme Raporu

Bu paket, mevcut uygulama yapısı korunarak güvenlik, veri bütünlüğü, migration, yedekleme, rapor dışa aktarma ve sağlık kontrolü alanlarında iyileştirilmiştir.

## Yapılanlar

- Kod içinde görünen sabit admin şifresi kullanılmıyor.
- İlk kurulum/geçici şifre düz metin dosyaya yazılmıyor.
- Kullanıcı ve ana şifreler PBKDF2-SHA256 hash olarak saklanıyor.
- SQLite bağlantılarında `foreign_keys`, `busy_timeout`, `WAL`, `trusted_schema=OFF` korumaları uygulanıyor.
- Temiz kurulumda tablo/indeks sırası test edildi.
- Cari risk limiti, vade günü, cari e-posta/not alanları ve hareket vade tarihi için veri kayıpsız migration eklendi.
- Audit log altyapısı korunup indekslendi.
- Kritik performans indeksleri eklendi.
- Veritabanı bütünlük kontrolü eklendi.
- SQLite backup API ile tutarlı yedekleme fonksiyonu eklendi.
- Eski otomatik yedekleri temizleme fonksiyonu eklendi.
- Cari bakiye, stok ve kasa için CSV dışa aktarma modülü eklendi.
- `proje_saglik_kontrol.py` eklendi: Python sözdizimi ve temiz DB kurulum testi yapar.
- `firma_bilgisi_getir()` içindeki tekrar eden `eposta` satırı temizlendi.

## CMD komutları

Projeyi çalıştırma:

```cmd
cd /d "C:\Users\technopc\OneDrive\Masaüstü\CariTakip"
python main.py
```

Sağlık kontrolü:

```cmd
cd /d "C:\Users\technopc\OneDrive\Masaüstü\CariTakip"
python proje_saglik_kontrol.py
```

CSV rapor üretme örneği:

```cmd
cd /d "C:\Users\technopc\OneDrive\Masaüstü\CariTakip"
python -c "from moduller.db import db_ayarla; from core.config import DB_ADI; db_ayarla(DB_ADI); from moduller.rapor_disari_aktar import cari_bakiye_csv; print(cari_bakiye_csv())"
```

## Not

PySide6 bu ortamda kurulu olmadığı için gerçek GUI açılış testi yapılamadı. Ancak Python sözdizimi ve temiz veritabanı kurulum testi başarıyla geçti.


## v137 - ERP Widget Library 1.0

- Ortak ERP widget kütüphanesi genişletildi.
- `ERPToolButton`, `ERPLineEdit`, `ERPComboBox`, `ERPDateEdit`, `ERPForm`, `ERPDialog`, `ERPStatusBar` eklendi.
- `widgets/__init__.py` yeni bileşenleri dışa aktaracak şekilde güncellendi.
- `main.py` ve mevcut sayfa uyumluluğu korundu.


## v138 - Design System 1.0
- Ölçü, spacing, radius ve tema renkleri tek merkezde toplandı.
- `widgets/design_system.py` v138 token sistemi oldu.
- `widgets/theme_styles.py` ile QSS üretici eklendi.
- ERP Widget Library token sistemini kullanacak şekilde güncellendi.


## v145 Unified UI
- Dashboard soft sage paleti tüm sayfalara yayıldı.
- Beyaz kalan eski sayfa alanları tema motoruna bağlandı.
- Açık tema genel uygulama yüzeyleri #c0cfca / #eef3f1 / #f7faf9 paletine taşındı.
