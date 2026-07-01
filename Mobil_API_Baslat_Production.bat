@echo off
cd /d "%~dp0"
set DAL_ERP_ENV=production
set DAL_ERP_API_HOST=0.0.0.0
set DAL_ERP_API_PORT=8000
REM Guvenlik icin bu tokeni degistir. Ornek:
REM set DAL_ERP_ADMIN_TOKEN=buraya-uzun-rastgele-token
if "%DAL_ERP_ADMIN_TOKEN%"=="" (
  echo HATA: Production modunda DAL_ERP_ADMIN_TOKEN zorunludur.
  echo Ornek: set DAL_ERP_ADMIN_TOKEN=uzun-rastgele-token
  pause
  exit /b 1
)
python -m api.server
pause
