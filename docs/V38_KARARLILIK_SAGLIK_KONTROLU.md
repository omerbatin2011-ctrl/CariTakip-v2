# V38 Kararlılık ve Sağlık Kontrolü

Bu sürümde amaç, uygulamanın uzun süreli kullanımda daha güvenilir davranması ve açılışta riskli ortam problemlerini sessizce loglayabilmesidir.

## Eklenenler

- `moduller/runtime_health.py` eklendi.
- Açılışta klasör, yazma izni, disk alanı, temel bağımlılık ve veritabanı hızlı kontrolü yapılır.
- Kontroller uygulamayı gereksiz yere durdurmaz; uyarılar `logs/islem_logu.txt` içine `SAGLIK` kategorisiyle yazılır.
- Açılış kurtarma yedeği SQLite backup API ile daha tutarlı alınır.
- Beklenmeyen hata penceresinde teknik/hassas detay gösterimi azaltıldı; detaylar log dosyasına bırakıldı.
- `KALITE_KONTROL.bat` daha net hale getirildi.

## Test

```powershell
python main.py
```

Ek kontrol:

```powershell
.\KALITE_KONTROL.bat
```
