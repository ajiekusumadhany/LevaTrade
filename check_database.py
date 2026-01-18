#!/usr/bin/env python3
"""
Check Database Status - Verifikasi data setelah cleanup
"""
from dry_run_system import dry_run_system

def check_database():
    """Check current database status"""
    print("📊 Database Status Check")
    print("=" * 40)
    
    # Get current data
    positions = dry_run_system.get_open_positions()
    history = dry_run_system.get_trade_history(10)
    
    print(f"\n📈 Open Positions: {len(positions)}")
    for pos in positions:
        pnl_emoji = "🟢" if pos['unrealized_pnl'] >= 0 else "🔴"
        print(f"   {pnl_emoji} {pos['symbol']}: {pos['direction']} | PnL: ${pos['unrealized_pnl']:.2f}")
    
    print(f"\n📊 Trade History: {len(history)}")
    for trade in history[:5]:
        pnl_emoji = "🟢" if trade['pnl'] >= 0 else "🔴"
        print(f"   {pnl_emoji} {trade['symbol']}: {trade['direction']} | PnL: ${trade['pnl']:.2f}")
    
    # Check for any remaining test data
    test_symbols = [pos for pos in positions if 'TEST' in pos['symbol'] or pos['symbol'] == 'BTCUSDT']
    test_history = [trade for trade in history if 'TEST' in trade['symbol'] or trade['symbol'] == 'BTCUSDT']
    
    print(f"\n🧪 Test Data Check:")
    print(f"   Test positions: {len(test_symbols)}")
    print(f"   Test history: {len(test_history)}")
    
    if len(test_symbols) == 0 and len(test_history) == 0:
        print("   ✅ No test data found - database is clean!")
    else:
        print("   ⚠️  Some test data still exists")
        for test in test_symbols + test_history:
            print(f"      - {test['symbol']}")

if __name__ == "__main__":
    check_database()