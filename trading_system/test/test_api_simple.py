#!/usr/bin/env python3
"""
Simple test to check if our API components work
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all imports work"""
    try:
        print("Testing imports...")
        
        print("✓ Testing accounts import...")
        from accounts import get_trader_account
        
        print("✓ Testing Polygon client...")
        from data.polygon import PolygonClient
        
        print("✓ Testing FastAPI...")
        from fastapi import FastAPI
        
        print("✓ All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_trader_accounts():
    """Test if trader accounts work"""
    try:
        print("\nTesting trader accounts...")
        from accounts import get_trader_account
        
        for trader in ["warren", "cathie", "flash"]:
            account = get_trader_account(trader)
            print(f"✓ {trader}: balance=${account.balance:,.2f}, holdings={len(account.holdings)}")
        
        return True
    except Exception as e:
        print(f"❌ Trader account test failed: {e}")
        return False

def test_polygon():
    """Test Polygon connection"""
    try:
        print("\nTesting Polygon API...")
        from data.polygon import PolygonClient
        
        client = PolygonClient()
        print("✓ Polygon client created successfully")
        return True
    except Exception as e:
        print(f"❌ Polygon test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing API components...")
    
    if not test_imports():
        sys.exit(1)
    
    if not test_trader_accounts():
        sys.exit(1)
        
    if not test_polygon():
        print("⚠️ Polygon failed but continuing...")
    
    print("\n✅ Basic components working! Try starting the API server.")