@echo off
chcp 65001 >nul
cd /d "%~dp0.."

echo DAL ERP Git ilk kurulum başlıyor...

git --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo HATA: Git bulunamadı.
    echo Git for Windows kurulduktan sonra CMD'yi kapatıp tekrar açın.
    pause
    exit /b 1
)

if not exist .git (
    git init
)

git add .
git commit -m "v130 git hazir kararlı sürüm"
git tag v130

echo.
echo Tamamlandı. Durum:
git status
pause
