#!/usr/bin/env python3
"""
FastAPI server to serve trading data to React frontend
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

@app.get("/debug/database")
async def debug_database():
    """Debug endpoint to check database status"""
    import os
    import sqlite3
    
    # Check if database file exists
    db_exists = os.path.exists("trading_system.db")
    db_size = os.path.getsize("trading_system.db") if db_exists else 0
    
    # Check tables and row counts
    tables_info = {}
    if db_exists:
        try:
            conn = sqlite3.connect("trading_system.db")
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                tables_info[table_name] = count
                
            conn.close()
        except Exception as e:
            tables_info["error"] = str(e)
    
    # Also check trader_accounts data
    trader_data = {}
    if db_exists and "trader_accounts" in tables_info:
        try:
            conn = sqlite3.connect("trading_system.db")
            cursor = conn.cursor()
            cursor.execute("SELECT trader_name, balance, holdings FROM trader_accounts")
            rows = cursor.fetchall()
            for row in rows:
                trader_data[row[0]] = {"balance": row[1], "holdings": row[2]}
            conn.close()
        except Exception as e:
            trader_data["error"] = str(e)
    
    return {
        "database_exists": db_exists,
        "database_size_bytes": db_size,
        "working_directory": os.getcwd(),
        "files_in_directory": os.listdir("."),
        "tables": tables_info,
        "trader_data": trader_data
    }

@app.get("/api/traders")
async def get_traders():
    """Get list of all traders"""
    return {
        "traders": [
            {"id": 1, "name": "warren", "display_name": "Warren", "color": "trading-blue"},
            {"id": 4, "name": "camillo", "display_name": "Camillo", "color": "trading-yellow"},
            {"id": 3, "name": "pavel", "display_name": "Pavel", "color": "trading-purple"}
        ]
    }

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
        traders = ["warren", "camillo", "pavel"]
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

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Trading System API Server...")
    print("📊 Frontend should connect to: http://localhost:8000")
    print("📝 API docs available at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)