#!/usr/bin/env python3
"""
Script untuk scan status sistem trading
"""
import json
from datetime import datetime

def scan_trading_system():
    print("🔍 SCANNING TRADING SYSTEM STATUS")
    print("=" * 50)
    
    # 1. Trading Control Status
    try:
        with open('trading_control.json', 'r') as f:
            control = json.load(f)
        
        status = "🟢 ENABLED" if control['enabled'] else "🔴 DISABLED"
        print(f"Trading Status: {status}")
        print(f"Last Updated: {control['last_updated']}")
        print(f"Updated By: {control['updated_by']}")
    except Exception as e:
        print(f"❌ Error reading trading control: {e}")
    
    print()
    
    # 2. Strategy Configuration
    try:
        with open('strategy_config.json', 'r') as f:
            config = json.load(f)
        
        print("📊 STRATEGY CONFIGURATION:")
        print(f"  Risk per trade: {config['base_risk_percent']}%")
        print(f"  Max positions: {config['max_positions']}")
        print(f"  Max total risk: {config['max_total_risk']}%")
        print(f"  Psychological protection: {'✅' if config['enable_psychological_protection'] else '❌'}")
        print(f"  Correlation protection: {'✅' if config['enable_correlation_protection'] else '❌'}")
    except Exception as e:
        print(f"❌ Error reading strategy config: {e}")
    
    print()
    
    # 3. Conditional Risk Status
    try:
        with open('conditional_risk_state.json', 'r') as f:
            risk = json.load(f)
        
        print("⚠️ CONDITIONAL RISK STATUS:")
        print(f"  Date: {risk['date']}")
        print(f"  Daily PnL: ${risk['daily_pnl']:.2f}")
        print(f"  Consecutive losses: {risk['consecutive_losses']}")
        print(f"  Last trade: {risk['last_trade_result']}")
        print(f"  NY session trades: {risk['trades_by_session']['NEWYORK']}")
    except Exception as e:
        print(f"❌ Error reading risk state: {e}")
    
    print()
    
    # 4. Dry Run System Status
    try:
        from dry_run_system import dry_run_system
        
        print("🧪 DRY RUN SYSTEM:")
        positions = dry_run_system.get_open_positions()
        metrics = dry_run_system.get_performance_metrics()
        
        print(f"  Open positions: {len(positions)}")
        print(f"  Balance: ${metrics['balance']:.2f}")
        print(f"  Total PnL: ${metrics['total_pnl']:.2f}")
        print(f"  Win rate: {metrics['win_rate']:.1f}%")
        print(f"  Total trades: {metrics['total_trades']}")
        
        if positions:
            print("  📈 Open Positions:")
            for pos in positions:
                pnl_color = "🟢" if pos.get('unrealized_pnl', 0) >= 0 else "🔴"
                print(f"    {pnl_color} {pos['symbol']} {pos['direction']} - PnL: ${pos.get('unrealized_pnl', 0):.2f}")
    except Exception as e:
        print(f"❌ Error reading dry run system: {e}")
    
    print()
    
    # 5. Real Trade System Status
    try:
        from real_trade_system import real_trade_system
        
        print("💰 REAL TRADE SYSTEM:")
        real_positions = real_trade_system.get_open_positions()
        real_metrics = real_trade_system.get_performance_metrics()
        
        print(f"  Open positions: {len(real_positions)}")
        print(f"  Balance: ${real_metrics['balance']:.2f}")
        print(f"  Total PnL: ${real_metrics['total_pnl']:.2f}")
        print(f"  Win rate: {real_metrics['win_rate']:.1f}%")
        print(f"  Total trades: {real_metrics['total_trades']}")
        
        if real_positions:
            print("  📈 Open Positions:")
            for pos in real_positions:
                pnl_color = "🟢" if pos.get('unrealized_pnl', 0) >= 0 else "🔴"
                print(f"    {pnl_color} {pos['symbol']} {pos['direction']} - PnL: ${pos.get('unrealized_pnl', 0):.2f}")
    except Exception as e:
        print(f"❌ Error reading real trade system: {e}")
    
    print()
    
    # 6. Database Files Check
    print("💾 DATABASE FILES:")
    import os
    
    db_files = [
        'dry_run_trades.db',
        'real_trades.db', 
        'strategy_performance.db',
        'psychological_state.db'
    ]
    
    for db_file in db_files:
        if os.path.exists(db_file):
            size = os.path.getsize(db_file)
            print(f"  ✅ {db_file} ({size} bytes)")
        else:
            print(f"  ❌ {db_file} (missing)")
    
    print()
    
    # 7. Restored Files Check
    print("📁 RESTORED FILES:")
    restored_files = [
        'notification_system.py',
        'overall_indicator_performance_system.py',
        'pair_performance_system.py',
        'market_data_system.py',
        'ai_analysis_system.py'
    ]
    
    for file in restored_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} (missing)")
    
    print()
    print("🔍 SCAN COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    scan_trading_system()