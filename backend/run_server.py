#!/usr/bin/env python3
"""
Simple server runner for VIRA AI backend
"""
import sys
import os

# Add the backend directory to Python path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import and run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8001,
        reload=True
    )