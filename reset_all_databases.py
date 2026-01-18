"""
Reset semua database trading karena formula position sizing yang salah
"""
import os
import sqlite3
from datetime import datetime

def reset_database(db_path, db_name):
    """Reset database dengan backup data lama"""
    if os.path.exists(db_path):
        # Backup database lama
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.rename(db_path, backup_path)
        print(f"✅ {db_name} backed up to: {backup_path}")
    else:
        print(f"ℹ️  {db_name} tidak ditemukan, skip backup")

def main():
    print("🗑️  RESET ALL TRADING DATABASES")
    print("=" * 50)
    print("⚠️  ALASAN: Formula position sizing salah total!")
    print("   - Position size terlalu besar (10x-100x dari yang seharusnya)")
    print("   - PnL percentage salah karena margin calculation salah")
    print("   - Semua history data tidak valid")
    print()
    
    # Konfirmasi
    confirm = input("❓ Yakin mau reset semua database? (ketik 'YES' untuk konfirmasi): ")
    if confirm != 'YES':
        print("❌ Reset dibatalkan")
        return
    
    print("\n🔄 Memulai reset...")
    
    # Reset dry run database
    reset_database("dry_run_trades.db", "Dry Run Database")
    
    # Reset real trade database  
    reset_database("real_trades.db", "Real Trade Database")
    
    print("\n✅ RESET SELESAI!")
    print("📊 Database baru akan dibuat otomatis saat bot jalan")
    print("🎯 Sekarang position sizing sudah benar:")
    print("   - Max margin per trade: $10 (1% dari $1000)")
    print("   - Position size akan sesuai dengan margin + leverage")
    print("   - PnL percentage akan akurat berdasarkan margin")
    print()
    print("🚀 Silakan restart bot untuk mulai trading dengan formula yang benar!")

if __name__ == "__main__":
    main()