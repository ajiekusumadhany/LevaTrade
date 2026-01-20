#!/usr/bin/env python3
"""
AI Analysis System - Simplified Version
Sistem analisis AI yang membedakan antara real-time dan historical analysis
"""
import sqlite3
import json
from typing import Dict, List
from datetime import datetime

def get_realtime_market_analysis(symbol: str) -> Dict:
    """
    Analisis real-time untuk symbol tertentu
    Mengambil data market langsung dari API
    """
    try:
        import asyncio
        from market_data_system import get_market_data_system
        from indicator_analysis_system import get_indicator_analyzer
        
        # Get real-time market data
        market_system = get_market_data_system()
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        market_data = loop.run_until_complete(market_system.get_market_data(symbol))
        loop.close()
        
        # Get historical performance
        analyzer = get_indicator_analyzer()
        dry_run_performance = analyzer.get_symbol_performance_analysis(symbol, "dry_run", 30)
        
        # Categorize market data
        market_cap_category = market_system.categorize_market_cap(market_data.get('market_cap', 0))
        volume_category = market_system.categorize_volume(market_data.get('total_volume_24h', 0))
        
        return {
            'symbol': symbol,
            'analysis_type': 'realtime',
            'timestamp': datetime.now().isoformat(),
            'market_cap': market_data.get('market_cap', 0),
            'market_cap_category': market_cap_category,
            'volume_24h': market_data.get('total_volume_24h', 0),
            'volume_category': volume_category,
            'liquidity_score': market_data.get('liquidity_score', 0),
            'volatility_score': market_data.get('volatility_score', 0),
            'market_dominance': market_data.get('market_dominance', 0),
            'historical_performance': dry_run_performance.get(symbol, {}),
            'success': True
        }
        
    except Exception as e:
        return {
            'symbol': symbol,
            'analysis_type': 'realtime',
            'error': str(e),
            'success': False
        }

def get_historical_trades_analysis(symbol: str = None, limit: int = 5, mode: str = "dry_run") -> List[Dict]:
    """
    Analisis historical trades dengan data yang tersimpan
    """
    try:
        from indicator_analysis_system import get_indicator_analyzer
        
        analyzer = get_indicator_analyzer()
        trades = analyzer.get_trade_history_analysis(mode, 30)
        
        print(f"   Debug: Found {len(trades)} total trades")
        
        if symbol:
            trades = [t for t in trades if t['symbol'] == symbol]
            print(f"   Debug: Filtered to {len(trades)} trades for {symbol}")
        
        # Limit results
        trades = trades[:limit]
        
        results = []
        for i, trade in enumerate(trades):
            try:
                print(f"   Debug: Processing trade {i+1}: {trade.get('symbol', 'Unknown')}")
                
                # Analyze indicators
                passed_indicators = trade.get('passed_indicators', [])
                failed_indicators = trade.get('failed_indicators', [])
                
                result = {
                    'symbol': trade.get('symbol', 'Unknown'),
                    'direction': trade.get('direction', 'Unknown'),
                    'pnl': trade.get('pnl', 0),
                    'pnl_percentage': trade.get('pnl_percentage', 0),
                    'exit_reason': trade.get('exit_reason', 'Unknown'),
                    'entry_time': trade.get('entry_time', ''),
                    'pass_rate': trade.get('pass_rate', 0),
                    'passed_indicators_count': len(passed_indicators),
                    'failed_indicators_count': len(failed_indicators),
                    'passed_indicators': [ind.get('name', 'Unknown') for ind in passed_indicators],
                    'failed_indicators': [ind.get('name', 'Unknown') for ind in failed_indicators],
                    'market_cap': trade.get('market_cap', 0),
                    'market_cap_category': trade.get('market_cap_category', ''),
                    'volume_category': trade.get('volume_category', ''),
                    'is_profitable': trade.get('pnl', 0) > 0
                }
                results.append(result)
                
            except Exception as e:
                print(f"   Debug: Error processing trade {i+1}: {e}")
                continue
        
        print(f"   Debug: Successfully processed {len(results)} trades")
        return results
        
    except Exception as e:
        print(f"   Debug: Main error in historical analysis: {e}")
        import traceback
        traceback.print_exc()
        return [{'error': str(e), 'success': False}]

def get_open_positions_analysis(symbol: str = None, mode: str = "dry_run") -> List[Dict]:
    """
    Analisis posisi yang masih terbuka
    """
    try:
        from indicator_analysis_system import get_indicator_analyzer
        
        analyzer = get_indicator_analyzer()
        positions = analyzer.get_open_positions_analysis(mode)
        
        if symbol:
            positions = [p for p in positions if p['symbol'] == symbol]
        
        results = []
        for position in positions:
            # Analyze indicators
            passed_indicators = position.get('passed_indicators', [])
            failed_indicators = position.get('failed_indicators', [])
            
            result = {
                'position_id': position['position_id'],
                'symbol': position['symbol'],
                'direction': position['direction'],
                'entry_price': position['entry_price'],
                'current_price': position['current_price'],
                'pnl_percentage': position['pnl_percentage'],
                'entry_time': position['entry_time'],
                'pass_rate': position['pass_rate'],
                'passed_indicators_count': len(passed_indicators),
                'failed_indicators_count': len(failed_indicators),
                'passed_indicators': [ind['name'] for ind in passed_indicators],
                'failed_indicators': [ind['name'] for ind in failed_indicators],
                'market_cap': position.get('market_cap', 0),
                'market_cap_category': position.get('market_cap_category', ''),
                'volume_category': position.get('volume_category', '')
            }
            results.append(result)
        
        return results
        
    except Exception as e:
        return [{'error': str(e), 'success': False}]

def analyze_indicator_performance(mode: str = "dry_run", days: int = 30) -> Dict:
    """
    Analisis performa indikator secara keseluruhan
    """
    try:
        from indicator_analysis_system import get_indicator_analyzer
        
        analyzer = get_indicator_analyzer()
        trades = analyzer.get_trade_history_analysis(mode, days)
        
        # Aggregate indicator performance
        indicator_stats = {}
        
        for trade in trades:
            passed_indicators = trade.get('passed_indicators', [])
            failed_indicators = trade.get('failed_indicators', [])
            is_profitable = trade['pnl'] > 0
            
            # Count passed indicators
            for indicator in passed_indicators:
                name = indicator['name']
                if name not in indicator_stats:
                    indicator_stats[name] = {
                        'total_passed': 0,
                        'total_failed': 0,
                        'wins_when_passed': 0,
                        'losses_when_passed': 0
                    }
                
                indicator_stats[name]['total_passed'] += 1
                if is_profitable:
                    indicator_stats[name]['wins_when_passed'] += 1
                else:
                    indicator_stats[name]['losses_when_passed'] += 1
            
            # Count failed indicators
            for indicator in failed_indicators:
                name = indicator['name']
                if name not in indicator_stats:
                    indicator_stats[name] = {
                        'total_passed': 0,
                        'total_failed': 0,
                        'wins_when_passed': 0,
                        'losses_when_passed': 0
                    }
                
                indicator_stats[name]['total_failed'] += 1
        
        # Calculate performance metrics
        performance_results = []
        for name, stats in indicator_stats.items():
            total_occurrences = stats['total_passed'] + stats['total_failed']
            pass_rate = (stats['total_passed'] / total_occurrences * 100) if total_occurrences > 0 else 0
            
            win_rate_when_passed = 0
            if stats['total_passed'] > 0:
                win_rate_when_passed = (stats['wins_when_passed'] / stats['total_passed'] * 100)
            
            performance_results.append({
                'indicator_name': name,
                'total_occurrences': total_occurrences,
                'pass_rate': pass_rate,
                'win_rate_when_passed': win_rate_when_passed,
                'total_passed': stats['total_passed'],
                'total_failed': stats['total_failed'],
                'wins_when_passed': stats['wins_when_passed'],
                'effectiveness_score': (pass_rate * 0.3) + (win_rate_when_passed * 0.7)  # Weighted score
            })
        
        # Sort by effectiveness score
        performance_results.sort(key=lambda x: x['effectiveness_score'], reverse=True)
        
        return {
            'mode': mode,
            'days_analyzed': days,
            'total_trades': len(trades),
            'indicator_performance': performance_results,
            'success': True
        }
        
    except Exception as e:
        return {'error': str(e), 'success': False}

if __name__ == "__main__":
    print("🧪 Testing Simple AI Analysis System...")
    
    # Test real-time analysis
    print("\n1. Testing real-time analysis:")
    realtime = get_realtime_market_analysis('BTCUSDT')
    if realtime.get('success'):
        print(f"   ✅ Success: {realtime['market_cap_category']} with ${realtime['market_cap']:,.0f}")
    else:
        print(f"   ❌ Error: {realtime.get('error')}")
    
    # Test historical analysis
    print("\n2. Testing historical analysis:")
    
    # First, let's see what symbols are available
    try:
        from indicator_analysis_system import get_indicator_analyzer
        analyzer = get_indicator_analyzer()
        all_trades = analyzer.get_trade_history_analysis("dry_run", 30)
        
        if all_trades:
            available_symbols = list(set([t['symbol'] for t in all_trades]))
            print(f"   Available symbols: {available_symbols}")
            
            # Test with first available symbol
            test_symbol = available_symbols[0] if available_symbols else None
            if test_symbol:
                historical = get_historical_trades_analysis(test_symbol, 3)
                if historical and 'error' not in historical[0]:
                    print(f"   ✅ Found {len(historical)} trades for {test_symbol}")
                    for trade in historical[:2]:
                        print(f"      - {trade['symbol']} {trade['direction']}: {trade['pnl_percentage']:.2f}% ({trade['exit_reason']})")
                else:
                    print(f"   ❌ Error processing trades for {test_symbol}")
            else:
                print(f"   ⚠️  No symbols available")
        else:
            print(f"   ⚠️  No trades found in database")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test indicator performance
    print("\n3. Testing indicator performance:")
    performance = analyze_indicator_performance()
    if performance.get('success'):
        print(f"   ✅ Analyzed {performance['total_trades']} trades")
        if performance['indicator_performance']:
            best_indicator = performance['indicator_performance'][0]
            print(f"   🏆 Best indicator: {best_indicator['indicator_name']} (score: {best_indicator['effectiveness_score']:.1f})")
    else:
        print(f"   ❌ Error: {performance.get('error')}")
    
    print("\n✅ Simple AI Analysis System test completed!")