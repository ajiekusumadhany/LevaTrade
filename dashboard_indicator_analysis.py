#!/usr/bin/env python3
"""
Dashboard Indicator Analysis Integration
Menambahkan endpoint untuk analisis indikator ke dashboard
"""
from flask import jsonify
from indicator_analysis_system import get_indicator_analyzer
from datetime import datetime, timedelta

def add_indicator_analysis_routes(app):
    """Add indicator analysis routes to Flask app"""
    
    @app.route('/api/indicator-analysis/<mode>')
    def get_indicator_analysis_overview(mode):
        """Get overview of indicator analysis"""
        try:
            analyzer = get_indicator_analyzer()
            
            # Get data for last 7 days
            open_positions = analyzer.get_open_positions_analysis(mode)
            trade_history = analyzer.get_trade_history_analysis(mode, 7)
            symbol_performance = analyzer.get_symbol_performance_analysis(None, mode, 7)
            
            # Calculate overall stats
            total_trades = len(trade_history)
            winning_trades = len([t for t in trade_history if t['pnl'] > 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            avg_pass_rate = sum(t['pass_rate'] for t in trade_history) / total_trades if total_trades > 0 else 0
            total_pnl = sum(t['pnl'] for t in trade_history)
            
            # Top performing symbols
            top_symbols = sorted(symbol_performance.items(), 
                               key=lambda x: x[1]['win_rate'], reverse=True)[:5]
            
            # Recent performance trend
            recent_trades = sorted(trade_history, key=lambda x: x['entry_time'])[-10:]
            
            return jsonify({
                'success': True,
                'data': {
                    'overview': {
                        'total_trades': total_trades,
                        'win_rate': win_rate,
                        'avg_pass_rate': avg_pass_rate,
                        'total_pnl': total_pnl,
                        'open_positions': len(open_positions)
                    },
                    'top_symbols': [
                        {
                            'symbol': symbol,
                            'win_rate': stats['win_rate'],
                            'total_trades': stats['total_trades'],
                            'avg_pnl': stats['avg_pnl']
                        }
                        for symbol, stats in top_symbols
                    ],
                    'recent_performance': [
                        {
                            'symbol': t['symbol'],
                            'direction': t['direction'],
                            'pnl_percentage': t['pnl_percentage'],
                            'pass_rate': t['pass_rate'],
                            'entry_time': t['entry_time']
                        }
                        for t in recent_trades
                    ]
                }
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/symbol-analysis/<mode>/<symbol>')
    def get_symbol_detailed_analysis(mode, symbol):
        """Get detailed analysis for specific symbol"""
        try:
            analyzer = get_indicator_analyzer()
            
            # Get symbol performance
            symbol_performance = analyzer.get_symbol_performance_analysis(symbol, mode, 30)
            
            # Get recent trades for this symbol
            all_trades = analyzer.get_trade_history_analysis(mode, 30)
            symbol_trades = [t for t in all_trades if t['symbol'] == symbol]
            
            # Get open positions for this symbol
            all_positions = analyzer.get_open_positions_analysis(mode)
            symbol_positions = [p for p in all_positions if p['symbol'] == symbol]
            
            if symbol not in symbol_performance:
                return jsonify({
                    'success': False, 
                    'error': f'No data found for {symbol} in {mode} mode'
                })
            
            stats = symbol_performance[symbol]
            
            # Analyze indicator performance
            indicator_stats = []
            for ind_name, ind_data in stats['indicator_performance'].items():
                indicator_stats.append({
                    'name': ind_name,
                    'pass_rate': ind_data.get('pass_rate', 0),
                    'win_rate_when_passed': ind_data.get('win_rate_when_passed', 0),
                    'total_occurrences': ind_data.get('total', 0),
                    'passed_count': ind_data.get('passed', 0)
                })
            
            # Sort by win rate when passed
            indicator_stats.sort(key=lambda x: x['win_rate_when_passed'], reverse=True)
            
            # Direction analysis
            long_trades = [t for t in symbol_trades if t['direction'] == 'LONG']
            short_trades = [t for t in symbol_trades if t['direction'] == 'SHORT']
            
            long_stats = {
                'total': len(long_trades),
                'wins': len([t for t in long_trades if t['pnl'] > 0]),
                'win_rate': (len([t for t in long_trades if t['pnl'] > 0]) / len(long_trades) * 100) if long_trades else 0,
                'avg_pnl': sum(t['pnl'] for t in long_trades) / len(long_trades) if long_trades else 0
            }
            
            short_stats = {
                'total': len(short_trades),
                'wins': len([t for t in short_trades if t['pnl'] > 0]),
                'win_rate': (len([t for t in short_trades if t['pnl'] > 0]) / len(short_trades) * 100) if short_trades else 0,
                'avg_pnl': sum(t['pnl'] for t in short_trades) / len(short_trades) if short_trades else 0
            }
            
            return jsonify({
                'success': True,
                'data': {
                    'symbol': symbol,
                    'overall_stats': {
                        'total_trades': stats['total_trades'],
                        'win_rate': stats['win_rate'],
                        'avg_pass_rate': stats['avg_pass_rate'],
                        'total_pnl': stats['total_pnl'],
                        'avg_pnl': stats['avg_pnl']
                    },
                    'direction_analysis': {
                        'LONG': long_stats,
                        'SHORT': short_stats
                    },
                    'indicator_performance': indicator_stats,
                    'recent_trades': [
                        {
                            'direction': t['direction'],
                            'entry_price': t['entry_price'],
                            'exit_price': t['exit_price'],
                            'pnl_percentage': t['pnl_percentage'],
                            'pass_rate': t['pass_rate'],
                            'exit_reason': t['exit_reason'],
                            'entry_time': t['entry_time']
                        }
                        for t in symbol_trades[-10:]  # Last 10 trades
                    ],
                    'open_positions': [
                        {
                            'direction': p['direction'],
                            'entry_price': p['entry_price'],
                            'current_price': p['current_price'],
                            'pnl_percentage': p['pnl_percentage'],
                            'pass_rate': p['pass_rate'],
                            'entry_time': p['entry_time']
                        }
                        for p in symbol_positions
                    ]
                }
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/strategy-report/<mode>')
    def get_strategy_report(mode):
        """Get comprehensive strategy report"""
        try:
            analyzer = get_indicator_analyzer()
            report = analyzer.generate_strategy_report(mode, 7)
            
            return jsonify({
                'success': True,
                'data': {
                    'report': report,
                    'generated_at': datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/indicator-comparison/<mode>')
    def get_indicator_comparison(mode):
        """Compare indicator performance across all symbols"""
        try:
            analyzer = get_indicator_analyzer()
            
            # Get all trades
            all_trades = analyzer.get_trade_history_analysis(mode, 30)
            
            # Aggregate indicator performance across all symbols
            indicator_aggregates = {}
            
            for trade in all_trades:
                for indicator in trade['passed_indicators']:
                    ind_name = indicator['name']
                    if ind_name not in indicator_aggregates:
                        indicator_aggregates[ind_name] = {
                            'total_passed': 0,
                            'wins_when_passed': 0,
                            'total_pnl_when_passed': 0
                        }
                    
                    indicator_aggregates[ind_name]['total_passed'] += 1
                    if trade['pnl'] > 0:
                        indicator_aggregates[ind_name]['wins_when_passed'] += 1
                    indicator_aggregates[ind_name]['total_pnl_when_passed'] += trade['pnl']
            
            # Calculate performance metrics
            indicator_performance = []
            for ind_name, data in indicator_aggregates.items():
                if data['total_passed'] > 0:
                    win_rate = (data['wins_when_passed'] / data['total_passed']) * 100
                    avg_pnl = data['total_pnl_when_passed'] / data['total_passed']
                    
                    indicator_performance.append({
                        'name': ind_name,
                        'win_rate_when_passed': win_rate,
                        'avg_pnl_when_passed': avg_pnl,
                        'total_occurrences': data['total_passed'],
                        'total_wins': data['wins_when_passed']
                    })
            
            # Sort by win rate
            indicator_performance.sort(key=lambda x: x['win_rate_when_passed'], reverse=True)
            
            return jsonify({
                'success': True,
                'data': {
                    'indicator_performance': indicator_performance,
                    'total_trades_analyzed': len(all_trades)
                }
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

if __name__ == "__main__":
    # Test the functions
    from indicator_analysis_system import IndicatorAnalysisSystem
    
    analyzer = IndicatorAnalysisSystem()
    
    print("🧪 Testing Dashboard Indicator Analysis...")
    
    # Test overview
    open_positions = analyzer.get_open_positions_analysis("dry_run")
    print(f"📊 Open positions: {len(open_positions)}")
    
    # Test trade history
    trades = analyzer.get_trade_history_analysis("dry_run", 7)
    print(f"📈 Recent trades: {len(trades)}")
    
    # Test symbol performance
    performance = analyzer.get_symbol_performance_analysis(None, "dry_run", 7)
    print(f"🎯 Symbols analyzed: {len(performance)}")
    
    print("✅ Dashboard integration ready!")