@echo off
echo Starting Liopleurodon Development Environment...

echo Starting Backend (FastAPI on Port 8000)...
start "Liopleurodon Backend" cmd /k "cd backend && IF EXIST venv\Scripts\activate (call venv\Scripts\activate) && uvicorn main:app --reload --port 8000"

echo Starting Frontend (Next.js on Port 3000)...
start "Liopleurodon Frontend" cmd /k "cd frontend && npm run dev"

echo Both services are starting in separate windows!
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:3000
