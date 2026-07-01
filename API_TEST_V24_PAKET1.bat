@echo off
chcp 65001 >nul
set API=http://127.0.0.1:8000
set TOKEN=admin-token

echo === DAL ERP v24 Paket 1 API Test ===
echo API ayri pencerede calisiyor olmali: python -m api.server
echo.

echo 1) Health
curl %API%/health
echo.
echo.

echo 2) Dashboard
curl -H "Authorization: Bearer %TOKEN%" %API%/dashboard
echo.
echo.

echo 3) Siparisler
curl -H "Authorization: Bearer %TOKEN%" %API%/siparisler
echo.
echo.

echo 4) Irsaliyeler
curl -H "Authorization: Bearer %TOKEN%" %API%/irsaliyeler
echo.
echo.

echo 5) Faturalar
curl -H "Authorization: Bearer %TOKEN%" %API%/faturalar
echo.
echo.

echo 6) Siparis zinciri ornek: /siparisler/1/zincir
curl -H "Authorization: Bearer %TOKEN%" %API%/siparisler/1/zincir
echo.
echo.

pause
