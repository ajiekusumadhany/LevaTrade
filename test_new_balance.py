#!/usr/bin/env python3
"""
Test balance baru setelah reset
"""
from dry_run_system import dry_run_system

def test_new_balance():
    print("=== NEW BALANCE TEST ===")
    print("=" * 30)
    
    # Test dry run system
    balance = dry_run_system.get_current_balance()
    positions = dry_run_system.get_open_positions()
    metrics = dry_run_system.get_performance_metrics()
    
    print(f"💰 Current Balance: ${balance:.2f}")
    print(f"📊 Open Positions: {len(positions)}")
    print(f"📈 Total Trades: {metrics['total_trades']}")
    print(f"💹 Total PnL: ${metrics['total_pnl']:.2f}")
    print(f"🎯 Win Rate: {metrics['win_rate']:.1f}%")
    
    if balance == 200.0 and len(positions) == 0 and metrics['total_trades'] == 0:
        print()
        print("✅ RESET SUCCESSFUL!")
        print("🚀 Ready to start fresh trading with $200")
    else:
        print()
        print("⚠️ Reset may not be complete")
        print("Expected: Balance=$200, Positions=0, Trades=0")

if __name__ == "__main__":
    test_new_balance()