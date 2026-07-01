@echo off
cd /d "%~dp0"
set DAL_ERP_ENV=production
set DAL_ERP_API_HOST=0.0.0.0
set DAL_ERP_API_PORT=8000
set DAL_ERP_ALLOWED_ORIGINS=
set DAL_ERP_ALLOW_SERVICE_TOKEN=0
python -m api.server
pause
