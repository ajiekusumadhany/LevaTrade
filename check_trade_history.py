"""
Check trade history dari dry run system
"""
from dry_run_system import dry_run_system

def check_history():
    print("📊 Trade History:")
    print("-" * 60)
    
    # Get trade history
    trades = dry_run_system.get_trade_history(10)
    
    if not trades:
        print("No trades found")
        return
    
    for trade in trades:
        pnl_emoji = "🟢" if trade['pnl'] >= 0 else "🔴"
        print(f"{pnl_emoji} {trade['symbol']} {trade['direction']}")
        print(f"   Entry: ${trade['entry_price']:.4f} -> Exit: ${trade['exit_price']:.4f}")
        print(f"   PnL: ${trade['pnl']:.2f} ({trade['pnl_percentage']:.2f}%)")
        print(f"   Exit Reason: {trade['exit_reason']}")
        print(f"   Duration: {trade['duration_minutes']} minutes")
        print(f"   Indicators: {trade['indicators']}")
        print("-" * 40)
    
    # Get performance metrics
    print("\n📈 Performance Summary:")
    metrics = dry_run_system.get_performance_metrics()
    print(f"Balance: ${metrics['balance']:.2f}")
    print(f"Total PnL: ${metrics['total_pnl']:.2f}")
    print(f"Win Rate: {metrics['win_rate']:.1f}%")
    print(f"Total Trades: {metrics['total_trades']}")
    print(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")

if __name__ == "__main__":
    check_history()