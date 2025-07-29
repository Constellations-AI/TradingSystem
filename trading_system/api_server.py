#!/usr/bin/env python3
"""
FastAPI server to serve trading data to React frontend
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from accounts import get_trader_account
from data.polygon import PolygonClient
from datetime import datetime, timedelta
import requests
import os
from typing import Dict, List, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Trading System API", version="1.0.0")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080", 
        "http://localhost:8081", 
        "http://localhost:3000",
        "https://www.constellationsai.com",
        "https://constellationsai.com"
    ],  # React dev servers + production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Keys from environment
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

# Initialize Polygon client
try:
    polygon_client = PolygonClient()
    logger.info("✅ Polygon client initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Polygon client: {e}")
    polygon_client = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Trading System API is running", "timestamp": datetime.now().isoformat()}

@app.get("/debug/environment")
async def debug_environment():
    """Debug endpoint to check environment variables"""
    import os
    
    env_vars = {
        "RAILWAY_ENVIRONMENT_NAME": os.getenv("RAILWAY_ENVIRONMENT_NAME"),
        "RENDER": os.getenv("RENDER"),
        "PORT": os.getenv("PORT"),
        "DATABASE_URL": "***" if os.getenv("DATABASE_URL") else None,
        "POLYGON_API_KEY": "***" if os.getenv("POLYGON_API_KEY") else None,
        "OPENAI_API_KEY": "***" if os.getenv("OPENAI_API_KEY") else None,
        "ALPHAVANTAGE_API_KEY": "***" if os.getenv("ALPHAVANTAGE_API_KEY") else None,
        "working_directory": os.getcwd(),
    }
    
    return {
        "environment_variables": env_vars,
        "should_start_trading": bool(os.getenv("RAILWAY_ENVIRONMENT_NAME") or os.getenv("RENDER")),
        "all_env_keys": [k for k in os.environ.keys() if "RAILWAY" in k or "RENDER" in k]
    }

@app.get("/debug/database")
async def debug_database():
    """Debug endpoint to check database status"""
    import os
    from database import Database
    from db_config import DATABASE_PATH
    
    # Use our Database class to check status
    try:
        db = Database(DATABASE_PATH)
        database_type = "PostgreSQL" if db.use_postgresql else "SQLite"
        database_url_present = bool(db.database_url)
        
        # Check tables and row counts
        tables_info = {}
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get all tables (different query for PostgreSQL vs SQLite)
                if db.use_postgresql:
                    cursor.execute("""
                        SELECT table_name FROM information_schema.tables 
                        WHERE table_schema = 'public'
                    """)
                else:
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
            
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    tables_info[table_name] = count
                    
        except Exception as e:
            tables_info["error"] = str(e)
    
        # Also check trader_accounts data
        trader_data = {}
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                if db.use_postgresql:
                    cursor.execute("SELECT trader_name, balance, holdings FROM trader_accounts")
                else:
                    cursor.execute("SELECT trader_name, balance, holdings FROM trader_accounts")
                rows = cursor.fetchall()
                for row in rows:
                    trader_data[row[0]] = {"balance": row[1], "holdings": row[2]}
        except Exception as e:
            trader_data["error"] = str(e)
        
        return {
            "database_type": database_type,
            "database_url_present": database_url_present,
            "database_path": DATABASE_PATH,
            "working_directory": os.getcwd(),
            "tables": tables_info,
            "trader_data": trader_data
        }
    except Exception as e:
        return {
            "error": str(e),
            "database_type": "Unknown",
            "database_url_present": False
        }

@app.get("/api/traders")
async def get_traders():
    """Get list of all traders"""
    return {
        "traders": [
            {"id": 1, "name": "warren", "display_name": "Warren", "color": "trading-blue"},
            {"id": 4, "name": "camillo", "display_name": "Camillo", "color": "trading-yellow"},
            {"id": 3, "name": "flash", "display_name": "Flash", "color": "trading-purple"}
        ]
    }

@app.get("/debug/traders/{trader_name}/raw")
async def get_trader_raw_data(trader_name: str):
    """Debug endpoint to see raw account data without price filtering"""
    try:
        account = get_trader_account(trader_name.lower())
        return {
            "name": account.name,
            "balance": account.balance,
            "raw_holdings": dict(account.holdings),
            "transaction_count": len(account.transactions),
            "last_transaction": account.transactions[-1].model_dump() if account.transactions else None,
            "portfolio_history_count": len(account.portfolio_value_time_series)
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug/traders/{trader_name}/raw")
async def get_trader_raw_data(trader_name: str):
    """Debug endpoint to see raw account data"""
    try:
        account = get_trader_account(trader_name.lower())
        return {
            "name": account.name,
            "balance": account.balance,
            "raw_holdings": dict(account.holdings),
            "transaction_count": len(account.transactions),
            "last_transaction": account.transactions[-1].model_dump() if account.transactions else None,
            "portfolio_history_count": len(account.portfolio_value_time_series)
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug/test-save/{trader_name}")
async def test_save_data(trader_name: str):
    """Test saving and immediately retrieving data"""
    try:
        from accounts import get_trader_account
        
        # Get account
        account = get_trader_account(trader_name.lower())
        original_balance = account.balance
        
        # Modify it slightly
        account.balance = account.balance - 1.0
        
        # Save it
        account.save()
        
        # Load a fresh copy
        fresh_account = get_trader_account(trader_name.lower())
        
        return {
            "original_balance": original_balance,
            "modified_balance": account.balance,
            "fresh_account_balance": fresh_account.balance,
            "save_worked": fresh_account.balance == account.balance
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/traders/{trader_name}/portfolio")
async def get_trader_portfolio(trader_name: str):
    """Get trader's current portfolio"""
    try:
        account = get_trader_account(trader_name.lower())
        
        # Calculate current portfolio value
        portfolio_value = account.calculate_portfolio_value()
        
        # Format holdings for frontend
        holdings = []
        for symbol, quantity in account.holdings.items():
            # Get ONLY real current prices - no mock data ever
            from accounts import get_current_price
            current_price = get_current_price(symbol)
            
            if current_price == 0:
                logger.error(f"❌ Failed to get real price for {symbol} - API failure")
                # Don't add this holding to the response rather than show fake data
                continue
            
            market_value = quantity * current_price
            
            holdings.append({
                "symbol": symbol,
                "quantity": quantity,
                "current_price": current_price,
                "market_value": market_value
            })
        
        return {
            "trader_name": trader_name,
            "portfolio_value": portfolio_value,
            "cash_balance": account.balance,
            "holdings": holdings,
            "total_trades": len(account.transactions)
        }
    
    except Exception as e:
        logger.error(f"Error getting portfolio for {trader_name}: {e}")
        raise HTTPException(status_code=404, detail=f"Trader {trader_name} not found")

@app.get("/api/traders/{trader_name}/performance")
async def get_trader_performance(trader_name: str):
    """Get trader's performance history"""
    try:
        account = get_trader_account(trader_name.lower())
        
        # Get portfolio value time series
        performance_data = []
        for timestamp, value in account.portfolio_value_time_series:
            performance_data.append({
                "timestamp": timestamp,
                "portfolio_value": value,
                "date": timestamp.split()[0] if isinstance(timestamp, str) else timestamp
            })
        
        # Calculate P&L from starting value
        starting_value = 10000  # Default starting value
        current_value = account.calculate_portfolio_value()
        total_pnl = current_value - starting_value
        total_return = (total_pnl / starting_value) * 100 if starting_value > 0 else 0
        
        return {
            "trader_name": trader_name,
            "current_value": current_value,
            "starting_value": starting_value,
            "total_pnl": total_pnl,
            "total_return": total_return,
            "performance_history": performance_data
        }
    
    except Exception as e:
        logger.error(f"Error getting performance for {trader_name}: {e}")
        raise HTTPException(status_code=404, detail=f"Trader {trader_name} not found")

@app.get("/api/traders/{trader_name}/trades")
async def get_trader_trades(trader_name: str, limit: int = 50):
    """Get trader's trading history"""
    try:
        account = get_trader_account(trader_name.lower())
        
        # Format trades for frontend
        trades = []
        for trade in account.transactions[-limit:]:  # Get last N trades
            # Trade is a Transaction object, not a dict
            trades.append({
                "timestamp": trade.timestamp,
                "symbol": trade.symbol,
                "side": "BUY" if trade.quantity > 0 else "SELL",
                "quantity": abs(trade.quantity),
                "price": trade.price,
                "total": trade.total(),
                "reasoning": trade.rationale,
                "status": "FILLED"  # Assume all historical trades are filled
            })
        
        # Sort by timestamp (newest first)
        trades.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "trader_name": trader_name,
            "trades": trades,
            "total_count": len(account.transactions)
        }
    
    except Exception as e:
        logger.error(f"Error getting trades for {trader_name}: {e}")
        raise HTTPException(status_code=404, detail=f"Trader {trader_name} not found")

@app.get("/api/market/{symbol}")
async def get_market_data(symbol: str, timeframe: str = "day", limit: int = 30):
    """Get real market data for candlestick chart"""
    if not polygon_client:
        raise HTTPException(status_code=503, detail="Market data service unavailable")
    
    try:
        logger.info(f"📊 Fetching market data for {symbol}")
        
        # Get aggregated data from Polygon
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=limit + 10)  # Add buffer for weekends/holidays
        
        from_date = start_date.strftime("%Y-%m-%d")
        to_date = end_date.strftime("%Y-%m-%d")
        
        # Fetch real market data
        polygon_data = polygon_client.get_aggregates(
            ticker=symbol.upper(),
            timespan=timeframe,
            from_date=from_date,
            to_date=to_date,
            limit=limit
        )
        
        # Transform Polygon data to our format
        market_data = []
        if polygon_data.get("results"):
            for candle in polygon_data["results"][-limit:]:  # Take last N candles
                # Polygon timestamps are in milliseconds
                timestamp_ms = candle.get("t", 0)
                date = datetime.fromtimestamp(timestamp_ms / 1000)
                
                market_data.append({
                    "timestamp": date.isoformat(),
                    "date": date.strftime("%Y-%m-%d"),
                    "time": date.strftime("%b %d"),  # For chart display
                    "open": round(candle.get("o", 0), 2),
                    "high": round(candle.get("h", 0), 2),
                    "low": round(candle.get("l", 0), 2),
                    "close": round(candle.get("c", 0), 2),
                    "volume": int(candle.get("v", 0))
                })
        
        if not market_data:
            logger.warning(f"No market data returned for {symbol}")
            # Fallback to mock data if no real data available
            return await _get_mock_market_data(symbol, limit)
        
        logger.info(f"✅ Returned {len(market_data)} candles for {symbol}")
        
        return {
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "data": market_data,
            "count": len(market_data)
        }
    
    except Exception as e:
        logger.error(f"Error getting market data for {symbol}: {e}")
        logger.info(f"🔄 Falling back to mock data for {symbol}")
        # Fallback to mock data if API fails
        return await _get_mock_market_data(symbol, limit)

async def _get_mock_market_data(symbol: str, limit: int = 30):
    """Fallback mock market data"""
    mock_data = []
    base_price = {"SPY": 450, "AAPL": 180, "TSLA": 250, "NVDA": 140}.get(symbol, 150)
    
    for i in range(limit):
        date = datetime.now() - timedelta(days=limit-i-1)
        
        # Generate realistic OHLCV data
        open_price = base_price + (i * 0.5) + (i % 3 - 1) * 2
        high_price = open_price * (1 + 0.02)
        low_price = open_price * (1 - 0.015)
        close_price = open_price + ((high_price - low_price) * 0.3)
        volume = 1000000 + (i * 10000)
        
        mock_data.append({
            "timestamp": date.isoformat(),
            "date": date.strftime("%Y-%m-%d"),
            "time": date.strftime("%b %d"),
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": int(volume)
        })
    
    return {
        "symbol": symbol.upper(),
        "timeframe": "day",
        "data": mock_data,
        "count": len(mock_data),
        "is_mock": True
    }

@app.get("/api/summary")
async def get_trading_summary():
    """Get overall trading system summary"""
    try:
        traders = ["warren", "camillo", "flash"]
        summary = {
            "total_portfolio_value": 0,
            "total_traders": len(traders),
            "trader_summaries": []
        }
        
        for trader_name in traders:
            try:
                account = get_trader_account(trader_name)
                portfolio_value = account.calculate_portfolio_value()
                summary["total_portfolio_value"] += portfolio_value
                
                summary["trader_summaries"].append({
                    "name": trader_name,
                    "portfolio_value": portfolio_value,
                    "holdings_count": len(account.holdings),
                    "trades_count": len(account.transactions)
                })
            except Exception as e:
                logger.warning(f"Could not get summary for {trader_name}: {e}")
        
        return summary
    
    except Exception as e:
        logger.error(f"Error getting trading summary: {e}")
        raise HTTPException(status_code=500, detail="Error generating trading summary")

@app.get("/api/system/performance")
async def get_system_performance():
    """Get comprehensive system performance metrics"""
    try:
        from database import Database
        from db_config import DATABASE_PATH
        from datetime import datetime, timedelta
        
        # Get database instance
        db = Database(DATABASE_PATH)
        
        # Calculate time periods
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        hour_ago = now - timedelta(hours=1)
        
        performance_data = {
            "timestamp": now.isoformat(),
            "database_type": "PostgreSQL" if db.use_postgresql else "SQLite",
            "traders": {},
            "system_metrics": {
                "total_traders": 0,
                "active_traders_today": 0,
                "total_trades_today": 0,
                "total_portfolio_value": 0,
                "total_pnl": 0,
                "average_pnl": 0
            }
        }
        
        # Get detailed trader performance
        traders = ["warren", "camillo", "flash"]
        active_today = 0
        total_trades_today = 0
        total_portfolio = 0
        total_pnl = 0
        
        for trader_name in traders:
            try:
                account = get_trader_account(trader_name)
                portfolio_value = account.calculate_portfolio_value()
                pnl = portfolio_value - 10000  # Starting balance
                
                # Count trades today
                trades_today = sum(1 for tx in account.transactions 
                                 if tx.timestamp.startswith(today_start.strftime("%Y-%m-%d")))
                
                # Recent activity (last hour)
                recent_updates = [update for update in account.portfolio_value_time_series 
                                if len(update) >= 2 and update[0] >= hour_ago.strftime("%Y-%m-%d %H:%M:%S")]
                
                # Latest transaction
                last_trade = None
                if account.transactions:
                    last_tx = account.transactions[-1]
                    last_trade = {
                        "symbol": last_tx.symbol,
                        "quantity": last_tx.quantity,
                        "price": last_tx.price,
                        "timestamp": last_tx.timestamp,
                        "side": "BUY" if last_tx.quantity > 0 else "SELL"
                    }
                
                trader_data = {
                    "portfolio_value": round(portfolio_value, 2),
                    "cash_balance": round(account.balance, 2),
                    "pnl": round(pnl, 2),
                    "pnl_percent": round((pnl / 10000) * 100, 2),
                    "holdings": dict(account.holdings),
                    "total_trades": len(account.transactions),
                    "trades_today": trades_today,
                    "recent_updates_count": len(recent_updates),
                    "last_trade": last_trade,
                    "is_active_today": trades_today > 0
                }
                
                performance_data["traders"][trader_name] = trader_data
                
                # Aggregate metrics
                if trades_today > 0:
                    active_today += 1
                total_trades_today += trades_today
                total_portfolio += portfolio_value
                total_pnl += pnl
                
            except Exception as e:
                logger.error(f"Error getting performance for {trader_name}: {e}")
                performance_data["traders"][trader_name] = {"error": str(e)}
        
        # Update system metrics
        performance_data["system_metrics"].update({
            "total_traders": len(traders),
            "active_traders_today": active_today,
            "total_trades_today": total_trades_today,
            "total_portfolio_value": round(total_portfolio, 2),
            "total_pnl": round(total_pnl, 2),
            "average_pnl": round(total_pnl / len(traders), 2) if traders else 0
        })
        
        return performance_data
        
    except Exception as e:
        logger.error(f"Error getting system performance: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting system performance: {str(e)}")

@app.get("/api/system/health")
async def get_system_health():
    """Get system health status"""
    try:
        from database import Database
        from db_config import DATABASE_PATH
        import psutil
        import os
        
        db = Database(DATABASE_PATH)
        
        health_data = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "database": {
                "type": "PostgreSQL" if db.use_postgresql else "SQLite",
                "url_present": bool(db.database_url) if hasattr(db, 'database_url') else False,
                "connection_test": "unknown"
            },
            "api_server": {
                "status": "running",
                "polygon_client": polygon_client is not None
            },
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            }
        }
        
        # Test database connection
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                health_data["database"]["connection_test"] = "success"
        except Exception as e:
            health_data["database"]["connection_test"] = f"failed: {str(e)}"
            health_data["status"] = "degraded"
        
        return health_data
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "error", 
            "error": str(e)
        }

@app.get("/api/system/live-activity")
async def get_live_activity():
    """Get recent trading activity across all traders"""
    try:
        from datetime import datetime, timedelta
        
        # Get activity from last 30 minutes
        cutoff_time = datetime.now() - timedelta(minutes=30)
        cutoff_str = cutoff_time.strftime("%Y-%m-%d %H:%M:%S")
        
        activity_data = {
            "timestamp": datetime.now().isoformat(),
            "cutoff_time": cutoff_str,
            "recent_trades": [],
            "recent_portfolio_updates": []
        }
        
        traders = ["warren", "camillo", "flash"]
        
        for trader_name in traders:
            try:
                account = get_trader_account(trader_name)
                
                # Get recent trades
                for tx in account.transactions:
                    if tx.timestamp >= cutoff_str:
                        activity_data["recent_trades"].append({
                            "trader": trader_name,
                            "timestamp": tx.timestamp,
                            "symbol": tx.symbol,
                            "side": "BUY" if tx.quantity > 0 else "SELL",
                            "quantity": abs(tx.quantity),
                            "price": tx.price,
                            "total": abs(tx.total())
                        })
                
                # Get recent portfolio updates
                for timestamp, value in account.portfolio_value_time_series:
                    if timestamp >= cutoff_str:
                        activity_data["recent_portfolio_updates"].append({
                            "trader": trader_name,
                            "timestamp": timestamp,
                            "portfolio_value": value
                        })
                        
            except Exception as e:
                logger.error(f"Error getting activity for {trader_name}: {e}")
        
        # Sort by timestamp
        activity_data["recent_trades"].sort(key=lambda x: x["timestamp"], reverse=True)
        activity_data["recent_portfolio_updates"].sort(key=lambda x: x["timestamp"], reverse=True)
        
        return activity_data
        
    except Exception as e:
        logger.error(f"Error getting live activity: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting live activity: {str(e)}")

@app.get("/monitor", response_class=HTMLResponse)
async def get_monitor_dashboard():
    """Serve the monitoring dashboard"""
    try:
        with open("dashboard.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html><body>
        <h1>Monitor Dashboard Not Found</h1>
        <p>The dashboard.html file is missing. Please ensure it exists in the same directory as the API server.</p>
        <p><a href="/docs">API Documentation</a></p>
        </body></html>
        """)

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Trading System API Server...")
    print("📊 Frontend should connect to: http://localhost:8000")
    print("📝 API docs available at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)