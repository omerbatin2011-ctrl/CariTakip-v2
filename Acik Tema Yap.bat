@echo off
reg delete "HKCU\Software\DAL\DAL ERP" /v "tema/koyu" /f >nul 2>nul
echo Tema ayari sifirlandi. Program acik tema ile baslayacak.
pause
