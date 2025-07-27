#!/usr/bin/env python3
"""
Ultra simple FastAPI test to see if dependencies work
"""
import subprocess
import sys
import os

# Force install FastAPI before doing ANYTHING else
print("🔧 Installing FastAPI...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn"])
print("✅ FastAPI installed")

# Now import and create a simple app
from fastapi import FastAPI

app = FastAPI(title="Test API")

@app.get("/")
def root():
    return {"message": "IT FUCKING WORKS!", "status": "success"}

@app.get("/test")
def test():
    return {"message": "Dependencies are working", "python_version": sys.version}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting simple test API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)