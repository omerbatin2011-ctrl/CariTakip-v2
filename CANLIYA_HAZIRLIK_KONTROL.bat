@echo off
cd /d "%~dp0"
echo CariTakip V40 canliya hazirlik kontrolu basliyor...
python tools\release_check.py
if errorlevel 1 goto hata
echo.
echo V40 kontrol basarili.
pause
exit /b 0
:hata
echo.
echo V40 kontrol hata buldu. Ustteki mesaji kontrol edin.
pause
exit /b 1
