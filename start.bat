@echo off
title Stock Agent Launcher
echo ============================================
echo         Stock Agent - Startup
echo ============================================
echo.

cd /d "%~dp0application"

echo [1/2] Checking FastAPI backend on port 8000...
netstat -ano -p TCP | findstr /R /C:":8000 .*LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo     Backend is already running on port 8000. Reusing existing server.
) else (
    echo     Starting FastAPI backend on port 8000...
    start "Stock Agent - Backend (keep open)" cmd /k "python -m uvicorn main:app --port 8000"
    echo     Waiting 20 seconds for backend to initialize...
    timeout /t 20 /nobreak > nul
)

echo [2/2] Checking Streamlit frontend on port 8501...
netstat -ano -p TCP | findstr /R /C:":8501 .*LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo     Frontend is already running on port 8501. Reusing existing server.
) else (
    echo     Starting Streamlit frontend on port 8501...
    start "Stock Agent - Frontend (keep open)" cmd /k "python -m streamlit run app.py --server.port 8501 --server.headless true"
    echo     Waiting 8 seconds for frontend to initialize...
    timeout /t 8 /nobreak > nul
)

echo.
echo ============================================
echo  Both servers are running!
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:8501
echo ============================================
echo.
echo  Opening browser...
start http://localhost:8501

echo  You can close this window.
echo  Keep the other two terminal windows OPEN.
timeout /t 5 /nobreak > nul
