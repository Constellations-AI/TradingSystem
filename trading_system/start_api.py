#!/usr/bin/env python3
"""
Quick start script for the Trading System API
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api_server import app
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Trading System API...")
    print("📊 React frontend should connect to: http://localhost:8000")
    print("📝 API docs at: http://localhost:8000/docs")
    print("💡 Test endpoints:")
    print("   - http://localhost:8000/api/traders")
    print("   - http://localhost:8000/api/market/SPY")
    print("   - http://localhost:8000/api/traders/warren/portfolio")
    print("   - http://localhost:8000/api/summary")
    print("")
    
    try:
        # Fix the reload warning by using string import
        uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        print("\n👋 API server stopped")