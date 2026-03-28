#!/usr/bin/env python3
"""
Script untuk clear trade data yang ada
"""
import sqlite3
import os

def clear_trade_data():
    print("🧹 CLEARING TRADE DATA...")
    print("=" * 40)
    
    # Clear dry run trades
    try:
        if os.path.exists('dry_run_trades.db'):
            conn = sqlite3.connect('dry_run_trades.db')
            cursor = conn.cursor()
            
            # Get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                try:
                    cursor.execute(f'DELETE FROM {table_name}')
                    print(f"✅ Cleared table: {table_name}")
                except Exception as e:
                    print(f"⚠️ Could not clear {table_name}: {e}")
            
            conn.commit()
            conn.close()
            print("✅ Dry run database cleared")
        else:
            print("⚠️ Dry run database not found")
    except Exception as e:
        print(f"❌ Error clearing dry run database: {e}")
    
    # Clear real trades
    try:
        if os.path.exists('real_trades.db'):
            conn = sqlite3.connect('real_trades.db')
            cursor = conn.cursor()
            
            # Get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                try:
                    cursor.execute(f'DELETE FROM {table_name}')
                    print(f"✅ Cleared table: {table_name}")
                except Exception as e:
                    print(f"⚠️ Could not clear {table_name}: {e}")
            
            conn.commit()
            conn.close()
            print("✅ Real trade database cleared")
        else:
            print("⚠️ Real trade database not found")
    except Exception as e:
        print(f"❌ Error clearing real trade database: {e}")
    
    print()
    print("🎯 TRADE DATA CLEARED!")
    print("💰 New balance will be $200 from .env file")

if __name__ == "__main__":
    clear_trade_data()