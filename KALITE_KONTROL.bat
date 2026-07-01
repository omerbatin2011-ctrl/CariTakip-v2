@echo off
cd /d "%~dp0"
echo [1/3] Python soz dizimi kontrolu...
python -m compileall -q -x "yedekler|logs|build|dist" .
if errorlevel 1 goto hata

echo [2/3] Ruff kalite kontrolu...
python -m ruff check .
if errorlevel 1 goto hata

echo [3/3] Bagimlilik kontrolu...
python -m pip check
if errorlevel 1 goto hata

echo.
echo Kalite kontrol basarili.
pause
exit /b 0

:hata
echo.
echo Kalite kontrol hata buldu. Yukaridaki mesaji kontrol edin.
pause
exit /b 1
