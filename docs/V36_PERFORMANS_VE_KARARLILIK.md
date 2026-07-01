# V36 Performans ve Kararlılık Notları

Bu sürümde çalışan akışı bozmadan güvenli performans/kararlılık iyileştirmeleri yapıldı.

## Yapılanlar

- Log dosyaları için otomatik döndürme eklendi. Loglar büyüyüp diski şişirmez.
- Açılış kurtarma yedeği varsayılan olarak günde bir kez oluşturulur. Böylece her açılışta gereksiz DB kopyalama azalır.
- İstenirse `DAL_ERP_HER_ACILISTA_YEDEK=1` ile eski davranış açılabilir.
- Mobil API SQLite bağlantılarına `timeout`, `busy_timeout`, `foreign_keys`, WAL ve temp memory ayarları eklendi.
- Mobil sipariş/irsaliye/fatura listeleri için aktif-durum-tarih indeksleri eklendi.
- API başarısız giriş hafızası periyodik temizlenir; API uzun açık kaldığında bellek şişmez.
- Tekrarlanan ürün aktif/ad indeksi kaldırıldı.

## Test

- Python sözdizimi kontrolü başarılı.
- Ana uygulama test komutu: `python main.py`
