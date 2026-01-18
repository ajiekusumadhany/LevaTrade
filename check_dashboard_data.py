"""
Check dashboard data - positions, history, performance
"""
from dry_run_system import dry_run_system
import json

def check_data():
    print("📊 DASHBOARD DATA CHECK")
    print("=" * 50)
    
    # 1. Open Positions
    positions = dry_run_system.get_open_positions()
    print(f"\n🔓 OPEN POSITIONS: {len(positions)}")
    if positions:
        for pos in positions:
            print(f"   {pos['symbol']}: {pos['direction']} {pos['quantity']:.3f} @ ${pos['entry_price']:.4f}")
            print(f"   Current: ${pos['current_price']:.4f} | PnL: ${pos['unrealized_pnl']:.2f}")
    else:
        print("   No open positions")
    
    # 2. Trade History
    history = dry_run_system.get_trade_history(10)
    print(f"\n📈 TRADE HISTORY: {len(history)} trades")
    for i, trade in enumerate(history, 1):
        pnl_emoji = "🟢" if trade['pnl'] >= 0 else "🔴"
        print(f"   {i}. {pnl_emoji} {trade['symbol']} {trade['direction']}")
        print(f"      Entry: ${trade['entry_price']:.4f} → Exit: ${trade['exit_price']:.4f}")
        print(f"      PnL: ${trade['pnl']:.2f} ({trade['pnl_percentage']:.2f}%) | {trade['exit_reason']}")
        print(f"      Duration: {trade['duration_minutes']}m")
    
    # 3. Performance Metrics
    metrics = dry_run_system.get_performance_metrics()
    print(f"\n📊 PERFORMANCE METRICS:")
    print(f"   Balance: ${metrics['balance']:.2f} (Start: ${metrics['starting_balance']:.2f})")
    print(f"   Total PnL: ${metrics['total_pnl']:.2f}")
    print(f"   Total Trades: {metrics['total_trades']}")
    print(f"   Win Rate: {metrics['win_rate']:.1f}% ({metrics['winning_trades']}W/{metrics['losing_trades']}L)")
    print(f"   Max Drawdown: {metrics['max_drawdown']:.2f}%")
    print(f"   Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"   Avg Win: ${metrics['avg_win']:.2f}")
    print(f"   Avg Loss: ${metrics['avg_loss']:.2f}")

if __name__ == "__main__":
    check_data()