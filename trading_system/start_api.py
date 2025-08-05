#!/usr/bin/env python3
"""
Quick start script for the Trading System API
Version 2.0 - Fixed dependency installation
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
    
    # Start trading floor in background if in production
    # Railway sets different environment variables: RAILWAY_ENVIRONMENT, RAILWAY_PROJECT_ID, etc.
    is_railway = any([
        os.getenv("RAILWAY_ENVIRONMENT_NAME"),
        os.getenv("RAILWAY_ENVIRONMENT"), 
        os.getenv("RAILWAY_PROJECT_ID"),
        os.getenv("RAILWAY_SERVICE_ID")
    ])
    is_render = os.getenv("RENDER")
    is_production = is_railway or is_render
    
    # Also allow manual override for testing
    force_trading = os.getenv("FORCE_TRADING_FLOOR", "").lower() in ["true", "1", "yes"]
    
    print(f"🔍 Environment detection:")
    print(f"   - Railway: {is_railway}")
    print(f"   - Render: {is_render}")  
    print(f"   - Force trading: {force_trading}")
    print(f"   - Will start trading floor: {is_production or force_trading}")
    
    if is_production or force_trading:
        print("🏢 Starting trading agents in background...")
        import threading
        import asyncio
        
        def run_trading_floor():
            import time
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    print(f"🔄 Trading floor startup attempt {retry_count + 1}/{max_retries}")
                    print("🔄 Importing trading floor...")
                    import trading_floor
                    print("📊 Trading floor imported successfully")
                    print("🚀 Starting trading floor main loop...")
                    asyncio.run(trading_floor.run_trading_floor())
                    break  # If we get here, trading floor exited normally
                except ImportError as e:
                    print(f"❌ Import error in trading floor: {e}")
                    import traceback
                    print(f"❌ Import traceback: {traceback.format_exc()}")
                    retry_count += 1
                except KeyboardInterrupt:
                    print("🛑 Trading floor stopped by user")
                    break
                except Exception as e:
                    print(f"❌ Trading floor runtime error: {e}")
                    import traceback
                    print(f"❌ Runtime traceback: {traceback.format_exc()}")
                    retry_count += 1
                    
                    if retry_count < max_retries:
                        print(f"🔄 Retrying in 30 seconds... ({retry_count}/{max_retries})")
                        time.sleep(30)
                    else:
                        print("❌ Max retries reached, trading floor disabled")
                        break
        
        # Start trading floor in a separate thread
        print("🧵 Creating trading thread...")
        trading_thread = threading.Thread(target=run_trading_floor, daemon=True)
        trading_thread.start()
        print("✅ Trading thread started, agents should be initializing...")
    
    try:
        # Don't use reload in production
        reload = os.getenv("RAILWAY_ENVIRONMENT_NAME") is None and os.getenv("RENDER") is None
        uvicorn.run(app, host="0.0.0.0", port=port, reload=reload)
    except KeyboardInterrupt:
        print("\n👋 API server stopped")