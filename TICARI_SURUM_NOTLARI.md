DAL ERP Next v143 - Cari Ekranı UX

# CariTakip Ticari Sürüm Adayı

Bu paket, denemeye almadan önce istenen üretim hazırlıklarını içerir.

## Eklenenler

- Güvenli SQLite yedekleme: çalışan veritabanı düz kopyalanmaz, SQLite backup API kullanılır.
- Eski otomatik yedek temizliği: varsayılan 30 gün.
- PDF rapor altyapısı: cari bakiye ve stok PDF çıktıları için `moduller/rapor_pdf.py`.
- CSV rapor altyapısı korunup genişletilmeye hazır bırakıldı.
- Offline lisans altyapısı: `moduller/lisanslama.py`.
- Offline güncelleme altyapısı: `moduller/guncelleme.py` ve `guncelleme.json`.
- Performans duman testi: `performans_testi.py`.
- Sağlık kontrolü artık temiz DB + güvenli yedek testini beraber yapar.
- EXE üretim yardımcıları: `build_exe.bat`, `main.spec`.
- Kurulum paketi yardımcıları: `build_setup.bat`, `DAL_ERP_Setup.iss`.

## Test komutları

```cmd
cd /d "C:\Users\technopc\OneDrive\Masaüstü\CariTakip"
python proje_saglik_kontrol.py
python performans_testi.py
python main.py
```

## EXE oluşturma

```cmd
cd /d "C:\Users\technopc\OneDrive\Masaüstü\CariTakip"
build_exe.bat
```

## Kurulum paketi

1. `build_exe.bat` ile EXE oluştur.
2. Inno Setup kur.
3. `DAL_ERP_Setup.iss` dosyasını Inno Setup ile aç.
4. Compile düğmesine bas.

## Not

WhatsApp gönderimleri güvenli şekilde tarayıcı bağlantısı açar; WhatsApp şifresi programa kaydedilmez.
SMS/e-fatura için gerçek servis sağlayıcı API bilgisi gerekir. Bu pakette güvenli altyapı hazırdır, canlı API anahtarı gömülü değildir.


## v145 Unified UI
- Dashboard soft sage paleti tüm sayfalara yayıldı.
- Beyaz kalan eski sayfa alanları tema motoruna bağlandı.
- Açık tema genel uygulama yüzeyleri #c0cfca / #eef3f1 / #f7faf9 paletine taşındı.
