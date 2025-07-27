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
    # Use Railway's PORT environment variable, fallback to 8000
    port = int(os.getenv("PORT", 8000))
    
    print("🚀 Starting Trading System API...")
    print(f"📊 React frontend should connect to: http://localhost:{port}")
    print(f"📝 API docs at: http://localhost:{port}/docs")
    print("💡 Test endpoints:")
    print(f"   - http://localhost:{port}/api/traders")
    print(f"   - http://localhost:{port}/api/market/SPY")
    print(f"   - http://localhost:{port}/api/traders/warren/portfolio")
    print(f"   - http://localhost:{port}/api/summary")
    print("")
    
    try:
        # Don't use reload in production
        reload = os.getenv("RAILWAY_ENVIRONMENT_NAME") is None
        uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=reload)
    except KeyboardInterrupt:
        print("\n👋 API server stopped")