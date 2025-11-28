@echo off
REM QA-Brain 启动脚本 (Windows)

echo 🚀 Starting QA-Brain...

REM 启动后端
echo 📦 Starting Backend...
start "QA-Brain Backend" cmd /k "cd backend && python main.py"

REM 等待后端启动
timeout /t 3 /nobreak >nul

REM 启动前端
echo 🎨 Starting Frontend...
start "QA-Brain Frontend" cmd /k "cd frontend && npm run dev"

echo ✅ QA-Brain is running!
echo    Backend:  http://localhost:8000
echo    Frontend: http://localhost:1314
echo.
echo Press any key to exit...
pause >nul

