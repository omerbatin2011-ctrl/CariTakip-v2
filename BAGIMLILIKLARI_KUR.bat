@echo off
cd /d "%~dp0"
echo DAL ERP / CariTakip bagimlilik kurulumu basliyor...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo Kurulum tamamlandi. Programi baslatmak icin: python main.py
pause
