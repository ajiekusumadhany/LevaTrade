#!/usr/bin/env python3
"""
Script untuk reset database dry run - hapus semua data test
"""

import sqlite3
import os
from datetime import datetime

def reset_dry_run_database():
    """Reset database dry run ke kondisi awal"""
    
    db_path = "dry_run_trades.db"
    
    print("=" * 60)
    print("RESET DRY RUN DATABASE")
    print("=" * 60)
    
    if not os.path.exists(db_path):
        print("❌ Database tidak ditemukan!")
        return
    
    # Backup database dulu
    backup_path = f"dry_run_trades_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Database di-backup ke: {backup_path}")
    except Exception as e:
        print(f"⚠️  Warning: Gagal backup database: {e}")
    
    # Connect ke database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Cek data yang ada sebelum dihapus
    cursor.execute('SELECT COUNT(*) FROM open_positions')
    open_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM trade_history')
    history_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM performance_metrics')
    metrics_count = cursor.fetchone()[0]
    
    print(f"\n📊 Data yang akan dihapus:")
    print(f"   - Open Positions: {open_count}")
    print(f"   - Trade History: {history_count}")
    print(f"   - Performance Metrics: {metrics_count}")
    
    if history_count > 0:
        # Tampilkan beberapa trade terakhir
        cursor.execute('SELECT symbol, direction, pnl, exit_reason FROM trade_history ORDER BY exit_time DESC LIMIT 5')
        recent_trades = cursor.fetchall()
        print(f"\n📋 5 Trade terakhir yang akan dihapus:")
        for trade in recent_trades:
            symbol, direction, pnl, exit_reason = trade
            print(f"   - {symbol} {direction}: ${pnl:.2f} ({exit_reason})")
    
    # Konfirmasi
    confirm = input(f"\n⚠️  Yakin ingin menghapus semua data? (ketik 'YES' untuk konfirmasi): ")
    
    if confirm != 'YES':
        print("❌ Reset dibatalkan!")
        conn.close()
        return
    
    # Hapus semua data
    print(f"\n🗑️  Menghapus data...")
    
    cursor.execute('DELETE FROM open_positions')
    deleted_positions = cursor.rowcount
    print(f"   ✅ Dihapus {deleted_positions} open positions")
    
    cursor.execute('DELETE FROM trade_history')
    deleted_history = cursor.rowcount
    print(f"   ✅ Dihapus {deleted_history} trade history")
    
    cursor.execute('DELETE FROM performance_metrics')
    deleted_metrics = cursor.rowcount
    print(f"   ✅ Dihapus {deleted_metrics} performance metrics")
    
    # Reset auto-increment counters (jika ada)
    try:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('open_positions', 'trade_history', 'performance_metrics')")
    except sqlite3.OperationalError:
        # Table sqlite_sequence tidak ada, skip
        pass
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"\n🎯 RESET SELESAI!")
    print(f"   - Database telah dibersihkan")
    print(f"   - Backup tersimpan di: {backup_path}")
    print(f"   - Bot siap untuk data real yang baru")
    
    # Verifikasi database kosong
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM open_positions')
    open_after = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM trade_history')
    history_after = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM performance_metrics')
    metrics_after = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"\n✅ Verifikasi:")
    print(f"   - Open Positions: {open_after}")
    print(f"   - Trade History: {history_after}")
    print(f"   - Performance Metrics: {metrics_after}")
    
    if open_after == 0 and history_after == 0 and metrics_after == 0:
        print(f"   🎉 Database berhasil direset!")
    else:
        print(f"   ❌ Ada masalah dengan reset!")

if __name__ == "__main__":
    reset_dry_run_database()