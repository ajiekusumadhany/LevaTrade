#!/usr/bin/env python3
"""
Script untuk reset semua database dan mulai ulang dengan balance $200
"""
import sqlite3
import os
import json
from datetime import datetime

def reset_databases():
    print("🔄 RESETTING ALL DATABASES...")
    print("=" * 50)
    
    # 1. Reset Dry Run Database
    try:
        if os.path.exists('dry_run_trades.db'):
            conn = sqlite3.connect('dry_run_trades.db')
            cursor = conn.cursor()
            
            # Clear all tables
            cursor.execute('DELETE FROM trade_history')
            cursor.execute('DELETE FROM open_positions')
            cursor.execute('DELETE FROM balance_history')
            
            # Reset balance to $200
            cursor.execute('''
                INSERT OR REPLACE INTO balance_history (date, balance, pnl, trades_count)
                VALUES (?, ?, ?, ?)
            ''', (datetime.now().strftime('%Y-%m-%d'), 200.0, 0.0, 0))
            
            conn.commit()
            conn.close()
            print("✅ Dry run database reset - Balance: $200")
        else:
            print("⚠️ Dry run database not found")
    except Exception as e:
        print(f"❌ Error resetting dry run database: {e}")
    
    # 2. Reset Real Trade Database
    try:
        if os.path.exists('real_trades.db'):
            conn = sqlite3.connect('real_trades.db')
            cursor = conn.cursor()
            
            # Clear all tables
            cursor.execute('DELETE FROM trade_history')
            cursor.execute('DELETE FROM open_positions')
            cursor.execute('DELETE FROM balance_history')
            
            # Reset balance to $200
            cursor.execute('''
                INSERT OR REPLACE INTO balance_history (date, balance, pnl, trades_count)
                VALUES (?, ?, ?, ?)
            ''', (datetime.now().strftime('%Y-%m-%d'), 200.0, 0.0, 0))
            
            conn.commit()
            conn.close()
            print("✅ Real trade database reset - Balance: $200")
        else:
            print("⚠️ Real trade database not found")
    except Exception as e:
        print(f"❌ Error resetting real trade database: {e}")
    
    # 3. Reset Strategy Performance Database
    try:
        if os.path.exists('strategy_performance.db'):
            conn = sqlite3.connect('strategy_performance.db')
            cursor = conn.cursor()
            
            # Clear performance data
            cursor.execute('DELETE FROM daily_performance')
            cursor.execute('DELETE FROM strategy_metrics')
            
            conn.commit()
            conn.close()
            print("✅ Strategy performance database reset")
        else:
            print("⚠️ Strategy performance database not found")
    except Exception as e:
        print(f"❌ Error resetting strategy performance database: {e}")
    
    # 4. Reset Psychological State Database
    try:
        if os.path.exists('psychological_state.db'):
            conn = sqlite3.connect('psychological_state.db')
            cursor = conn.cursor()
            
            # Clear psychological data
            cursor.execute('DELETE FROM psychological_metrics')
            cursor.execute('DELETE FROM session_analysis')
            
            conn.commit()
            conn.close()
            print("✅ Psychological state database reset")
        else:
            print("⚠️ Psychological state database not found")
    except Exception as e:
        print(f"❌ Error resetting psychological state database: {e}")
    
    # 5. Reset Conditional Risk State
    try:
        risk_state = {
            "date": datetime.now().strftime('%Y-%m-%d'),
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
        
        with open('conditional_risk_state.json', 'w') as f:
            json.dump(risk_state, f, indent=2)
        
        print("✅ Conditional risk state reset")
    except Exception as e:
        print(f"❌ Error resetting conditional risk state: {e}")
    
    # 6. Reset Notifications
    try:
        notifications = []
        with open('notifications.json', 'w') as f:
            json.dump(notifications, f, indent=2)
        
        print("✅ Notifications cleared")
    except Exception as e:
        print(f"❌ Error clearing notifications: {e}")
    
    # 7. Update .env file with new balance
    try:
        with open('.env', 'r') as f:
            env_content = f.read()
        
        # Update BALANCE_USD
        lines = env_content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('BALANCE_USD='):
                lines[i] = 'BALANCE_USD=200'
                break
        
        with open('.env', 'w') as f:
            f.write('\n'.join(lines))
        
        print("✅ Environment balance updated to $200")
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
    
    print()
    print("🎯 DATABASE RESET COMPLETE!")
    print("=" * 50)
    print("📊 New Configuration:")
    print("   💰 Starting Balance: $200")
    print("   📈 Trade History: Cleared")
    print("   🎯 Open Positions: None")
    print("   📊 Performance Metrics: Reset")
    print("   🧠 Psychological State: Reset")
    print("   ⚠️ Risk Management: Reset")
    print()
    print("🚀 Ready to start fresh trading!")

if __name__ == "__main__":
    reset_databases()