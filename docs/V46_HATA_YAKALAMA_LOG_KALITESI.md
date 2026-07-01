# V46 Hata Yakalama ve Log Kalitesi

Bu sürümde hata/log katmanı güçlendirildi.

- Beklenmeyen hatalara kısa takip kodu eklendi.
- `logs/hata_log.jsonl` ile makine tarafından okunabilir hata kaydı eklendi.
- Şifre, token, bearer token ve IBAN gibi hassas alanlar loga yazılmadan maskeleniyor.
- `tools/error_log_check.py` eklendi.
- `tools/release_check.py` V46 kontrolleriyle güncellendi.

Test komutları:

```powershell
python tools\release_check.py
python tools\error_log_check.py
```
