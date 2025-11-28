#!/bin/bash

# QA-Brain 启动脚本

echo "🚀 Starting QA-Brain..."

# 检查 Python 环境
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.13+"
    exit 1
fi

# 检查 Node.js 环境
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi

# 启动后端
echo "📦 Starting Backend..."
cd backend
python main.py &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 3

# 启动前端
echo "🎨 Starting Frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ QA-Brain is running!"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:1314"
echo ""
echo "Press Ctrl+C to stop all services"

# 捕获 Ctrl+C 信号
trap "echo '🛑 Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT

# 等待进程
wait

