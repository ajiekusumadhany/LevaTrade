"""
Complete System Reset - Force recreate databases and reset everything
"""
import sqlite3
import os
import time
import json
from datetime import datetime

def force_delete_database(db_path):
    """Force delete database file with retries"""
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
                print(f"   ✅ Deleted {db_path}")
                return True
        except Exception as e:
            print(f"   ⚠️ Attempt {attempt + 1}: Cannot delete {db_path}: {e}")
            if attempt < max_attempts - 1:
                time.sleep(2)  # Wait 2 seconds before retry
            else:
                print(f"   ❌ Failed to delete {db_path} after {max_attempts} attempts")
                return False
    return False

def create_complete_database(db_path):
    """Create database with complete schema"""
    print(f"🔧 Creating {db_path} with complete schema...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create open_positions table with ALL required columns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS open_positions (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                quantity REAL NOT NULL,
                leverage INTEGER NOT NULL,
                entry_time TEXT NOT NULL,
                stop_loss REAL DEFAULT 0,
                take_profit REAL DEFAULT 0,
                tp_price REAL DEFAULT 0,
                sl_price REAL DEFAULT 0,
                trading_session TEXT DEFAULT "",
                current_price REAL DEFAULT 0,
                unrealized_pnl REAL DEFAULT 0,
                position_value_usd REAL DEFAULT 0,
                margin_used REAL DEFAULT 0,
                liquidation_price REAL DEFAULT 0,
                bybit_order_id TEXT DEFAULT "",
                indicators TEXT DEFAULT "",
                ai_reasoning TEXT DEFAULT "",
                ai_entry_reasoning TEXT DEFAULT "",
                session_type TEXT DEFAULT "",
                risk_percentage REAL DEFAULT 0,
                atr_value REAL DEFAULT 0,
                tp_atr_multiplier REAL DEFAULT 0,
                sl_atr_multiplier REAL DEFAULT 0,
                market_cap REAL DEFAULT 0,
                market_cap_rank INTEGER DEFAULT 0,
                total_volume_24h REAL DEFAULT 0,
                circulating_supply REAL DEFAULT 0,
                total_supply REAL DEFAULT 0,
                max_supply REAL DEFAULT 0,
                price_change_24h REAL DEFAULT 0,
                price_change_percentage_24h REAL DEFAULT 0,
                price_change_percentage_7d REAL DEFAULT 0,
                price_change_percentage_30d REAL DEFAULT 0,
                ath REAL DEFAULT 0,
                ath_change_percentage REAL DEFAULT 0,
                atl REAL DEFAULT 0,
                atl_change_percentage REAL DEFAULT 0,
                bybit_volume_24h REAL DEFAULT 0,
                bybit_turnover_24h REAL DEFAULT 0,
                liquidity_score REAL DEFAULT 0,
                volatility_score REAL DEFAULT 0,
                market_dominance REAL DEFAULT 0,
                market_cap_category TEXT DEFAULT "",
                volume_category TEXT DEFAULT "",
                market_data_timestamp TEXT DEFAULT "",
                correlation_group TEXT DEFAULT "",
                psychological_factor REAL DEFAULT 1.0,
                entry_confidence REAL DEFAULT 0,
                max_favorable_excursion REAL DEFAULT 0,
                max_adverse_excursion REAL DEFAULT 0,
                price_change_percentage REAL DEFAULT 0,
                last_update_time TEXT DEFAULT "",
                duration_minutes INTEGER DEFAULT 0,
                peak_pnl REAL DEFAULT 0,
                drawdown_from_peak REAL DEFAULT 0,
                trailing_stop_price REAL DEFAULT 0,
                is_trailing_active INTEGER DEFAULT 0
            )
        ''')
        
        # Create trade_history table with ALL required columns (39 columns)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_history (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL DEFAULT 0,
                quantity REAL NOT NULL,
                leverage INTEGER NOT NULL,
                entry_time TEXT NOT NULL,
                exit_time TEXT DEFAULT "",
                exit_reason TEXT DEFAULT "",
                pnl REAL DEFAULT 0,
                pnl_percentage REAL DEFAULT 0,
                indicators TEXT DEFAULT "",
                position_value_usd REAL DEFAULT 0,
                duration_minutes INTEGER DEFAULT 0,
                ai_entry_reasoning TEXT DEFAULT "",
                ai_exit_reasoning TEXT DEFAULT "",
                market_cap REAL DEFAULT 0,
                market_cap_rank INTEGER DEFAULT 0,
                total_volume_24h REAL DEFAULT 0,
                circulating_supply REAL DEFAULT 0,
                total_supply REAL DEFAULT 0,
                max_supply REAL DEFAULT 0,
                price_change_24h REAL DEFAULT 0,
                price_change_percentage_24h REAL DEFAULT 0,
                price_change_percentage_7d REAL DEFAULT 0,
                price_change_percentage_30d REAL DEFAULT 0,
                ath REAL DEFAULT 0,
                ath_change_percentage REAL DEFAULT 0,
                atl REAL DEFAULT 0,
                atl_change_percentage REAL DEFAULT 0,
                bybit_volume_24h REAL DEFAULT 0,
                bybit_turnover_24h REAL DEFAULT 0,
                liquidity_score REAL DEFAULT 0,
                volatility_score REAL DEFAULT 0,
                market_dominance REAL DEFAULT 0,
                market_cap_category TEXT DEFAULT "",
                volume_category TEXT DEFAULT "",
                market_data_timestamp TEXT DEFAULT "",
                trading_session TEXT DEFAULT ""
            )
        ''')
        
        # Create performance_metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                total_pnl REAL DEFAULT 0,
                win_rate REAL DEFAULT 0,
                profit_factor REAL DEFAULT 0,
                max_drawdown REAL DEFAULT 0,
                balance REAL DEFAULT 200.0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert initial performance metrics with $200 balance
        cursor.execute('''
            INSERT OR REPLACE INTO performance_metrics (date, balance, updated_at)
            VALUES (?, 200.0, ?)
        ''', (datetime.now().strftime('%Y-%m-%d'), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ {db_path} created successfully with complete schema")
        return True
        
    except Exception as e:
        print(f"   ❌ Error creating {db_path}: {e}")
        return False

def reset_notifications():
    """Reset notifications file"""
    try:
        with open("notifications.json", "w") as f:
            json.dump([], f)
        print("   ✅ Notifications cleared")
    except Exception as e:
        print(f"   ❌ Error clearing notifications: {e}")

def reset_trading_control():
    """Reset trading control to enabled state"""
    try:
        trading_control = {
            "enabled": True,
            "status_text": "Trading Enabled",
            "last_updated": datetime.now().isoformat(),
            "updated_by": "system_reset"
        }
        with open("trading_control.json", "w") as f:
            json.dump(trading_control, f, indent=2)
        print("   ✅ Trading control reset to enabled")
    except Exception as e:
        print(f"   ❌ Error resetting trading control: {e}")

def main():
    print("🔧 COMPLETE SYSTEM RESET")
    print("=" * 60)
    
    # Stop any running processes first
    print("🛑 Stopping any running processes...")
    
    # Force delete and recreate databases
    print("\n🗄️ Resetting databases...")
    
    # Delete old databases
    force_delete_database("dry_run_trades.db")
    force_delete_database("real_trades.db")
    
    # Wait a moment
    time.sleep(1)
    
    # Create new databases
    dry_run_success = create_complete_database("dry_run_trades.db")
    real_trades_success = create_complete_database("real_trades.db")
    
    # Reset other components
    print("\n📱 Resetting notifications...")
    reset_notifications()
    
    print("\n🎮 Resetting trading control...")
    reset_trading_control()
    
    print("\n" + "=" * 60)
    if dry_run_success and real_trades_success:
        print("✅ COMPLETE SYSTEM RESET SUCCESSFUL!")
        print("💰 Balance reset to $200")
        print("�️ All databases recreated with complete schema")
        print("� Notifications cleared")
        print("� Trading control enabled")
        print("🔄 System ready to restart")
    else:
        print("❌ SYSTEM RESET FAILED!")
        print("⚠️ Some components may not have been reset properly")

if __name__ == "__main__":
    main()