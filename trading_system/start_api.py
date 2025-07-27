#!/usr/bin/env python3
"""
Quick start script for the Trading System API
"""
import os
import sys
import subprocess

def ensure_dependencies():
    """Ensure FastAPI dependencies are installed before importing anything"""
    try:
        import fastapi
        import uvicorn
        print("✅ FastAPI dependencies found")
        return True
    except ImportError:
        print("🔧 Installing missing dependencies...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "fastapi>=0.104.0", "uvicorn>=0.24.0", "aiofiles"
            ])
            print("✅ Dependencies installed")
            # Test import after installation
            import fastapi
            import uvicorn
            return True
        except Exception as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False

# Ensure dependencies before doing ANY imports
if not ensure_dependencies():
    print("❌ Cannot proceed without FastAPI dependencies")
    sys.exit(1)

# Now safely import our API server
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from api_server import app
    import uvicorn
    print("✅ Successfully imported FastAPI app")
except ImportError as e:
    print(f"❌ Failed to import api_server: {e}")
    sys.exit(1)

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
        reload = os.getenv("RAILWAY_ENVIRONMENT_NAME") is None and os.getenv("RENDER") is None
        uvicorn.run(app, host="0.0.0.0", port=port, reload=reload)
    except KeyboardInterrupt:
        print("\n👋 API server stopped")