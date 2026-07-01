@echo off
cd /d "%~dp0"
set DAL_ERP_ENV=development
set DAL_ERP_API_HOST=0.0.0.0
set DAL_ERP_API_PORT=8000
set DAL_ERP_ALLOWED_ORIGINS=http://localhost:5000,http://127.0.0.1:5000,http://localhost:3000,http://127.0.0.1:3000
set DAL_ERP_ALLOW_SERVICE_TOKEN=0
python -m api.server
pause
