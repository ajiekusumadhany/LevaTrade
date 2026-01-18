#!/usr/bin/env python3
"""
Fix Database Schema - Add missing ai_entry_reasoning column
"""
import sqlite3
import os

def fix_dry_run_database():
    """Add missing ai_entry_reasoning column to dry run database"""
    db_path = "dry_run_trades.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database {db_path} not found")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if ai_entry_reasoning column exists in open_positions
        cursor.execute("PRAGMA table_info(open_positions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'ai_entry_reasoning' not in columns:
            print("🔧 Adding ai_entry_reasoning column to open_positions...")
            cursor.execute('ALTER TABLE open_positions ADD COLUMN ai_entry_reasoning TEXT DEFAULT ""')
            print("✅ Added ai_entry_reasoning column to open_positions")
        else:
            print("✅ ai_entry_reasoning column already exists in open_positions")
        
        # Check if ai_entry_reasoning and ai_exit_reasoning columns exist in trade_history
        cursor.execute("PRAGMA table_info(trade_history)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'ai_entry_reasoning' not in columns:
            print("🔧 Adding ai_entry_reasoning column to trade_history...")
            cursor.execute('ALTER TABLE trade_history ADD COLUMN ai_entry_reasoning TEXT DEFAULT ""')
            print("✅ Added ai_entry_reasoning column to trade_history")
        else:
            print("✅ ai_entry_reasoning column already exists in trade_history")
            
        if 'ai_exit_reasoning' not in columns:
            print("🔧 Adding ai_exit_reasoning column to trade_history...")
            cursor.execute('ALTER TABLE trade_history ADD COLUMN ai_exit_reasoning TEXT DEFAULT ""')
            print("✅ Added ai_exit_reasoning column to trade_history")
        else:
            print("✅ ai_exit_reasoning column already exists in trade_history")
        
        conn.commit()
        print(f"✅ Dry run database schema updated successfully")
        
    except Exception as e:
        print(f"❌ Error updating dry run database: {e}")
        conn.rollback()
    finally:
        conn.close()

def fix_real_trade_database():
    """Add missing ai_entry_reasoning column to real trade database"""
    db_path = "real_trades.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database {db_path} not found")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if ai_entry_reasoning column exists in open_positions
        cursor.execute("PRAGMA table_info(open_positions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'ai_entry_reasoning' not in columns:
            print("🔧 Adding ai_entry_reasoning column to real trade open_positions...")
            cursor.execute('ALTER TABLE open_positions ADD COLUMN ai_entry_reasoning TEXT DEFAULT ""')
            print("✅ Added ai_entry_reasoning column to real trade open_positions")
        else:
            print("✅ ai_entry_reasoning column already exists in real trade open_positions")
        
        # Check if ai_entry_reasoning and ai_exit_reasoning columns exist in trade_history
        cursor.execute("PRAGMA table_info(trade_history)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'ai_entry_reasoning' not in columns:
            print("🔧 Adding ai_entry_reasoning column to real trade trade_history...")
            cursor.execute('ALTER TABLE trade_history ADD COLUMN ai_entry_reasoning TEXT DEFAULT ""')
            print("✅ Added ai_entry_reasoning column to real trade trade_history")
        else:
            print("✅ ai_entry_reasoning column already exists in real trade trade_history")
            
        if 'ai_exit_reasoning' not in columns:
            print("🔧 Adding ai_exit_reasoning column to real trade trade_history...")
            cursor.execute('ALTER TABLE trade_history ADD COLUMN ai_exit_reasoning TEXT DEFAULT ""')
            print("✅ Added ai_exit_reasoning column to real trade trade_history")
        else:
            print("✅ ai_exit_reasoning column already exists in real trade trade_history")
        
        conn.commit()
        print(f"✅ Real trade database schema updated successfully")
        
    except Exception as e:
        print(f"❌ Error updating real trade database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 Fixing database schema...")
    print("=" * 50)
    
    # Fix dry run database
    print("\n📊 Fixing Dry Run Database:")
    fix_dry_run_database()
    
    # Fix real trade database
    print("\n💰 Fixing Real Trade Database:")
    fix_real_trade_database()
    
    print("\n" + "=" * 50)
    print("✅ Database schema fix completed!")
    print("🚀 You can now restart the trading bot")