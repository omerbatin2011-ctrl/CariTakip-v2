# V47 Büyük Veri ve Profil Kontrolü

Bu sürüm Faz 1 ve Faz 2 için güvenli ölçüm araçları ekler.

## Eklenen araçlar

- `tools/big_data_performance_test.py`
  - Gerçek veritabanına dokunmaz.
  - DB'yi geçici klasöre kopyalar.
  - Test kayıtlarını kopya DB üzerinde üretir.
  - Arama, dashboard toplamları ve hareket özetlerini ölçer.

- `tools/runtime_profile_check.py`
  - Kritik modüllerin import süresi ve bellek tepe değerini ölçer.
  - Açılış yavaşlığına sebep olabilecek modülleri raporlar.

## Önerilen kullanım

Hızlı test:

```powershell
python tools\big_data_performance_test.py --quick
python tools\runtime_profile_check.py
```

Daha büyük test:

```powershell
python tools\big_data_performance_test.py --cariler 100000 --urunler 100000 --hareketler 1000000
```

Raporlar `logs/` klasörüne yazılır.
