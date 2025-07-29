#!/usr/bin/env python3
"""
Trading System Monitor
Allows monitoring of live system performance via API endpoints
"""

import requests
import json
import time
from datetime import datetime
import sys

def get_system_url():
    """Get the system URL - try Railway first, then local"""
    # You can set this to your Railway URL
    railway_url = "https://tradingsystem-production.up.railway.app"  # Your actual Railway URL
    local_url = "http://localhost:8000"
    
    # Try Railway first
    try:
        response = requests.get(f"{railway_url}/", timeout=5)
        if response.status_code == 200:
            return railway_url
    except:
        pass
    
    # Fall back to local
    try:
        response = requests.get(f"{local_url}/", timeout=2)
        if response.status_code == 200:
            return local_url
    except:
        pass
    
    return None

def fetch_endpoint(url, endpoint):
    """Fetch data from an API endpoint"""
    try:
        response = requests.get(f"{url}{endpoint}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def format_currency(amount):
    """Format currency amounts"""
    return f"${amount:,.2f}"

def print_system_performance(data):
    """Print system performance in a readable format"""
    print("=" * 60)
    print(f"📊 TRADING SYSTEM PERFORMANCE - {data.get('timestamp', 'Unknown time')}")
    print(f"💾 Database: {data.get('database_type', 'Unknown')}")
    print("=" * 60)
    
    # System metrics
    metrics = data.get('system_metrics', {})
    print(f"🔢 Total Traders: {metrics.get('total_traders', 0)}")
    print(f"✅ Active Today: {metrics.get('active_traders_today', 0)}")
    print(f"💰 Total Portfolio: {format_currency(metrics.get('total_portfolio_value', 0))}")
    print(f"📈 Total P&L: {format_currency(metrics.get('total_pnl', 0))}")
    print(f"📊 Average P&L: {format_currency(metrics.get('average_pnl', 0))}")
    print(f"🔄 Total Trades Today: {metrics.get('total_trades_today', 0)}")
    print()
    
    # Individual trader performance
    traders = data.get('traders', {})
    for trader_name, trader_data in traders.items():
        if 'error' in trader_data:
            print(f"❌ {trader_name.upper()}: Error - {trader_data['error']}")
            continue
            
        status = "🟢 ACTIVE" if trader_data.get('is_active_today', False) else "🔴 INACTIVE"
        print(f"{status} {trader_name.upper()}:")
        print(f"   💰 Portfolio: {format_currency(trader_data.get('portfolio_value', 0))}")
        print(f"   💵 Cash: {format_currency(trader_data.get('cash_balance', 0))}")
        print(f"   📈 P&L: {format_currency(trader_data.get('pnl', 0))} ({trader_data.get('pnl_percent', 0):.2f}%)")
        print(f"   🛒 Holdings: {len(trader_data.get('holdings', {}))}")
        print(f"   🔄 Trades Today: {trader_data.get('trades_today', 0)}")
        
        last_trade = trader_data.get('last_trade')
        if last_trade:
            print(f"   🕐 Last Trade: {last_trade['side']} {last_trade['quantity']} {last_trade['symbol']} @ {format_currency(last_trade['price'])}")
        print()

def print_system_health(data):
    """Print system health status"""
    print("=" * 60)
    print(f"🏥 SYSTEM HEALTH - {data.get('timestamp', 'Unknown time')}")
    print("=" * 60)
    
    status = data.get('status', 'unknown')
    status_emoji = {"healthy": "🟢", "degraded": "🟡", "error": "🔴"}.get(status, "❓")
    print(f"Status: {status_emoji} {status.upper()}")
    print()
    
    # Database status
    db = data.get('database', {})
    print(f"💾 Database:")
    print(f"   Type: {db.get('type', 'Unknown')}")
    print(f"   URL Present: {db.get('url_present', False)}")
    print(f"   Connection: {db.get('connection_test', 'Unknown')}")
    print()
    
    # System metrics
    system = data.get('system', {})
    if system:
        print(f"🖥️  System Resources:")
        print(f"   CPU: {system.get('cpu_percent', 0):.1f}%")
        print(f"   Memory: {system.get('memory_percent', 0):.1f}%")
        print(f"   Disk: {system.get('disk_percent', 0):.1f}%")
    print()

def print_live_activity(data):
    """Print recent trading activity"""
    print("=" * 60)
    print(f"🔴 LIVE ACTIVITY - {data.get('timestamp', 'Unknown time')}")
    print(f"📅 Since: {data.get('cutoff_time', 'Unknown')}")
    print("=" * 60)
    
    # Recent trades
    trades = data.get('recent_trades', [])
    if trades:
        print(f"💸 Recent Trades ({len(trades)}):")
        for trade in trades[:10]:  # Show last 10 trades
            emoji = "🟢" if trade['side'] == 'BUY' else "🔴"
            print(f"   {emoji} {trade['timestamp']} - {trade['trader'].upper()}: {trade['side']} {trade['quantity']} {trade['symbol']} @ {format_currency(trade['price'])}")
        print()
    
    # Recent portfolio updates (summarized)
    updates = data.get('recent_portfolio_updates', [])
    if updates:
        print(f"📊 Recent Portfolio Updates: {len(updates)} total")
        
        # Group by trader
        by_trader = {}
        for update in updates:
            trader = update['trader']
            if trader not in by_trader:
                by_trader[trader] = []
            by_trader[trader].append(update)
        
        for trader, trader_updates in by_trader.items():
            if trader_updates:
                latest = trader_updates[0]  # Most recent
                count = len(trader_updates)
                print(f"   📈 {trader.upper()}: {count} updates, latest: {format_currency(latest['portfolio_value'])}")
        print()

def main():
    """Main monitoring loop"""
    # Get system URL
    url = get_system_url()
    if not url:
        print("❌ Could not connect to trading system API")
        print("   Make sure the API server is running on localhost:8000 or update the Railway URL")
        sys.exit(1)
    
    print(f"🔗 Connected to: {url}")
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "performance":
            data = fetch_endpoint(url, "/api/system/performance")
            if 'error' not in data:
                print_system_performance(data)
            else:
                print(f"❌ Error: {data['error']}")
                
        elif mode == "health":
            data = fetch_endpoint(url, "/api/system/health")
            if 'error' not in data:
                print_system_health(data)
            else:
                print(f"❌ Error: {data['error']}")
                
        elif mode == "activity":
            data = fetch_endpoint(url, "/api/system/live-activity")
            if 'error' not in data:
                print_live_activity(data)
            else:
                print(f"❌ Error: {data['error']}")
                
        elif mode == "watch":
            print("👀 Watching system performance (Ctrl+C to stop)...")
            try:
                while True:
                    print("\033[2J\033[H")  # Clear screen
                    data = fetch_endpoint(url, "/api/system/performance")
                    if 'error' not in data:
                        print_system_performance(data)
                    else:
                        print(f"❌ Error: {data['error']}")
                    
                    time.sleep(10)  # Update every 10 seconds
            except KeyboardInterrupt:
                print("\n👋 Monitoring stopped")
        else:
            print("❌ Unknown mode. Use: performance, health, activity, or watch")
    else:
        # Default: show all
        print("\n" + "="*60)
        print("📊 FULL SYSTEM STATUS")
        print("="*60)
        
        # Performance
        data = fetch_endpoint(url, "/api/system/performance")
        if 'error' not in data:
            print_system_performance(data)
        
        # Health
        data = fetch_endpoint(url, "/api/system/health")
        if 'error' not in data:
            print_system_health(data)
        
        # Activity
        data = fetch_endpoint(url, "/api/system/live-activity")
        if 'error' not in data:
            print_live_activity(data)

if __name__ == "__main__":
    main()