DAL ERP Next v144 - Cari Ekranı UX

# DAL ERP Next / CariTakip

Modern PyQt tabanlı cari takip ve ERP dönüşüm projesi.

## Çalıştırma

```cmd
cd /d "C:\Users\technopc\OneDrive\Masaüstü\CariTakip"
py main.py
```

## Git ile ilk kayıt

Git kurulduktan sonra:

```cmd
git init
git add .
git commit -m "v130 git hazir kararlı sürüm"
git tag v130
```

## Önemli not

`.gitignore` içinde veritabanı dosyaları (`*.db`) bilinçli olarak hariç tutuldu. Gerçek müşteri/cari verisi GitHub'a gönderilmemeli.

Geliştirme yaparken örnek veri gerekiyorsa ayrı bir `sample.db` veya `demo.db` dosyası kullanılabilir.

## Sürüm

Mevcut temel sürüm: `v130`


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


## v142 Kalite Araçları

- `Saglik Kontrol.bat`: Proje sağlık kontrolünü çalıştırır.
- `scripts/yeni_surumu_kaydet.bat`: Çalışan sürümü Git ile kaydeder ve etiketler.
- `scripts/log_temizle.bat`: Hata ve işlem loglarını temizler.



## v145 Unified UI
- Dashboard soft sage paleti tüm sayfalara yayıldı.
- Beyaz kalan eski sayfa alanları tema motoruna bağlandı.
- Açık tema genel uygulama yüzeyleri #c0cfca / #eef3f1 / #f7faf9 paletine taşındı.
