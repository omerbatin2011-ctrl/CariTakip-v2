@echo off
cd /d "%~dp0.."
set /p SURUM=Surum etiketi girin (ornek v141): 
if "%SURUM%"=="" (
  echo HATA: Surum bos olamaz.
  pause
  exit /b 1
)
git --version
if errorlevel 1 (
  echo HATA: Git bulunamadi.
  pause
  exit /b 1
)
git add .
git commit -m "%SURUM% kararli surum"
git tag %SURUM%
git status
echo Tamamlandi.
pause
