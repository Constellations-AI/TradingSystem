#!/usr/bin/env python3
"""
Bulk Market Data Preparation
Downloads and caches market data before trading begins
"""
from data.polygon import PolygonClient
from database import Database
from datetime import datetime
import time

# Core portfolio stocks to track
CORE_PORTFOLIO = ["HOOD", "TSLA", "AAPL", "NVDA"]

class MarketDataPrep:
    """Handles bulk market data preparation"""
    
    def __init__(self, db_path: str = "trading_system.db"):
        self.polygon = PolygonClient(db_path=db_path)
        self.db = Database(db_path)
    
    def prep_market_data(self, verbose: bool = True) -> dict:
        """
        Download and cache all market data for trading day
        Returns summary of data prepared
        """
        start_time = time.time()
        summary = {
            "timestamp": datetime.now().isoformat(),
            "core_portfolio": {},
            "market_movers": {},
            "market_status": {},
            "total_api_calls": 0,
            "prep_time_seconds": 0
        }
        
        if verbose:
            print("🚀 Starting market data preparation...")
        
        # 1. Market Status
        if verbose:
            print("📊 Getting market status...")
        summary["market_status"] = self.polygon.get_market_status()
        summary["total_api_calls"] += 1
        
        # 2. Core Portfolio Data (3 months historical + current)
        if verbose:
            print(f"📈 Preparing core portfolio: {', '.join(CORE_PORTFOLIO)}")
        
        for ticker in CORE_PORTFOLIO:
            if verbose:
                print(f"  • {ticker}...")
            
            # Historical price data (3 months)
            price_data = self.polygon.get_aggregates(ticker, timespan="day", limit=90)
            
            # Current quote
            current_quote = self.polygon.get_last_quote(ticker)
            
            # Technical indicators
            rsi_data = self.polygon.get_rsi(ticker, limit=14)
            macd_data = self.polygon.get_macd(ticker, limit=26)
            sma_20 = self.polygon.get_sma(ticker, window=20, limit=20)
            sma_50 = self.polygon.get_sma(ticker, window=50, limit=50)
            
            summary["core_portfolio"][ticker] = {
                "price_bars": len(price_data.get("results", [])),
                "current_quote": current_quote.get("status") == "OK",
                "technical_indicators": {
                    "rsi": len(rsi_data.get("results", {}).get("values", [])),
                    "macd": len(macd_data.get("results", {}).get("values", [])),
                    "sma_20": len(sma_20.get("results", {}).get("values", [])),
                    "sma_50": len(sma_50.get("results", {}).get("values", []))
                }
            }
            summary["total_api_calls"] += 6  # price + quote + 4 indicators
        
        # 3. Market Movers
        if verbose:
            print("🎯 Getting market movers...")
        
        gainers = self.polygon.get_market_gainers(limit=20)
        losers = self.polygon.get_market_losers(limit=20)
        most_active = self.polygon.get_most_active(limit=20)
        
        summary["market_movers"] = {
            "gainers": len(gainers.get("results", [])),
            "losers": len(losers.get("results", [])),
            "most_active": len(most_active.get("results", []))
        }
        summary["total_api_calls"] += 3
        
        # Final summary
        summary["prep_time_seconds"] = round(time.time() - start_time, 2)
        
        if verbose:
            print(f"✅ Market prep complete!")
            print(f"   • {summary['total_api_calls']} API calls made")
            print(f"   • {summary['prep_time_seconds']}s total time")
            print(f"   • Core portfolio: {len(CORE_PORTFOLIO)} stocks prepared")
            print(f"   • Market movers: {sum(summary['market_movers'].values())} stocks")
        
        return summary

def prep_market_data_cli():
    """Command line interface for market prep"""
    print("🌅 Pre-Market Data Preparation")
    print("=" * 40)
    
    prep = MarketDataPrep()
    summary = prep.prep_market_data(verbose=True)
    
    print(f"\n📋 Summary:")
    print(f"Market Status: {summary['market_status'].get('market', 'Unknown')}")
    
    for ticker, data in summary["core_portfolio"].items():
        bars = data["price_bars"]
        quote = "✅" if data["current_quote"] else "❌"
        indicators = sum(data["technical_indicators"].values())
        print(f"{ticker}: {bars} price bars, quote {quote}, {indicators} indicator points")

if __name__ == "__main__":
    prep_market_data_cli()