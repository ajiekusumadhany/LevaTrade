#!/usr/bin/env python3
"""
Script untuk menghapus semua data trading dan memulai fresh dengan balance $200
"""
import sqlite3
import os
import json
from datetime import datetime

def clear_all_databases():
    """Clear all trading databases and reset to fresh state"""
    
    print("🗑️ CLEARING ALL TRADING DATA")
    print("=" * 50)
    
    # Database files to clear
    db_files = [
        'dry_run_trades.db',
        'real_trades.db',
        'strategy_performance.db',
        'psychological_state.db'
    ]
    
    # Clear each database
    for db_file in db_files:
        if os.path.exists(db_file):
            try:
                # Connect and get all tables
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Get all table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                # Clear each table
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"DELETE FROM {table_name}")
                    print(f"  ✅ Cleared table: {table_name} in {db_file}")
                
                conn.commit()
                conn.close()
                
                print(f"✅ Database cleared: {db_file}")
                
            except Exception as e:
                print(f"❌ Error clearing {db_file}: {e}")
        else:
            print(f"⚠️ Database not found: {db_file}")
    
    print()
    
    # Clear JSON state files
    json_files = [
        'notifications.json',
        'conditional_risk_state.json',
        'trading_control.json'
    ]
    
    for json_file in json_files:
        if os.path.exists(json_file):
            try:
                if json_file == 'notifications.json':
                    # Reset notifications
                    with open(json_file, 'w') as f:
                        json.dump([], f)
                
                elif json_file == 'conditional_risk_state.json':
                    # Reset conditional risk state
                    reset_state = {
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "daily_pnl": 0.0,
                        "consecutive_losses": 0,
                        "trades_by_session": {
                            "DEAD_ZONE": 0,
                            "ASIA": 0,
                            "LONDON": 0,
                            "NEWYORK": 0
                        },
                        "ny_1pct_trades": 0,
                        "last_trade_result": "NONE",
                        "last_trade_time": "",
                        "session_pnl": {
                            "DEAD_ZONE": 0.0,
                            "ASIA": 0.0,
                            "LONDON": 0.0,
                            "NEWYORK": 0.0
                        }
                    }
                    with open(json_file, 'w') as f:
                        json.dump(reset_state, f, indent=2)
                
                elif json_file == 'trading_control.json':
                    # Reset trading control
                    control_state = {
                        "enabled": False,
                        "last_updated": datetime.now().isoformat(),
                        "updated_by": "database_reset"
                    }
                    with open(json_file, 'w') as f:
                        json.dump(control_state, f, indent=2)
                
                print(f"✅ JSON file reset: {json_file}")
                
            except Exception as e:
                print(f"❌ Error resetting {json_file}: {e}")
    
    print()
    
    # Verify balance in .env
    try:
        with open('.env', 'r') as f:
            env_content = f.read()
        
        if 'BALANCE_USD=200' in env_content:
            print("✅ Balance confirmed: $200 USD")
        else:
            print("⚠️ Balance not set to $200 in .env file")
    except Exception as e:
        print(f"❌ Error checking .env: {e}")
    
    print()
    print("🎯 FRESH START READY!")
    print("=" * 50)
    print("📊 Starting Balance: $200 USD")
    print("🔄 All trade history cleared")
    print("📈 All performance metrics reset")
    print("🧠 Psychological state reset")
    print("⚠️ Risk management reset")
    print("🚫 Trading disabled (use dashboard to enable)")
    print()
    print("🚀 Ready to start fresh trading!")

if __name__ == "__main__":
    # Confirmation
    print("⚠️ WARNING: This will DELETE ALL trading data!")
    print("📊 Current balance will be reset to $200")
    print("🗑️ All trade history will be lost")
    print()
    
    confirm = input("Type 'CLEAR' to confirm: ")
    if confirm == 'CLEAR':
        clear_all_databases()
    else:
        print("❌ Operation cancelled")