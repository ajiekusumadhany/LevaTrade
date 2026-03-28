"""
Check Database Status - Cek kondisi database setelah reset
"""
import sqlite3
import os
from datetime import datetime

def check_database(db_path):
    """Check database content"""
    print(f"\n🔍 Checking {db_path}...")
    
    if not os.path.exists(db_path):
        print(f"   ❌ Database {db_path} not found")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if not tables:
            print(f"   ⚠️ No tables found in {db_path}")
            conn.close()
            return
        
        print(f"   📊 Tables found: {[t[0] for t in tables]}")
        
        # Check each table
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   - {table_name}: {count} records")
            
            # Show sample data if exists
            if count > 0 and count <= 5:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                rows = cursor.fetchall()
                for i, row in enumerate(rows):
                    print(f"     Row {i+1}: {str(row)[:100]}...")
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Error checking {db_path}: {e}")

def main():
    print("🔍 DATABASE STATUS CHECK")
    print("=" * 50)
    
    # Check all database files
    db_files = [
        "dry_run_trades.db",
        "real_trades.db",
        "strategy_performance.db", 
        "psychological_state.db"
    ]
    
    for db_file in db_files:
        check_database(db_file)
    
    print("\n" + "=" * 50)
    print("✅ Database check complete")

if __name__ == "__main__":
    main()