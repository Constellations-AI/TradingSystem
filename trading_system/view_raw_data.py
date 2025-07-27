#!/usr/bin/env python3
"""
Raw Database Viewer - See EVERYTHING in the database
"""
import sqlite3
import json

def view_raw_data(db_path="trading_system.db", table_name=None, row_id=None):
    """View raw database contents without formatting"""
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print(f"🔍 RAW DATA VIEWER: {db_path}")
        print("=" * 80)
        
        if table_name and row_id:
            # Show specific row
            cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (row_id,))
            row = cursor.fetchone()
            if row:
                print(f"\n📋 {table_name} - Row {row_id}:")
                print("-" * 60)
                for key in row.keys():
                    value = row[key]
                    print(f"{key}:")
                    if key in ['response_data', 'parameters', 'conversation_history', 'tool_args'] and value:
                        try:
                            parsed = json.loads(value)
                            print(json.dumps(parsed, indent=2))
                        except:
                            print(f"  {value}")
                    else:
                        print(f"  {value}")
                    print()
            else:
                print(f"No row found with id {row_id} in {table_name}")
        
        elif table_name:
            # Show all rows from specific table
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            print(f"\n📋 {table_name} - ALL ROWS ({len(rows)} total):")
            print("-" * 60)
            
            for row in rows:
                print(f"\n--- Row ID: {row['id']} ---")
                for key in row.keys():
                    value = row[key]
                    print(f"{key}: {repr(value)}")
                print()
        
        else:
            # Show all tables with counts
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            print("\n📊 TABLES OVERVIEW:")
            print("-" * 40)
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"{table}: {count} rows")
            
            print(f"\nUsage:")
            print(f"  python view_raw_data.py [table_name] [row_id]")
            print(f"  python view_raw_data.py raw_api_calls")
            print(f"  python view_raw_data.py raw_api_calls 1")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    
    table = sys.argv[1] if len(sys.argv) > 1 else None
    row_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    view_raw_data("trading_system.db", table, row_id)