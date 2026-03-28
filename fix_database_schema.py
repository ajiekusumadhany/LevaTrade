"""
Fix Database Schema - Perbaiki schema database yang missing columns
"""
import sqlite3
import os

def fix_database_schema(db_path):
    """Fix database schema by adding missing columns"""
    print(f"🔧 Fixing schema for {db_path}...")
    
    if not os.path.exists(db_path):
        print(f"   ❌ {db_path} not found")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if tp_price column exists
        cursor.execute("PRAGMA table_info(open_positions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        missing_columns = []
        required_columns = {
            'tp_price': 'REAL DEFAULT 0',
            'sl_price': 'REAL DEFAULT 0',
            'current_price': 'REAL DEFAULT 0',
            'unrealized_pnl': 'REAL DEFAULT 0',
            'position_value_usd': 'REAL DEFAULT 0',
            'margin_used': 'REAL DEFAULT 0',
            'liquidation_price': 'REAL DEFAULT 0',
            'bybit_order_id': 'TEXT',
            'indicators': 'TEXT',
            'ai_reasoning': 'TEXT',
            'session_type': 'TEXT',
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
            'last_update_time': 'TEXT',
            'duration_minutes': 'INTEGER DEFAULT 0',
            'peak_pnl': 'REAL DEFAULT 0',
            'drawdown_from_peak': 'REAL DEFAULT 0',
            'trailing_stop_price': 'REAL DEFAULT 0',
            'is_trailing_active': 'INTEGER DEFAULT 0'
        }
        
        # Add missing columns
        for col_name, col_type in required_columns.items():
            if col_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE open_positions ADD COLUMN {col_name} {col_type}")
                    missing_columns.append(col_name)
                except Exception as e:
                    if "duplicate column name" not in str(e).lower():
                        print(f"   ⚠️ Error adding {col_name}: {e}")
        
        if missing_columns:
            print(f"   ✅ Added columns: {', '.join(missing_columns)}")
        else:
            print(f"   ✅ Schema already complete")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Error fixing {db_path}: {e}")

def main():
    print("🔧 FIXING DATABASE SCHEMAS")
    print("=" * 50)
    
    # Fix both databases
    fix_database_schema("dry_run_trades.db")
    fix_database_schema("real_trades.db")
    
    print("\n✅ Database schema fixes complete!")

if __name__ == "__main__":
    main()