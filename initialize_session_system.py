#!/usr/bin/env python3
"""
Initialize Trading Session System
Menambahkan kolom trading_session ke database dan mengupdate data yang sudah ada
"""
from trading_session_system import TradingSessionAnalyzer

def main():
    print("🚀 Initializing Trading Session Analysis System...")
    
    analyzer = TradingSessionAnalyzer()
    
    # Step 1: Add session columns to databases
    print("\n1️⃣ Adding session columns to databases...")
    analyzer.add_session_column_to_database()
    
    # Step 2: Update existing records with session data
    print("\n2️⃣ Updating existing records with session data...")
    analyzer.update_existing_sessions()
    
    # Step 3: Test session performance analysis
    print("\n3️⃣ Testing session performance analysis...")
    
    # Test dry run
    dry_performance = analyzer.get_session_performance("dry_run", 30)
    if dry_performance.get('success'):
        print(f"   ✅ Dry Run: Analyzed {dry_performance['total_trades']} trades")
        for session_key, stats in dry_performance['sessions'].items():
            if stats['total_trades'] > 0:
                print(f"      {stats['color']} {stats['name']}: {stats['total_trades']} trades, {stats['win_rate']:.1f}% WR, ${stats['total_pnl']:.2f} PnL")
    else:
        print(f"   ❌ Dry Run Error: {dry_performance.get('error')}")
    
    # Test real trade
    real_performance = analyzer.get_session_performance("real_trade", 30)
    if real_performance.get('success'):
        print(f"   ✅ Real Trade: Analyzed {real_performance['total_trades']} trades")
        for session_key, stats in real_performance['sessions'].items():
            if stats['total_trades'] > 0:
                print(f"      {stats['color']} {stats['name']}: {stats['total_trades']} trades, {stats['win_rate']:.1f}% WR, ${stats['total_pnl']:.2f} PnL")
    else:
        print(f"   ❌ Real Trade Error: {real_performance.get('error')}")
    
    # Step 4: Show best/worst sessions
    print("\n4️⃣ Best/Worst Session Analysis...")
    
    best_worst = analyzer.get_best_worst_sessions("dry_run", 30)
    if best_worst.get('success'):
        if best_worst.get('best_win_rate'):
            session_key, session_data = best_worst['best_win_rate']
            print(f"   🏆 Best Win Rate: {session_data['color']} {session_data['name']} - {session_data['win_rate']:.1f}%")
        
        if best_worst.get('most_profitable'):
            session_key, session_data = best_worst['most_profitable']
            print(f"   💰 Most Profitable: {session_data['color']} {session_data['name']} - ${session_data['total_pnl']:.2f}")
    
    print("\n✅ Trading Session Analysis System initialized successfully!")
    print("\n📊 You can now:")
    print("   • View session performance in the dashboard")
    print("   • Access session analysis via the sidebar menu")
    print("   • Use API endpoints for session data")
    print("   • Ask AI about session-specific performance")

if __name__ == "__main__":
    main()