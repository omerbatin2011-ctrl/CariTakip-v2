# V42-V43-V44 Performans, RAM ve Kod Sadeleştirme

Bu paket V41 üzerine hazırlanmıştır.

## V42 - Startup ve büyük modül yükleme
- Dashboard detay pencereleri uygulama açılışında yüklenmek yerine ihtiyaç anında yüklenir.
- Grafik/rapor/ayar detay ekranlarının ağır bağımlılıkları açılış maliyetinden çıkarıldı.

## V43 - RAM ve tekrar eden hesap azaltma
- Küçük TTL cache eklendi.
- Cari ve stok özet sorguları kısa süreli cache ile korunur.
- Dashboard yenilemelerinde aynı özet verilerin tekrar tekrar hesaplanması azaltıldı.

## V44 - Kod sadeleştirme
- Tablo güncelleme sırasında repaint/sort maliyetini azaltan ortak yardımcı fonksiyon eklendi.
- Dashboard detay tablo kopyalama işlemi ortak güvenli tablo doldurma mantığını kullanır.

## Not
Cache süreleri kısa tutulmuştur. Veri güncelliği ile performans dengesi korunmuştur.
