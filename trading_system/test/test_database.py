#!/usr/bin/env python3
"""
Test script to verify database setup and basic functionality
"""
import asyncio
from database import Database
from data.alpha_vantage import AlphaVantageClient

async def test_database_setup():
    """Test basic database functionality"""
    print("🧪 Testing Database Setup...")
    
    # Initialize database
    db = Database("test_trading_system.db")
    print("✅ Database initialized")
    
    # Test API caching
    print("\n📡 Testing Alpha Vantage integration...")
    try:
        alpha = AlphaVantageClient(db_path="test_trading_system.db")
        
        # Test a simple API call (this will actually call the API)
        print("Making test API call...")
        result = alpha.search_symbol("AAPL")
        print(f"✅ API call successful: {len(result.get('bestMatches', []))} results")
        
        # Test caching (this should be cached)
        print("Testing cache...")
        result2 = alpha.search_symbol("AAPL")
        print("✅ Cache test completed")
        
    except Exception as e:
        print(f"⚠️ Alpha Vantage test failed (this is expected if API key not configured): {e}")
    
    # Test database analytics
    print("\n📊 Testing database analytics...")
    analytics = db.get_briefing_analytics()
    print(f"Analytics: {analytics}")
    
    print("\n🎉 Database setup test completed!")
    return True

if __name__ == "__main__":
    asyncio.run(test_database_setup())