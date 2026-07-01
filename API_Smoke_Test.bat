@echo off
cd /d "%~dp0"
set DAL_ERP_TEST_BASE_URL=http://127.0.0.1:8000
python tools\api_smoke_test.py
pause
