#!/usr/bin/env python3
"""
Overall Indicator Performance Analysis System
Menganalisis performa keseluruhan setiap indikator teknikal
"""
import sqlite3
import json
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from indicator_analysis_system import get_indicator_analyzer

class OverallIndicatorAnalyzer:
    def __init__(self):
        self.dry_run_db = "dry_run_trades.db"
        self.real_db = "real_trades.db"
        self.indicator_analyzer = get_indicator_analyzer()
        
        # Indicator descriptions
        self.indicator_descriptions = {
            'ema_fast_above_slow': 'EMA Fast Above Slow',
            'macd_bullish': 'MACD Bullish Signal',
            'rsi_oversold': 'RSI Oversold (<30)',
            'rsi_overbought': 'RSI Overbought (>70)',
            'rsi_neutral': 'RSI Neutral Zone (30-70)',
            'volume_confirmation': 'Volume Above Average',
            'volatility_confirmation': 'Sufficient Volatility',
            'price_near_support': 'Price Near Support',
            'price_near_resistance': 'Price Near Resistance',
            'trend_alignment': 'Trend Alignment',
            'momentum_confirmation': 'Momentum Confirmation'
        }
        
        # Indicator categories
        self.indicator_categories = {
            'TREND': ['ema_fast_above_slow', 'trend_alignment'],
            'MOMENTUM': ['macd_bullish', 'momentum_confirmation'],
            'OSCILLATOR': ['rsi_oversold', 'rsi_overbought', 'rsi_neutral'],
            'VOLUME': ['volume_confirmation'],
            'VOLATILITY': ['volatility_confirmation'],
            'SUPPORT_RESISTANCE': ['price_near_support', 'price_near_resistance']
        }
    
    def get_overall_indicator_performance(self, mode: str = "dry_run", days: int = 30) -> Dict:
        """Get comprehensive indicator performance analysis"""
        db_path = self.dry_run_db if mode == "dry_run" else self.real_db
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get cutoff date
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Get all trades with indicators
            cursor.execute('''
                SELECT symbol, direction, pnl, pnl_percentage, indicators, exit_reason, entry_time
                FROM trade_history 
                WHERE entry_time >= ? AND indicators IS NOT NULL AND indicators != ""
                ORDER BY entry_time DESC
            ''', (cutoff_date,))
            
            trades = cursor.fetchall()
            conn.close()
            
            # Initialize indicator stats
            indicator_stats = {}
            
            for trade in trades:
                symbol, direction, pnl, pnl_percentage, indicators_json, exit_reason, entry_time = trade
                
                # Parse indicators
                try:
                    if isinstance(indicators_json, str):
                        indicators = json.loads(indicators_json)
                    else:
                        indicators = indicators_json
                except:
                    continue
                
                # Analyze indicators for this trade
                passed_indicators, failed_indicators = self.indicator_analyzer.analyze_indicators(indicators, direction)
                
                is_winning_trade = pnl > 0
                
                # Process passed indicators
                for indicator in passed_indicators:
                    ind_name = indicator['name']
                    
                    if ind_name not in indicator_stats:
                        indicator_stats[ind_name] = {
                            'name': ind_name,
                            'description': self.indicator_descriptions.get(ind_name, ind_name.replace('_', ' ').title()),
                            'total_passed': 0,
                            'total_failed': 0,
                            'wins_when_passed': 0,
                            'losses_when_passed': 0,
                            'wins_when_failed': 0,
                            'losses_when_failed': 0,
                            'total_trades': 0,
                            'pass_rate': 0,
                            'win_rate_when_passed': 0,
                            'win_rate_when_failed': 0,
                            'overall_accuracy': 0,
                            'pnl_when_passed': 0,
                            'pnl_when_failed': 0,
                            'avg_pnl_when_passed': 0,
                            'avg_pnl_when_failed': 0,
                            'symbols_traded': set(),
                            'directions_traded': {'LONG': 0, 'SHORT': 0},
                            'exit_reasons_when_passed': {},
                            'exit_reasons_when_failed': {},
                            'category': self._get_indicator_category(ind_name)
                        }
                    
                    stats = indicator_stats[ind_name]
                    stats['total_passed'] += 1
                    stats['total_trades'] += 1
                    stats['pnl_when_passed'] += pnl
                    stats['symbols_traded'].add(symbol)
                    stats['directions_traded'][direction] += 1
                    
                    # Track exit reasons when passed
                    if exit_reason not in stats['exit_reasons_when_passed']:
                        stats['exit_reasons_when_passed'][exit_reason] = 0
                    stats['exit_reasons_when_passed'][exit_reason] += 1
                    
                    if is_winning_trade:
                        stats['wins_when_passed'] += 1
                    else:
                        stats['losses_when_passed'] += 1
                
                # Process failed indicators
                for indicator in failed_indicators:
                    ind_name = indicator['name']
                    
                    if ind_name not in indicator_stats:
                        indicator_stats[ind_name] = {
                            'name': ind_name,
                            'description': self.indicator_descriptions.get(ind_name, ind_name.replace('_', ' ').title()),
                            'total_passed': 0,
                            'total_failed': 0,
                            'wins_when_passed': 0,
                            'losses_when_passed': 0,
                            'wins_when_failed': 0,
                            'losses_when_failed': 0,
                            'total_trades': 0,
                            'pass_rate': 0,
                            'win_rate_when_passed': 0,
                            'win_rate_when_failed': 0,
                            'overall_accuracy': 0,
                            'pnl_when_passed': 0,
                            'pnl_when_failed': 0,
                            'avg_pnl_when_passed': 0,
                            'avg_pnl_when_failed': 0,
                            'symbols_traded': set(),
                            'directions_traded': {'LONG': 0, 'SHORT': 0},
                            'exit_reasons_when_passed': {},
                            'exit_reasons_when_failed': {},
                            'category': self._get_indicator_category(ind_name)
                        }
                    
                    stats = indicator_stats[ind_name]
                    stats['total_failed'] += 1
                    stats['total_trades'] += 1
                    stats['pnl_when_failed'] += pnl
                    stats['symbols_traded'].add(symbol)
                    stats['directions_traded'][direction] += 1
                    
                    # Track exit reasons when failed
                    if exit_reason not in stats['exit_reasons_when_failed']:
                        stats['exit_reasons_when_failed'][exit_reason] = 0
                    stats['exit_reasons_when_failed'][exit_reason] += 1
                    
                    if is_winning_trade:
                        stats['wins_when_failed'] += 1
                    else:
                        stats['losses_when_failed'] += 1
            
            # Calculate final metrics
            for ind_name, stats in indicator_stats.items():
                if stats['total_trades'] > 0:
                    stats['pass_rate'] = (stats['total_passed'] / stats['total_trades']) * 100
                    
                    if stats['total_passed'] > 0:
                        stats['win_rate_when_passed'] = (stats['wins_when_passed'] / stats['total_passed']) * 100
                        stats['avg_pnl_when_passed'] = stats['pnl_when_passed'] / stats['total_passed']
                    
                    if stats['total_failed'] > 0:
                        stats['win_rate_when_failed'] = (stats['wins_when_failed'] / stats['total_failed']) * 100
                        stats['avg_pnl_when_failed'] = stats['pnl_when_failed'] / stats['total_failed']
                    
                    # Overall accuracy: how often the indicator correctly predicts trade outcome
                    correct_predictions = stats['wins_when_passed'] + stats['losses_when_failed']
                    stats['overall_accuracy'] = (correct_predictions / stats['total_trades']) * 100
                    
                    # Convert set to list for JSON serialization
                    stats['symbols_traded'] = list(stats['symbols_traded'])
            
            # Sort by overall accuracy
            sorted_indicators = sorted(indicator_stats.items(), key=lambda x: x[1]['overall_accuracy'], reverse=True)
            
            return {
                'mode': mode,
                'days_analyzed': days,
                'total_trades_analyzed': len(trades),
                'total_indicators': len(indicator_stats),
                'indicators': dict(sorted_indicators),
                'success': True
            }
            
        except Exception as e:
            print(f"❌ Error analyzing indicator performance: {e}")
            return {'error': str(e), 'success': False}
    
    def _get_indicator_category(self, indicator_name: str) -> str:
        """Get category for an indicator"""
        for category, indicators in self.indicator_categories.items():
            if indicator_name in indicators:
                return category
        return 'OTHER'
    
    def get_indicator_categories_summary(self, indicator_data: Dict) -> Dict:
        """Get summary by indicator categories"""
        if not indicator_data.get('success'):
            return {'error': 'No indicator data available'}
        
        category_summary = {}
        
        for ind_name, stats in indicator_data['indicators'].items():
            category = stats['category']
            
            if category not in category_summary:
                category_summary[category] = {
                    'category': category,
                    'indicators': [],
                    'avg_accuracy': 0,
                    'avg_pass_rate': 0,
                    'total_trades': 0
                }
            
            category_summary[category]['indicators'].append(stats)
            category_summary[category]['total_trades'] += stats['total_trades']
        
        # Calculate category averages
        for category, summary in category_summary.items():
            if summary['indicators']:
                summary['avg_accuracy'] = sum(ind['overall_accuracy'] for ind in summary['indicators']) / len(summary['indicators'])
                summary['avg_pass_rate'] = sum(ind['pass_rate'] for ind in summary['indicators']) / len(summary['indicators'])
                
                # Sort indicators by accuracy within category
                summary['indicators'].sort(key=lambda x: x['overall_accuracy'], reverse=True)
        
        return category_summary
    
    def get_indicator_recommendations(self, indicator_data: Dict) -> List[str]:
        """Generate recommendations based on indicator performance"""
        if not indicator_data.get('success'):
            return ["No data available for recommendations"]
        
        recommendations = []
        indicators = indicator_data['indicators']
        
        if not indicators:
            return ["No indicators found in the specified period"]
        
        # Best performing indicators
        best_indicators = list(indicators.items())[:3]
        worst_indicators = list(indicators.items())[-3:]
        
        # High accuracy indicators (>70%)
        high_accuracy = [(name, stats) for name, stats in indicators.items() 
                        if stats['overall_accuracy'] > 70 and stats['total_trades'] >= 5]
        
        # Reliable indicators (high pass rate + good win rate when passed)
        reliable = [(name, stats) for name, stats in indicators.items() 
                   if stats['pass_rate'] > 60 and stats['win_rate_when_passed'] > 60 and stats['total_trades'] >= 5]
        
        recommendations.append(f"🏆 Most Accurate Indicators: {', '.join([ind[1]['description'] for ind in best_indicators])}")
        
        if high_accuracy:
            recommendations.append(f"🎯 High Accuracy (>70%): {', '.join([ind[1]['description'] for ind in high_accuracy[:3]])}")
        
        if reliable:
            recommendations.append(f"✅ Most Reliable: {', '.join([ind[1]['description'] for ind in reliable[:3]])}")
        
        recommendations.append(f"⚠️ Needs Improvement: {', '.join([ind[1]['description'] for ind in worst_indicators])}")
        
        return recommendations

# Global instance
overall_indicator_analyzer = OverallIndicatorAnalyzer()

def get_overall_indicator_analyzer():
    """Get global overall indicator analyzer instance"""
    return overall_indicator_analyzer

if __name__ == "__main__":
    print("🧪 Testing Overall Indicator Performance Analysis System...")
    
    analyzer = OverallIndicatorAnalyzer()
    
    # Test indicator performance analysis
    print("\n📊 Testing Indicator Performance Analysis...")
    performance = analyzer.get_overall_indicator_performance("dry_run", 30)
    
    if performance.get('success'):
        print(f"✅ Analyzed {performance['total_indicators']} indicators from {performance['total_trades_analyzed']} trades")
        
        for ind_name, stats in list(performance['indicators'].items())[:5]:
            print(f"\n🎯 {stats['description']}:")
            print(f"   Overall Accuracy: {stats['overall_accuracy']:.1f}%")
            print(f"   Pass Rate: {stats['pass_rate']:.1f}% ({stats['total_passed']}/{stats['total_trades']})")
            print(f"   Win Rate When Passed: {stats['win_rate_when_passed']:.1f}%")
            print(f"   Win Rate When Failed: {stats['win_rate_when_failed']:.1f}%")
            print(f"   Category: {stats['category']}")
            print(f"   Symbols: {len(stats['symbols_traded'])} pairs")
    else:
        print(f"❌ Error: {performance.get('error')}")
    
    print("\n✅ Overall Indicator Performance Analysis System ready!")