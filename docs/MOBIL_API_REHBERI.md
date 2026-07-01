# DAL ERP Next Mobil API v1

Bu sürüm masaüstü programa aynı Wi‑Fi içinden mobil bağlantı altyapısı ekler.

## Kurulum

1. `Mobil_API_Kurulum.bat` dosyasını çalıştırın.
2. Programı normal şekilde açın: `py main.py`
3. Giriş yaptıktan sonra API arka planda açılır.
4. Test için bilgisayarda şu adresi açın:
   - `http://127.0.0.1:8000/docs`

## Telefon bağlantısı

Telefon ve bilgisayar aynı Wi‑Fi ağında olmalı.

Bilgisayar IP adresini öğrenmek için CMD:

```cmd
ipconfig
```

Örnek telefon adresi:

```text
http://192.168.1.25:8000/docs
```

Windows Güvenlik Duvarı sorarsa Python için özel ağ izni verin.

## Uç Noktalar

- `POST /login` kullanıcı adı/şifre ile token alır.
- `GET /dashboard` mobil özet verir.
- `GET /cariler?q=ahmet` cari arar.
- `GET /cariler/{id}` cari detay/bakiye verir.
- `GET /cariler/{id}/hareketler` cari hareketlerini verir.
- `POST /tahsilat` mobil tahsilat ekler.
- `GET /stoklar?q=urun` stok arar.
- `GET /hareketler` son hareketleri verir.

## Login örneği

```json
{
  "kullanici_adi": "admin",
  "sifre": "şifreniz"
}
```

Dönen `token`, diğer isteklerde header olarak gönderilir:

```text
Authorization: Bearer TOKEN_BURAYA
```

## Güvenlik notu

Bu ilk sürüm aynı Wi‑Fi içindir. İnternete açmadan önce HTTPS, sabit token politikası, modem/port güvenliği ve kullanıcı yetki kontrolü ayrıca sıkılaştırılmalıdır.
