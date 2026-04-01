@echo off
echo Starting VIRA AI - Advanced Chatbot System
echo ===========================================
echo 
echo This system includes:
echo - Conversational AI with GPT-4o-mini
echo - RAG System for document processing
echo - Agent System for automation
echo - Voice Processing capabilities
echo - Advanced frontend with React
echo - MongoDB integration
echo 
echo Make sure you have:
echo 1. OpenAI API key in backend/.env
echo 2. Python 3.8+ installed
echo 3. All requirements installed
echo 
echo Starting Backend Server...
echo --------------------------
cd backend
start cmd /k "python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload"
cd ..
timeout /t 3 /nobreak >nul
echo 
echo Starting Frontend Server...
echo ---------------------------
cd frontend
start cmd /k "python -m http.server 3001"
cd ..
echo 
echo System started successfully!
echo 
echo Backend API: http://127.0.0.1:8001
echo Frontend UI: http://127.0.0.1:3001
echo 
echo Opening browser...
start http://127.0.0.1:3001
echo 
echo Press Ctrl+C in the terminal windows to stop the servers
pause