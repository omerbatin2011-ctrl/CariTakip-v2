@echo off
cd /d "%~dp0.."
if exist logs\hata_log.txt del logs\hata_log.txt
if exist logs\islem_logu.txt del logs\islem_logu.txt
echo Log dosyalari temizlendi.
pause
