"""
Monitor Strategy Improvements - Track impact of TP/SL ratio fix
"""
import sqlite3
from datetime import datetime, timedelta
import json

def monitor_recent_performance():
    """Monitor performa setelah perbaikan TP/SL ratio"""
    
    print("📊 MONITORING STRATEGY IMPROVEMENTS")
    print("=" * 60)
    
    conn = sqlite3.connect('dry_run_trades.db')
    cursor = conn.cursor()
    
    # Get trades from last 2 hours (after TP/SL fix)
    two_hours_ago = (datetime.now() - timedelta(hours=2)).isoformat()
    
    print(f"\n🕐 RECENT PERFORMANCE (Last 2 hours)")
    print("-" * 40)
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total_trades,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
            AVG(pnl) as avg_pnl,
            AVG(pnl_percentage) as avg_pnl_pct,
            SUM(pnl) as total_pnl
        FROM trade_history 
        WHERE entry_time > ?
    ''', (two_hours_ago,))
    
    recent_stats = cursor.fetchone()
    
    if recent_stats and recent_stats[0] > 0:
        total, wins, avg_pnl, avg_pnl_pct, total_pnl = recent_stats
        win_rate = (wins / total) * 100 if total > 0 else 0
        
        print(f"Recent Trades: {total}")
        print(f"Win Rate: {win_rate:.1f}%")
        print(f"Avg PnL: ${avg_pnl:.2f} ({avg_pnl_pct:.2f}%)")
        print(f"Total PnL: ${total_pnl:.2f}")
        
        # Compare with historical
        cursor.execute('''
            SELECT 
                AVG(pnl) as historical_avg_pnl,
                AVG(CASE WHEN pnl > 0 THEN 1.0 ELSE 0.0 END) * 100 as historical_wr
            FROM trade_history 
            WHERE entry_time < ?
        ''', (two_hours_ago,))
        
        historical = cursor.fetchone()
        if historical and historical[0] is not None:
            hist_avg_pnl, hist_wr = historical
            
            print(f"\n📈 COMPARISON:")
            print(f"Win Rate: {win_rate:.1f}% vs {hist_wr:.1f}% (historical)")
            print(f"Avg PnL: ${avg_pnl:.2f} vs ${hist_avg_pnl:.2f} (historical)")
            
            if avg_pnl > hist_avg_pnl:
                improvement = ((avg_pnl - hist_avg_pnl) / abs(hist_avg_pnl)) * 100
                print(f"✅ IMPROVEMENT: +{improvement:.1f}% in avg PnL")
            else:
                decline = ((hist_avg_pnl - avg_pnl) / abs(hist_avg_pnl)) * 100
                print(f"⚠️ DECLINE: -{decline:.1f}% in avg PnL")
        else:
            print(f"\n📈 COMPARISON: No historical data available")
    else:
        print("❌ No recent trades to analyze")
    
    # Check current open positions with new TP/SL
    print(f"\n🔄 CURRENT OPEN POSITIONS")
    print("-" * 40)
    
    cursor.execute('''
        SELECT symbol, direction, entry_price, tp_price, sl_price, entry_time
        FROM open_positions 
        WHERE entry_time > ?
        ORDER BY entry_time DESC
    ''', (two_hours_ago,))
    
    recent_positions = cursor.fetchall()
    
    if recent_positions:
        print("Recent positions with improved TP/SL ratio:")
        for symbol, direction, entry, tp, sl, entry_time in recent_positions:
            # Calculate actual TP/SL ratio
            if direction == "LONG":
                tp_distance = tp - entry
                sl_distance = entry - sl
            else:  # SHORT
                tp_distance = entry - tp
                sl_distance = sl - entry
            
            ratio = tp_distance / sl_distance if sl_distance > 0 else 0
            
            print(f"  {symbol} {direction}: Entry ${entry:.6f}, TP ${tp:.6f}, SL ${sl:.6f}")
            print(f"    Risk/Reward Ratio: {ratio:.2f}:1")
            print(f"    Opened: {entry_time}")
            print()
    else:
        print("No recent positions with new TP/SL")
    
    conn.close()

def check_tp_sl_effectiveness():
    """Check if new TP/SL ratio is more effective"""
    
    print(f"\n🎯 TP/SL RATIO EFFECTIVENESS")
    print("-" * 40)
    
    conn = sqlite3.connect('dry_run_trades.db')
    cursor = conn.cursor()
    
    # Analyze TP vs SL hits
    cursor.execute('''
        SELECT 
            exit_reason,
            COUNT(*) as count,
            AVG(pnl) as avg_pnl,
            AVG(pnl_percentage) as avg_pnl_pct
        FROM trade_history
        WHERE exit_reason IN ('TP_HIT', 'SL_HIT')
        GROUP BY exit_reason
    ''')
    
    exit_analysis = cursor.fetchall()
    
    tp_avg = sl_avg = 0
    tp_count = sl_count = 0
    
    for exit_reason, count, avg_pnl, avg_pnl_pct in exit_analysis:
        print(f"{exit_reason}: {count} trades, avg ${avg_pnl:.2f} ({avg_pnl_pct:.2f}%)")
        
        if exit_reason == 'TP_HIT':
            tp_avg = avg_pnl
            tp_count = count
        elif exit_reason == 'SL_HIT':
            sl_avg = avg_pnl
            sl_count = count
    
    if tp_avg > 0 and sl_avg < 0:
        actual_ratio = abs(tp_avg / sl_avg)
        print(f"\nActual Risk/Reward Ratio: {actual_ratio:.2f}:1")
        
        if actual_ratio >= 1.8:
            print("✅ Good risk/reward ratio achieved")
        elif actual_ratio >= 1.5:
            print("⚠️ Acceptable risk/reward ratio")
        else:
            print("❌ Poor risk/reward ratio - needs improvement")
    
    conn.close()

def generate_improvement_report():
    """Generate report on improvement progress"""
    
    print(f"\n📋 IMPROVEMENT PROGRESS REPORT")
    print("=" * 60)
    
    print("✅ IMPLEMENTED FIXES:")
    print("1. TP/SL Ratio: 0.8x/0.6x → 1.2x/0.6x (2:1 ratio)")
    print("2. Risk/Reward: 1.33:1 → 2:1 (50% improvement)")
    
    print(f"\n📊 EXPECTED IMPACT:")
    print("- Better profit capture on winning trades")
    print("- Improved overall PnL despite same win rate")
    print("- More sustainable trading strategy")
    
    print(f"\n🎯 MONITORING CHECKLIST:")
    checklist = [
        "[ ] Monitor win rate (should maintain 55-65%)",
        "[ ] Track average PnL per trade (target: positive)",
        "[ ] Verify TP/SL ratio in new positions (should be 2:1)",
        "[ ] Compare recent vs historical performance",
        "[ ] Watch for TP hit frequency vs SL hit frequency"
    ]
    
    for item in checklist:
        print(f"   {item}")
    
    print(f"\n⏰ NEXT REVIEW:")
    print("- Monitor for 24 hours")
    print("- Collect minimum 10 trades for statistical significance")
    print("- Compare performance metrics")
    print("- Decide on next optimization steps")

if __name__ == "__main__":
    try:
        monitor_recent_performance()
        check_tp_sl_effectiveness()
        generate_improvement_report()
    except Exception as e:
        print(f"❌ Error during monitoring: {e}")
        import traceback
        traceback.print_exc()