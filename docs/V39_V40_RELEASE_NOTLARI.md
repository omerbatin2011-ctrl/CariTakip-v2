# V39 + V40 Kararlılık, Bakım ve Release Candidate

Bu paket V39 ve V40 adımlarını birlikte içerir.

## V39 Bakım Kolaylığı

- Geçici Python cache dosyaları temizlendi.
- Release öncesi kontrol aracı eklendi: `tools/release_check.py`.
- Tek komutluk kontrol dosyası eklendi: `CANLIYA_HAZIRLIK_KONTROL.bat`.
- Kritik modüller için import kontrolü eklendi.
- Log boyutu, yazma izni ve SQLite bütünlük kontrolleri tek raporda toplandı.

## V40 Release Candidate

- Açılış sağlık kontrolü JSON raporu üretir: `logs/saglik_raporu.json`.
- Canlıya hazırlık kontrolü JSON raporu üretir: `logs/release_check_v40.json`.
- API canlı kontrol paket adı V40 seviyesine güncellendi.
- Uygulamayı durdurmadan teşhis etmeye yarayan kontroller güçlendirildi.

## Test

Masaüstü uygulaması:

```powershell
Set-Location "C:\Users\dalel\Downloads\CariTakip_v40_release_candidate\CariTakip"
python main.py
```

Canlıya hazırlık kontrolü:

```powershell
Set-Location "C:\Users\dalel\Downloads\CariTakip_v40_release_candidate\CariTakip"
python tools\release_check.py
```

veya çift tık:

```text
CANLIYA_HAZIRLIK_KONTROL.bat
```
