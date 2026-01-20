"""
Complete System Reset - Reset databases, notifications, balance to $200
"""
import os
import sqlite3
import json
from datetime import datetime

def reset_databases():
    """Reset all database files"""
    print("🗄️ Resetting databases...")
    
    # Database files to reset
    db_files = [
        "dry_run_trades.db",
        "real_trades.db", 
        "strategy_performance.db",
        "psychological_state.db"
    ]
    
    for db_file in db_files:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
                print(f"   ✅ Deleted {db_file}")
            except Exception as e:
                print(f"   ❌ Error deleting {db_file}: {e}")
        else:
            print(f"   ℹ️ {db_file} not found (already clean)")

def reset_notifications():
    """Reset notifications file"""
    print("📡 Resetting notifications...")
    
    try:
        # Clear notifications.json
        with open("notifications.json", "w") as f:
            json.dump([], f)
        print("   ✅ Cleared notifications.json")
    except Exception as e:
        print(f"   ❌ Error clearing notifications: {e}")

def reset_balance():
    """Reset balance to $200 in .env file"""
    print("💰 Setting balance to $200...")
    
    try:
        # Read current .env file
        env_lines = []
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                env_lines = f.readlines()
        
        # Update or add BALANCE_USD line
        balance_found = False
        for i, line in enumerate(env_lines):
            if line.startswith("BALANCE_USD="):
                env_lines[i] = "BALANCE_USD=200\n"
                balance_found = True
                break
        
        if not balance_found:
            env_lines.append("BALANCE_USD=200\n")
        
        # Write back to .env
        with open(".env", "w") as f:
            f.writelines(env_lines)
        
        print("   ✅ Balance set to $200 in .env")
        
    except Exception as e:
        print(f"   ❌ Error setting balance: {e}")

def reset_trading_control():
    """Reset trading control to enabled state"""
    print("🎛️ Resetting trading control...")
    
    try:
        control_data = {
            "enabled": True,
            "last_updated": datetime.now().isoformat(),
            "updated_by": "reset_system"
        }
        
        with open("trading_control.json", "w") as f:
            json.dump(control_data, f, indent=2)
        
        print("   ✅ Trading control reset (enabled)")
        
    except Exception as e:
        print(f"   ❌ Error resetting trading control: {e}")

def initialize_fresh_databases():
    """Initialize fresh database structures"""
    print("🔧 Initializing fresh databases...")
    
    try:
        # Initialize dry run database
        conn = sqlite3.connect("dry_run_trades.db")
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS open_positions (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                quantity REAL NOT NULL,
                leverage INTEGER NOT NULL,
                entry_time TEXT NOT NULL,
                stop_loss REAL,
                take_profit REAL,
                unrealized_pnl REAL DEFAULT 0,
                position_value_usd REAL DEFAULT 0,
                margin_used REAL DEFAULT 0,
                liquidation_price REAL DEFAULT 0,
                bybit_order_id TEXT,
                indicators TEXT,
                ai_reasoning TEXT,
                session_type TEXT,
                risk_percentage REAL DEFAULT 0,
                atr_value REAL DEFAULT 0,
                tp_atr_multiplier REAL DEFAULT 0,
                sl_atr_multiplier REAL DEFAULT 0,
                market_cap REAL DEFAULT 0,
                total_volume_24h REAL DEFAULT 0,
                market_cap_category TEXT DEFAULT '',
                volume_category TEXT DEFAULT '',
                correlation_group TEXT DEFAULT '',
                psychological_factor REAL DEFAULT 1.0,
                entry_confidence REAL DEFAULT 0,
                max_favorable_excursion REAL DEFAULT 0,
                max_adverse_excursion REAL DEFAULT 0,
                current_price REAL DEFAULT 0,
                price_change_percentage REAL DEFAULT 0,
                last_update_time TEXT,
                duration_minutes INTEGER DEFAULT 0,
                peak_pnl REAL DEFAULT 0,
                drawdown_from_peak REAL DEFAULT 0,
                trailing_stop_price REAL DEFAULT 0,
                is_trailing_active INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_history (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL NOT NULL,
                quantity REAL NOT NULL,
                leverage INTEGER NOT NULL,
                entry_time TEXT NOT NULL,
                exit_time TEXT NOT NULL,
                exit_reason TEXT NOT NULL,
                pnl REAL NOT NULL,
                pnl_percentage REAL NOT NULL,
                indicators TEXT,
                position_value_usd REAL DEFAULT 0,
                duration_minutes INTEGER DEFAULT 0,
                bybit_entry_order_id TEXT,
                bybit_exit_order_id TEXT,
                fees_paid REAL DEFAULT 0,
                ai_entry_reasoning TEXT DEFAULT '',
                ai_exit_reasoning TEXT DEFAULT ''
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_pnl REAL DEFAULT 0,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                win_rate REAL DEFAULT 0,
                max_drawdown REAL DEFAULT 0,
                profit_factor REAL DEFAULT 0,
                sharpe_ratio REAL DEFAULT 0,
                balance REAL DEFAULT 0,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("   ✅ Dry run database initialized")
        
        # Initialize real trades database (same structure)
        conn = sqlite3.connect("real_trades.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS open_positions (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                quantity REAL NOT NULL,
                leverage INTEGER NOT NULL,
                entry_time TEXT NOT NULL,
                stop_loss REAL,
                take_profit REAL,
                unrealized_pnl REAL DEFAULT 0,
                position_value_usd REAL DEFAULT 0,
                margin_used REAL DEFAULT 0,
                liquidation_price REAL DEFAULT 0,
                bybit_order_id TEXT,
                indicators TEXT,
                ai_reasoning TEXT,
                session_type TEXT,
                risk_percentage REAL DEFAULT 0,
                atr_value REAL DEFAULT 0,
                tp_atr_multiplier REAL DEFAULT 0,
                sl_atr_multiplier REAL DEFAULT 0,
                market_cap REAL DEFAULT 0,
                total_volume_24h REAL DEFAULT 0,
                market_cap_category TEXT DEFAULT '',
                volume_category TEXT DEFAULT '',
                correlation_group TEXT DEFAULT '',
                psychological_factor REAL DEFAULT 1.0,
                entry_confidence REAL DEFAULT 0,
                max_favorable_excursion REAL DEFAULT 0,
                max_adverse_excursion REAL DEFAULT 0,
                current_price REAL DEFAULT 0,
                price_change_percentage REAL DEFAULT 0,
                last_update_time TEXT,
                duration_minutes INTEGER DEFAULT 0,
                peak_pnl REAL DEFAULT 0,
                drawdown_from_peak REAL DEFAULT 0,
                trailing_stop_price REAL DEFAULT 0,
                is_trailing_active INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_history (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL NOT NULL,
                quantity REAL NOT NULL,
                leverage INTEGER NOT NULL,
                entry_time TEXT NOT NULL,
                exit_time TEXT NOT NULL,
                exit_reason TEXT NOT NULL,
                pnl REAL NOT NULL,
                pnl_percentage REAL NOT NULL,
                indicators TEXT,
                position_value_usd REAL DEFAULT 0,
                duration_minutes INTEGER DEFAULT 0,
                bybit_entry_order_id TEXT,
                bybit_exit_order_id TEXT,
                fees_paid REAL DEFAULT 0,
                ai_entry_reasoning TEXT DEFAULT '',
                ai_exit_reasoning TEXT DEFAULT ''
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_pnl REAL DEFAULT 0,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                win_rate REAL DEFAULT 0,
                max_drawdown REAL DEFAULT 0,
                profit_factor REAL DEFAULT 0,
                sharpe_ratio REAL DEFAULT 0,
                balance REAL DEFAULT 0,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("   ✅ Real trades database initialized")
        
    except Exception as e:
        print(f"   ❌ Error initializing databases: {e}")

def run_complete_reset():
    """Run complete system reset"""
    print("🔄 STARTING COMPLETE SYSTEM RESET")
    print("=" * 50)
    
    # Step 1: Reset databases
    reset_databases()
    
    # Step 2: Reset notifications
    reset_notifications()
    
    # Step 3: Reset balance to $200
    reset_balance()
    
    # Step 4: Reset trading control
    reset_trading_control()
    
    # Step 5: Initialize fresh databases
    initialize_fresh_databases()
    
    print("\n" + "=" * 50)
    print("✅ COMPLETE SYSTEM RESET FINISHED")
    print("💰 Balance: $200")
    print("🗄️ Databases: Fresh and empty")
    print("📡 Notifications: Cleared")
    print("🎛️ Trading: Enabled")
    print("\n🚀 System ready for fresh start!")
    print("📱 You can now test /start command in Telegram")

if __name__ == "__main__":
    run_complete_reset()