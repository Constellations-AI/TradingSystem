#!/usr/bin/env python3
"""
Database Inspector - View data in trading_system.db
"""
import sqlite3
import json
from datetime import datetime

def inspect_database(db_path="trading_system.db"):
    """Inspect database contents in a readable format"""
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print(f"📊 Inspecting database: {db_path}")
        print("=" * 60)
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            print(f"\n📋 TABLE: {table}")
            print("-" * 40)
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"Total rows: {count}")
            
            if count > 0:
                # Show sample data
                cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                rows = cursor.fetchall()
                
                for i, row in enumerate(rows, 1):
                    print(f"\n  Row {i}:")
                    for key in row.keys():
                        value = row[key]
                        
                        # Pretty print JSON data
                        if key in ['response_data', 'parameters', 'conversation_history', 'tool_args']:
                            try:
                                if value:
                                    parsed = json.loads(value)
                                    if key == 'response_data' and 'feed' in parsed:
                                        print(f"    {key}: {len(parsed['feed'])} articles")
                                    elif key == 'parameters':
                                        print(f"    {key}: {parsed}")
                                    else:
                                        print(f"    {key}: [JSON data - {len(str(value))} chars]")
                                else:
                                    print(f"    {key}: None")
                            except:
                                print(f"    {key}: {str(value)[:100]}...")
                        
                        # Truncate long text
                        elif isinstance(value, str) and len(value) > 100:
                            print(f"    {key}: {value[:100]}...")
                        
                        # Show other fields normally
                        else:
                            print(f"    {key}: {value}")
        
        # Show useful queries
        print(f"\n🔍 USEFUL QUERIES:")
        print("-" * 40)
        
        # Cache hit rate
        if 'raw_api_calls' in tables:
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN was_cached = 1 THEN 1 END) as cache_hits,
                    COUNT(*) as total_calls,
                    ROUND(COUNT(CASE WHEN was_cached = 1 THEN 1 END) * 100.0 / COUNT(*), 1) as hit_rate
                FROM raw_api_calls
            """)
            result = cursor.fetchone()
            print(f"Cache performance: {result[0]}/{result[1]} hits ({result[2]}% hit rate)")
        
        # Recent activity
        if 'user_sessions' in tables:
            cursor.execute("SELECT COUNT(*) FROM user_sessions WHERE created_at > datetime('now', '-24 hours')")
            recent = cursor.fetchone()[0]
            print(f"Sessions in last 24h: {recent}")
        
        # Tool usage
        if 'tool_usage' in tables:
            cursor.execute("SELECT tool_name, COUNT(*) as usage_count FROM tool_usage GROUP BY tool_name")
            tool_stats = cursor.fetchall()
            print("Tool usage:")
            for tool, count in tool_stats:
                print(f"  {tool}: {count} calls")
        
        conn.close()
        
    except Exception as e:
        print(f"Error inspecting database: {e}")

if __name__ == "__main__":
    inspect_database()