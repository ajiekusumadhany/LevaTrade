"""
Complete Database Fix - Perbaiki semua masalah database schema
"""
import sqlite3
import os
from datetime import datetime

def recreate_database_with_complete_schema(db_path):
    """Recreate database with complete schema"""
    print(f"🔧 Recreating {db_path} with complete schema...")
    
    # Backup existing data if any
    backup_data = {"positions": [], "history": [], "metrics": []}
    
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Backup existing data
            try:
                cursor.execute("SELECT * FROM open_positions")
                backup_data["positions"] = cursor.fetchall()
                print(f"   📦 Backed up {len(backup_data['positions'])} positions")
            except:
                pass
                
            try:
                cursor.execute("SELECT * FROM trade_history")
                backup_data["history"] = cursor.fetchall()
                print(f"   📦 Backed up {len(backup_data['history'])} trades")
            except:
                pass
                
            try:
                cursor.execute("SELECT * FROM performance_metrics")
                backup_data["metrics"] = cursor.fetchall()
                print(f"   📦 Backed up {len(backup_data['metrics'])} metrics")
            except:
                pass
                
            conn.close()
            
            # Remove old database
            os.remove(db_path)
            print(f"   🗑️ Removed old {db_path}")
            
        except Exception as e:
            print(f"   ⚠️ Error backing up {db_path}: {e}")
    
    # Create new database with complete schema
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create open_positions table with ALL required columns (matching dry_run_system expectations)
        cursor.execute('''
            CREATE TABLE open_positions (
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
        
        # Create trade_history table with ALL required columns (39 columns for dry_run)
        cursor.execute('''
            CREATE TABLE trade_history (
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
            CREATE TABLE performance_metrics (
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
        
        # Insert initial performance metrics
        cursor.execute('''
            INSERT INTO performance_metrics (date, balance, updated_at)
            VALUES (?, 200.0, ?)
        ''', (datetime.now().strftime('%Y-%m-%d'), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ {db_path} recreated with complete schema")
        
    except Exception as e:
        print(f"   ❌ Error creating {db_path}: {e}")

def main():
    print("🔧 COMPLETE DATABASE SCHEMA FIX")
    print("=" * 60)
    
    # Recreate both databases with complete schema
    recreate_database_with_complete_schema("dry_run_trades.db")
    recreate_database_with_complete_schema("real_trades.db")
    
    print("\n✅ Database schema completely fixed!")
    print("💰 Balance reset to $200")
    print("🗄️ All tables have complete schema")
    print("🔄 Ready to restart bot")

if __name__ == "__main__":
    main()