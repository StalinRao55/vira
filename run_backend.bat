@echo off
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload