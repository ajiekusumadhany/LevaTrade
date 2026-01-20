"""
Strategy Analysis - Analisis mendalam untuk meningkatkan trading strategy
"""
import sqlite3
import json
from datetime import datetime, timedelta
import pandas as pd
from collections import defaultdict, Counter
import re

def analyze_database():
    """Analisis komprehensif database trading"""
    
    print("🔍 ANALISIS STRATEGY TRADING")
    print("=" * 60)
    
    # Connect to database
    conn = sqlite3.connect('dry_run_trades.db')
    cursor = conn.cursor()
    
    # 1. ANALISIS PERFORMA KESELURUHAN
    print("\n📊 1. PERFORMA KESELURUHAN")
    print("-" * 40)
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total_trades,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
            SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
            AVG(pnl) as avg_pnl,
            SUM(pnl) as total_pnl,
            AVG(pnl_percentage) as avg_pnl_pct,
            AVG(duration_minutes) as avg_duration
        FROM trade_history
    ''')
    
    stats = cursor.fetchone()
    if stats and stats[0] > 0:
        total, wins, losses, avg_pnl, total_pnl, avg_pnl_pct, avg_duration = stats
        win_rate = (wins / total) * 100 if total > 0 else 0
        
        print(f"Total Trades: {total}")
        print(f"Win Rate: {win_rate:.1f}% ({wins} wins, {losses} losses)")
        print(f"Total PnL: ${total_pnl:.2f}")
        print(f"Average PnL: ${avg_pnl:.2f} ({avg_pnl_pct:.2f}%)")
        print(f"Average Duration: {avg_duration:.1f} minutes")
    else:
        print("❌ Tidak ada data trade history")
        return
    
    # 2. ANALISIS PER SYMBOL
    print("\n📈 2. ANALISIS PER SYMBOL")
    print("-" * 40)
    
    cursor.execute('''
        SELECT 
            symbol,
            COUNT(*) as trades,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
            AVG(pnl) as avg_pnl,
            SUM(pnl) as total_pnl,
            AVG(pnl_percentage) as avg_pnl_pct
        FROM trade_history
        GROUP BY symbol
        ORDER BY total_pnl DESC
    ''')
    
    symbol_stats = cursor.fetchall()
    print("Top 10 Symbols by Total PnL:")
    for i, (symbol, trades, wins, avg_pnl, total_pnl, avg_pnl_pct) in enumerate(symbol_stats[:10]):
        win_rate = (wins / trades) * 100 if trades > 0 else 0
        print(f"{i+1:2d}. {symbol:12s} | {trades:2d} trades | {win_rate:5.1f}% WR | ${total_pnl:6.2f} total | ${avg_pnl:5.2f} avg")
    
    print("\nWorst 5 Symbols by Total PnL:")
    for i, (symbol, trades, wins, avg_pnl, total_pnl, avg_pnl_pct) in enumerate(symbol_stats[-5:]):
        win_rate = (wins / trades) * 100 if trades > 0 else 0
        print(f"{i+1:2d}. {symbol:12s} | {trades:2d} trades | {win_rate:5.1f}% WR | ${total_pnl:6.2f} total | ${avg_pnl:5.2f} avg")
    
    # 3. ANALISIS INDIKATOR
    print("\n🎯 3. ANALISIS INDIKATOR TEKNIKAL")
    print("-" * 40)
    
    # Ambil semua trade dengan indikator
    cursor.execute('SELECT indicators, pnl, pnl_percentage, exit_reason FROM trade_history WHERE indicators IS NOT NULL')
    trades_data = cursor.fetchall()
    
    indicator_analysis = defaultdict(lambda: {'total': 0, 'wins': 0, 'losses': 0, 'total_pnl': 0})
    
    for indicators_json, pnl, pnl_pct, exit_reason in trades_data:
        try:
            indicators = json.loads(indicators_json)
            is_win = pnl > 0
            
            for indicator, value in indicators.items():
                if isinstance(value, bool):
                    # Analisis boolean indicators
                    key = f"{indicator}_{value}"
                    indicator_analysis[key]['total'] += 1
                    indicator_analysis[key]['total_pnl'] += pnl
                    if is_win:
                        indicator_analysis[key]['wins'] += 1
                    else:
                        indicator_analysis[key]['losses'] += 1
                        
        except (json.JSONDecodeError, TypeError):
            continue
    
    # Sort by win rate
    sorted_indicators = sorted(indicator_analysis.items(), 
                             key=lambda x: x[1]['wins'] / x[1]['total'] if x[1]['total'] > 0 else 0, 
                             reverse=True)
    
    print("Indikator dengan Win Rate Tertinggi (min 3 trades):")
    for indicator, stats in sorted_indicators[:15]:
        if stats['total'] >= 3:
            win_rate = (stats['wins'] / stats['total']) * 100
            avg_pnl = stats['total_pnl'] / stats['total']
            print(f"{indicator:25s} | {stats['total']:2d} trades | {win_rate:5.1f}% WR | ${avg_pnl:5.2f} avg")
    
    print("\nIndikator dengan Win Rate Terendah (min 3 trades):")
    for indicator, stats in sorted_indicators[-15:]:
        if stats['total'] >= 3:
            win_rate = (stats['wins'] / stats['total']) * 100
            avg_pnl = stats['total_pnl'] / stats['total']
            print(f"{indicator:25s} | {stats['total']:2d} trades | {win_rate:5.1f}% WR | ${avg_pnl:5.2f} avg")
    
    # 4. ANALISIS EXIT REASON
    print("\n🚪 4. ANALISIS EXIT REASON")
    print("-" * 40)
    
    cursor.execute('''
        SELECT 
            exit_reason,
            COUNT(*) as count,
            AVG(pnl) as avg_pnl,
            AVG(pnl_percentage) as avg_pnl_pct,
            AVG(duration_minutes) as avg_duration
        FROM trade_history
        GROUP BY exit_reason
        ORDER BY count DESC
    ''')
    
    exit_stats = cursor.fetchall()
    for exit_reason, count, avg_pnl, avg_pnl_pct, avg_duration in exit_stats:
        print(f"{exit_reason:10s} | {count:3d} trades | ${avg_pnl:6.2f} avg | {avg_pnl_pct:6.2f}% | {avg_duration:5.1f}min")
    
    # 5. ANALISIS DIRECTION
    print("\n📊 5. ANALISIS DIRECTION (LONG vs SHORT)")
    print("-" * 40)
    
    cursor.execute('''
        SELECT 
            direction,
            COUNT(*) as trades,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
            AVG(pnl) as avg_pnl,
            SUM(pnl) as total_pnl,
            AVG(pnl_percentage) as avg_pnl_pct
        FROM trade_history
        GROUP BY direction
    ''')
    
    direction_stats = cursor.fetchall()
    for direction, trades, wins, avg_pnl, total_pnl, avg_pnl_pct in direction_stats:
        win_rate = (wins / trades) * 100 if trades > 0 else 0
        print(f"{direction:5s} | {trades:3d} trades | {win_rate:5.1f}% WR | ${total_pnl:7.2f} total | ${avg_pnl:5.2f} avg")
    
    # 6. ANALISIS LEVERAGE
    print("\n⚡ 6. ANALISIS LEVERAGE")
    print("-" * 40)
    
    cursor.execute('''
        SELECT 
            leverage,
            COUNT(*) as trades,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
            AVG(pnl) as avg_pnl,
            SUM(pnl) as total_pnl
        FROM trade_history
        GROUP BY leverage
        ORDER BY leverage
    ''')
    
    leverage_stats = cursor.fetchall()
    for leverage, trades, wins, avg_pnl, total_pnl in leverage_stats:
        win_rate = (wins / trades) * 100 if trades > 0 else 0
        print(f"{leverage:2d}x | {trades:3d} trades | {win_rate:5.1f}% WR | ${total_pnl:7.2f} total | ${avg_pnl:5.2f} avg")
    
    # 7. ANALISIS TRADING SESSION
    print("\n🕐 7. ANALISIS TRADING SESSION")
    print("-" * 40)
    
    cursor.execute('''
        SELECT 
            trading_session,
            COUNT(*) as trades,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
            AVG(pnl) as avg_pnl,
            SUM(pnl) as total_pnl
        FROM trade_history
        WHERE trading_session IS NOT NULL AND trading_session != ''
        GROUP BY trading_session
        ORDER BY total_pnl DESC
    ''')
    
    session_stats = cursor.fetchall()
    if session_stats:
        for session, trades, wins, avg_pnl, total_pnl in session_stats:
            win_rate = (wins / trades) * 100 if trades > 0 else 0
            print(f"{session:12s} | {trades:3d} trades | {win_rate:5.1f}% WR | ${total_pnl:7.2f} total")
    else:
        print("❌ Tidak ada data trading session")
    
    conn.close()

def analyze_ai_reasoning():
    """Analisis AI reasoning untuk pattern dan insights"""
    
    print("\n🤖 ANALISIS AI REASONING")
    print("=" * 60)
    
    conn = sqlite3.connect('dry_run_trades.db')
    cursor = conn.cursor()
    
    # Ambil AI reasoning dari trades
    cursor.execute('''
        SELECT ai_entry_reasoning, ai_exit_reasoning, pnl, pnl_percentage, symbol, direction, exit_reason
        FROM trade_history 
        WHERE (ai_entry_reasoning IS NOT NULL AND ai_entry_reasoning != '') 
           OR (ai_exit_reasoning IS NOT NULL AND ai_exit_reasoning != '')
        ORDER BY pnl DESC
    ''')
    
    ai_data = cursor.fetchall()
    
    if not ai_data:
        print("❌ Tidak ada data AI reasoning")
        return
    
    print(f"📊 Total trades dengan AI reasoning: {len(ai_data)}")
    
    # 1. ANALISIS ENTRY REASONING
    print("\n🚀 1. ANALISIS ENTRY REASONING")
    print("-" * 40)
    
    entry_keywords = defaultdict(lambda: {'count': 0, 'wins': 0, 'total_pnl': 0})
    
    for entry_reason, exit_reason, pnl, pnl_pct, symbol, direction, exit_type in ai_data:
        if entry_reason:
            # Extract keywords dari entry reasoning
            words = re.findall(r'\b\w+\b', entry_reason.lower())
            important_words = [w for w in words if len(w) > 4 and w not in ['dengan', 'untuk', 'yang', 'akan', 'dapat', 'this', 'that', 'have', 'been', 'from']]
            
            is_win = pnl > 0
            
            for word in set(important_words):  # Use set to avoid counting same word multiple times
                entry_keywords[word]['count'] += 1
                entry_keywords[word]['total_pnl'] += pnl
                if is_win:
                    entry_keywords[word]['wins'] += 1
    
    # Sort by frequency
    sorted_entry_keywords = sorted(entry_keywords.items(), key=lambda x: x[1]['count'], reverse=True)
    
    print("Top Keywords dalam Entry Reasoning (min 3 occurrences):")
    for word, stats in sorted_entry_keywords[:20]:
        if stats['count'] >= 3:
            win_rate = (stats['wins'] / stats['count']) * 100
            avg_pnl = stats['total_pnl'] / stats['count']
            print(f"{word:15s} | {stats['count']:2d}x | {win_rate:5.1f}% WR | ${avg_pnl:5.2f} avg")
    
    # 2. ANALISIS EXIT REASONING
    print("\n🚪 2. ANALISIS EXIT REASONING")
    print("-" * 40)
    
    exit_keywords = defaultdict(lambda: {'count': 0, 'total_pnl': 0})
    
    for entry_reason, exit_reason, pnl, pnl_pct, symbol, direction, exit_type in ai_data:
        if exit_reason:
            words = re.findall(r'\b\w+\b', exit_reason.lower())
            important_words = [w for w in words if len(w) > 4 and w not in ['dengan', 'untuk', 'yang', 'akan', 'dapat', 'this', 'that', 'have', 'been', 'from']]
            
            for word in set(important_words):
                exit_keywords[word]['count'] += 1
                exit_keywords[word]['total_pnl'] += pnl
    
    sorted_exit_keywords = sorted(exit_keywords.items(), key=lambda x: x[1]['count'], reverse=True)
    
    print("Top Keywords dalam Exit Reasoning (min 3 occurrences):")
    for word, stats in sorted_exit_keywords[:20]:
        if stats['count'] >= 3:
            avg_pnl = stats['total_pnl'] / stats['count']
            print(f"{word:15s} | {stats['count']:2d}x | ${avg_pnl:5.2f} avg PnL")
    
    # 3. BEST vs WORST TRADES ANALYSIS
    print("\n🏆 3. BEST vs WORST TRADES")
    print("-" * 40)
    
    # Best trades
    best_trades = sorted(ai_data, key=lambda x: x[2], reverse=True)[:5]  # Sort by PnL
    print("Top 5 Best Trades:")
    for i, (entry, exit, pnl, pnl_pct, symbol, direction, exit_type) in enumerate(best_trades):
        print(f"{i+1}. {symbol} {direction} | ${pnl:.2f} ({pnl_pct:.1f}%) | {exit_type}")
        if entry:
            entry_short = entry[:100] + "..." if len(entry) > 100 else entry
            print(f"   Entry: {entry_short}")
        if exit:
            exit_short = exit[:100] + "..." if len(exit) > 100 else exit
            print(f"   Exit:  {exit_short}")
        print()
    
    # Worst trades
    worst_trades = sorted(ai_data, key=lambda x: x[2])[:5]  # Sort by PnL ascending
    print("Top 5 Worst Trades:")
    for i, (entry, exit, pnl, pnl_pct, symbol, direction, exit_type) in enumerate(worst_trades):
        print(f"{i+1}. {symbol} {direction} | ${pnl:.2f} ({pnl_pct:.1f}%) | {exit_type}")
        if entry:
            entry_short = entry[:100] + "..." if len(entry) > 100 else entry
            print(f"   Entry: {entry_short}")
        if exit:
            exit_short = exit[:100] + "..." if len(exit) > 100 else exit
            print(f"   Exit:  {exit_short}")
        print()
    
    conn.close()

def generate_recommendations():
    """Generate recommendations berdasarkan analisis"""
    
    print("\n💡 REKOMENDASI PERBAIKAN STRATEGY")
    print("=" * 60)
    
    conn = sqlite3.connect('dry_run_trades.db')
    cursor = conn.cursor()
    
    # 1. Cek win rate keseluruhan
    cursor.execute('SELECT AVG(CASE WHEN pnl > 0 THEN 1.0 ELSE 0.0 END) * 100 FROM trade_history')
    win_rate = cursor.fetchone()[0] or 0
    
    print(f"📊 Current Win Rate: {win_rate:.1f}%")
    
    if win_rate < 50:
        print("⚠️  CRITICAL: Win rate di bawah 50%!")
        print("   Rekomendasi:")
        print("   - Review dan ketatkan filter entry")
        print("   - Pertimbangkan mengurangi leverage")
        print("   - Analisis ulang indikator yang digunakan")
    elif win_rate < 60:
        print("⚠️  WARNING: Win rate masih bisa ditingkatkan")
        print("   Rekomendasi:")
        print("   - Fine-tune parameter indikator")
        print("   - Pertimbangkan filter tambahan")
    else:
        print("✅ Win rate sudah baik!")
    
    # 2. Analisis indikator bermasalah
    cursor.execute('SELECT indicators, pnl FROM trade_history WHERE indicators IS NOT NULL')
    trades_data = cursor.fetchall()
    
    problematic_indicators = []
    
    for indicators_json, pnl in trades_data:
        try:
            indicators = json.loads(indicators_json)
            if pnl < 0:  # Losing trade
                for indicator, value in indicators.items():
                    if isinstance(value, bool) and value:  # Indicator yang TRUE tapi trade loss
                        problematic_indicators.append(indicator)
        except:
            continue
    
    if problematic_indicators:
        problem_count = Counter(problematic_indicators)
        print(f"\n🚨 Indikator yang sering muncul di losing trades:")
        for indicator, count in problem_count.most_common(10):
            print(f"   - {indicator}: {count} kali di losing trades")
    
    # 3. Rekomendasi berdasarkan exit reason
    cursor.execute('''
        SELECT exit_reason, COUNT(*), AVG(pnl) 
        FROM trade_history 
        GROUP BY exit_reason
    ''')
    
    exit_analysis = cursor.fetchall()
    
    print(f"\n📈 Analisis Exit Strategy:")
    for exit_reason, count, avg_pnl in exit_analysis:
        if avg_pnl < 0:
            print(f"   ⚠️  {exit_reason}: {count} trades, avg ${avg_pnl:.2f}")
            if exit_reason == 'SL_HIT':
                print("      Rekomendasi: Pertimbangkan SL yang lebih longgar atau filter entry yang lebih ketat")
        else:
            print(f"   ✅ {exit_reason}: {count} trades, avg ${avg_pnl:.2f}")
    
    # 4. Rekomendasi leverage
    cursor.execute('''
        SELECT leverage, COUNT(*), AVG(pnl), AVG(CASE WHEN pnl > 0 THEN 1.0 ELSE 0.0 END) * 100 as wr
        FROM trade_history 
        GROUP BY leverage
        ORDER BY wr DESC
    ''')
    
    leverage_analysis = cursor.fetchall()
    
    print(f"\n⚡ Analisis Leverage:")
    best_leverage = None
    best_wr = 0
    
    for leverage, count, avg_pnl, wr in leverage_analysis:
        print(f"   {leverage}x: {count} trades, {wr:.1f}% WR, ${avg_pnl:.2f} avg")
        if wr > best_wr and count >= 5:  # Min 5 trades untuk valid
            best_wr = wr
            best_leverage = leverage
    
    if best_leverage:
        print(f"   💡 Rekomendasi: Fokus pada leverage {best_leverage}x (WR tertinggi: {best_wr:.1f}%)")
    
    conn.close()
    
    print(f"\n🎯 KESIMPULAN DAN ACTION ITEMS:")
    print("1. Monitor indikator dengan win rate rendah")
    print("2. Pertimbangkan filter tambahan untuk entry")
    print("3. Review AI reasoning pattern untuk insight")
    print("4. Optimasi parameter berdasarkan session trading")
    print("5. Test parameter baru di dry run sebelum live trading")

if __name__ == "__main__":
    try:
        analyze_database()
        analyze_ai_reasoning()
        generate_recommendations()
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()