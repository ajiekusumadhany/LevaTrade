"""
Fix All Database Issues - Perbaiki semua masalah database
"""
import sqlite3
import os

def fix_database_completely(db_path):
    """Fix database schema completely"""
    print(f"🔧 Completely fixing {db_path}...")
    
    if not os.path.exists(db_path):
        print(f"   ❌ {db_path} not found")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check existing columns in open_positions
        cursor.execute("PRAGMA table_info(open_positions)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        print(f"   📊 Existing columns: {len(existing_columns)}")
        
        # Add all missing columns to open_positions
        required_columns = {
            'tp_price': 'REAL DEFAULT 0',
            'sl_price': 'REAL DEFAULT 0', 
            'trading_session': 'TEXT DEFAULT ""',
            'current_price': 'REAL DEFAULT 0',
            'unrealized_pnl': 'REAL DEFAULT 0',
            'position_value_usd': 'REAL DEFAULT 0',
            'margin_used': 'REAL DEFAULT 0',
            'liquidation_price': 'REAL DEFAULT 0',
            'bybit_order_id': 'TEXT DEFAULT ""',
            'indicators': 'TEXT DEFAULT ""',
            'ai_reasoning': 'TEXT DEFAULT ""',
            'session_type': 'TEXT DEFAULT ""',
            'risk_percentage': 'REAL DEFAULT 0',
            'atr_value': 'REAL DEFAULT 0',
            'tp_atr_multiplier': 'REAL DEFAULT 0',
            'sl_atr_multiplier': 'REAL DEFAULT 0',
            'market_cap': 'REAL DEFAULT 0',
            'total_volume_24h': 'REAL DEFAULT 0',
            'market_cap_category': 'TEXT DEFAULT ""',
            'volume_category': 'TEXT DEFAULT ""',
            'correlation_group': 'TEXT DEFAULT ""',
            'psychological_factor': 'REAL DEFAULT 1.0',
            'entry_confidence': 'REAL DEFAULT 0',
            'max_favorable_excursion': 'REAL DEFAULT 0',
            'max_adverse_excursion': 'REAL DEFAULT 0',
            'price_change_percentage': 'REAL DEFAULT 0',
            'last_update_time': 'TEXT DEFAULT ""',
            'duration_minutes': 'INTEGER DEFAULT 0',
            'peak_pnl': 'REAL DEFAULT 0',
            'drawdown_from_peak': 'REAL DEFAULT 0',
            'trailing_stop_price': 'REAL DEFAULT 0',
            'is_trailing_active': 'INTEGER DEFAULT 0'
        }
        
        added_count = 0
        for col_name, col_def in required_columns.items():
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE open_positions ADD COLUMN {col_name} {col_def}")
                    added_count += 1
                    print(f"   ✅ Added: {col_name}")
                except Exception as e:
                    if "duplicate column name" not in str(e).lower():
                        print(f"   ⚠️ Error adding {col_name}: {e}")
        
        # Check and fix trade_history table
        cursor.execute("PRAGMA table_info(trade_history)")
        history_columns = [col[1] for col in cursor.fetchall()]
        
        history_required = {
            'trading_session': 'TEXT DEFAULT ""',
            'indicators_passed': 'TEXT DEFAULT ""',
            'indicators_failed': 'TEXT DEFAULT ""',
            'ai_entry_reasoning': 'TEXT DEFAULT ""',
            'ai_exit_reasoning': 'TEXT DEFAULT ""',
            'market_cap': 'REAL DEFAULT 0',
            'total_volume_24h': 'REAL DEFAULT 0',
            'market_cap_category': 'TEXT DEFAULT ""',
            'volume_category': 'TEXT DEFAULT ""',
            'session_type': 'TEXT DEFAULT ""',
            'risk_percentage': 'REAL DEFAULT 0',
            'atr_value': 'REAL DEFAULT 0'
        }
        
        for col_name, col_def in history_required.items():
            if col_name not in history_columns:
                try:
                    cursor.execute(f"ALTER TABLE trade_history ADD COLUMN {col_name} {col_def}")
                    added_count += 1
                    print(f"   ✅ Added to trade_history: {col_name}")
                except Exception as e:
                    if "duplicate column name" not in str(e).lower():
                        print(f"   ⚠️ Error adding to trade_history {col_name}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ {db_path} fixed - {added_count} columns added")
        
    except Exception as e:
        print(f"   ❌ Error fixing {db_path}: {e}")

def main():
    print("🔧 FIXING ALL DATABASE ISSUES")
    print("=" * 50)
    
    # Fix both databases
    fix_database_completely("dry_run_trades.db")
    fix_database_completely("real_trades.db")
    
    print("\n✅ All database issues fixed!")
    print("🔄 Please restart the bot and dashboard")

if __name__ == "__main__":
    main()