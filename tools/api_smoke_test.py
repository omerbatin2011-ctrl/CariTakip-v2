from __future__ import annotations

import getpass
import json
import os
import urllib.error
import urllib.request

BASE_URL = os.environ.get("DAL_ERP_TEST_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def request_json(path: str, method: str = "GET", payload: dict | None = None, token: str | None = None) -> dict:
    data = None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(BASE_URL + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} {path}: {body}")
    except Exception as exc:
        raise SystemExit(f"Bağlantı hatası {path}: {exc}")


def main() -> int:
    print(f"DAL ERP API Smoke Test: {BASE_URL}")
    print("1) Health kontrolü")
    print(json.dumps(request_json("/health"), ensure_ascii=False, indent=2))

    username = input("API kullanıcı adı [admin]: ").strip() or "admin"
    password = getpass.getpass("API şifre: ")
    login = request_json("/login", "POST", {"kullanici_adi": username, "sifre": password})
    token = login.get("token")
    if not token:
        raise SystemExit("Login başarılı görünmedi; token alınamadı.")
    print(f"2) Login OK: {login.get('kullanici_adi')} / {login.get('rol')}")

    for title, path in [
        ("Canlı kontrol", "/canli/kontrol"),
        ("Dashboard", "/dashboard"),
        ("Firma", "/firma"),
        ("Rapor özeti", "/raporlar/ozet"),
    ]:
        print(f"3) {title}")
        data = request_json(path, token=token)
        print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
    print("OK: Temel API akışı çalışıyor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
