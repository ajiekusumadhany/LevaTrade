#!/usr/bin/env python3
"""
Indicator Analysis System
Menganalisis indikator yang passed dan failed untuk setiap pair dan trade
"""
import sqlite3
import json
from typing import Dict, List, Tuple, Any
from datetime import datetime, timedelta
import pandas as pd

class IndicatorAnalysisSystem:
    def __init__(self, dry_run_db_path: str = "dry_run_trades.db", real_db_path: str = "real_trades.db"):
        self.dry_run_db_path = dry_run_db_path
        self.real_db_path = real_db_path
        
        # Definisi indikator dan kondisi yang diharapkan untuk setiap arah
        self.indicator_expectations = {
            'LONG': {
                # Boolean indicators - kondisi yang diharapkan untuk LONG
                'ema_fast_above_slow': True,
                'macd_bullish': True,
                'rsi_oversold': True,  # RSI oversold bagus untuk entry LONG
                'rsi_overbought': False,  # RSI overbought buruk untuk LONG
                'rsi_neutral': True,  # RSI neutral oke untuk LONG
                'volume_confirmation': True,
                'volatility_confirmation': True,
                'price_near_support': True,  # Dekat support bagus untuk LONG
                'price_near_resistance': False,  # Dekat resistance buruk untuk LONG
                'trend_alignment': True,
                'momentum_confirmation': True
            },
            'SHORT': {
                # Boolean indicators - kondisi yang diharapkan untuk SHORT
                'ema_fast_above_slow': False,  # EMA fast di bawah slow bagus untuk SHORT
                'macd_bullish': False,  # MACD bearish bagus untuk SHORT
                'rsi_oversold': False,  # RSI oversold buruk untuk SHORT
                'rsi_overbought': True,  # RSI overbought bagus untuk entry SHORT
                'rsi_neutral': True,  # RSI neutral oke untuk SHORT
                'volume_confirmation': True,
                'volatility_confirmation': True,
                'price_near_support': False,  # Dekat support buruk untuk SHORT
                'price_near_resistance': True,  # Dekat resistance bagus untuk SHORT
                'trend_alignment': True,
                'momentum_confirmation': True
            }
        }
        
        # Deskripsi indikator untuk laporan
        self.indicator_descriptions = {
            'ema_fast_above_slow': 'EMA Fast Above Slow',
            'macd_bullish': 'MACD Bullish Signal',
            'rsi_oversold': 'RSI Oversold Condition',
            'rsi_overbought': 'RSI Overbought Condition',
            'rsi_neutral': 'RSI Neutral Zone',
            'volume_confirmation': 'Volume Confirmation',
            'volatility_confirmation': 'Volatility Confirmation',
            'price_near_support': 'Price Near Support Level',
            'price_near_resistance': 'Price Near Resistance Level',
            'trend_alignment': 'Trend Alignment',
            'momentum_confirmation': 'Momentum Confirmation',
            'rsi_level': 'RSI Level',
            'atr_value': 'ATR Value',
            'ema_fast_value': 'EMA Fast Value',
            'ema_slow_value': 'EMA Slow Value',
            'macd_line_value': 'MACD Line Value',
            'signal_line_value': 'Signal Line Value',
            'support_resistance': 'Support/Resistance Level',
            'price_distance_from_level': 'Distance from S/R Level'
        }
    
    def analyze_indicators(self, indicators: Dict, direction: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Menganalisis indikator mana yang passed dan failed untuk arah trading tertentu
        
        Returns:
            Tuple[passed_indicators, failed_indicators]
        """
        passed = []
        failed = []
        
        expected = self.indicator_expectations.get(direction, {})
        
        for indicator_name, actual_value in indicators.items():
            # Skip numerical indicators untuk analisis passed/failed
            if indicator_name in ['rsi_level', 'atr_value', 'ema_fast_value', 'ema_slow_value', 
                                'macd_line_value', 'signal_line_value', 'support_resistance', 
                                'price_distance_from_level']:
                continue
            
            expected_value = expected.get(indicator_name)
            if expected_value is None:
                continue
            
            indicator_info = {
                'name': indicator_name,
                'description': self.indicator_descriptions.get(indicator_name, indicator_name),
                'actual': actual_value,
                'expected': expected_value,
                'match': actual_value == expected_value
            }
            
            if actual_value == expected_value:
                passed.append(indicator_info)
            else:
                failed.append(indicator_info)
        
        return passed, failed
    
    def get_open_positions_analysis(self, mode: str = "dry_run") -> List[Dict]:
        """
        Menganalisis indikator untuk semua posisi yang masih open
        """
        db_path = self.dry_run_db_path if mode == "dry_run" else self.real_db_path
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, symbol, direction, entry_price, current_price, 
                       indicators, entry_time, ai_entry_reasoning
                FROM open_positions
                ORDER BY entry_time DESC
            ''')
            
            positions = cursor.fetchall()
            conn.close()
            
            analysis_results = []
            
            for pos in positions:
                if len(pos) >= 8:
                    pos_id, symbol, direction, entry_price, current_price, indicators_json, entry_time, ai_entry_reasoning = pos
                else:
                    pos_id, symbol, direction, entry_price, current_price, indicators_json, entry_time = pos
                    ai_entry_reasoning = ""
                
                # Parse indicators
                if isinstance(indicators_json, str):
                    indicators = json.loads(indicators_json)
                else:
                    indicators = indicators_json
                
                # Analyze indicators
                passed, failed = self.analyze_indicators(indicators, direction)
                
                # Calculate performance metrics
                total_indicators = len(passed) + len(failed)
                pass_rate = (len(passed) / total_indicators * 100) if total_indicators > 0 else 0
                
                # Calculate current PnL
                pnl_percentage = 0
                if entry_price and current_price:
                    if direction == "LONG":
                        pnl_percentage = ((current_price - entry_price) / entry_price) * 100
                    else:  # SHORT
                        pnl_percentage = ((entry_price - current_price) / entry_price) * 100
                
                analysis_results.append({
                    'position_id': pos_id,
                    'symbol': symbol,
                    'direction': direction,
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'entry_time': entry_time,
                    'pnl_percentage': pnl_percentage,
                    'indicators': indicators,
                    'passed_indicators': passed,
                    'failed_indicators': failed,
                    'pass_rate': pass_rate,
                    'total_indicators': total_indicators,
                    'ai_entry_reasoning': ai_entry_reasoning,
                    'mode': mode
                })
            
            return analysis_results
            
        except Exception as e:
            print(f"❌ Error analyzing open positions: {e}")
            return []
    
    def get_trade_history_analysis(self, mode: str = "dry_run", days: int = 7) -> List[Dict]:
        """
        Menganalisis indikator untuk history trades dalam periode tertentu
        """
        db_path = self.dry_run_db_path if mode == "dry_run" else self.real_db_path
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get trades from last N days
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                SELECT id, symbol, direction, entry_price, exit_price, pnl, pnl_percentage,
                       exit_reason, indicators, entry_time, exit_time, ai_entry_reasoning, ai_exit_reasoning,
                       market_cap, market_cap_rank, total_volume_24h, liquidity_score, volatility_score,
                       market_dominance, market_cap_category, volume_category
                FROM trade_history
                WHERE entry_time >= ?
                ORDER BY entry_time DESC
            ''', (cutoff_date,))
            
            trades = cursor.fetchall()
            conn.close()
            
            analysis_results = []
            
            for trade in trades:
                # Handle different schema lengths
                if len(trade) >= 20:  # New schema with market data
                    (trade_id, symbol, direction, entry_price, exit_price, pnl, pnl_percentage,
                     exit_reason, indicators_json, entry_time, exit_time, ai_entry_reasoning, ai_exit_reasoning,
                     market_cap, market_cap_rank, total_volume_24h, liquidity_score, volatility_score,
                     market_dominance, market_cap_category, volume_category) = trade
                elif len(trade) >= 13:  # Old schema with AI reasoning
                    (trade_id, symbol, direction, entry_price, exit_price, pnl, pnl_percentage,
                     exit_reason, indicators_json, entry_time, exit_time, ai_entry_reasoning, ai_exit_reasoning) = trade
                    # Set default market data
                    market_cap = market_cap_rank = total_volume_24h = liquidity_score = volatility_score = market_dominance = 0
                    market_cap_category = volume_category = ""
                else:  # Very old schema
                    (trade_id, symbol, direction, entry_price, exit_price, pnl, pnl_percentage,
                     exit_reason, indicators_json, entry_time, exit_time) = trade[:11]
                    ai_entry_reasoning = ai_exit_reasoning = ""
                    market_cap = market_cap_rank = total_volume_24h = liquidity_score = volatility_score = market_dominance = 0
                    market_cap_category = volume_category = ""
                
                # Parse indicators
                if isinstance(indicators_json, str):
                    indicators = json.loads(indicators_json)
                else:
                    indicators = indicators_json
                
                # Analyze indicators
                passed, failed = self.analyze_indicators(indicators, direction)
                
                # Calculate performance metrics
                total_indicators = len(passed) + len(failed)
                pass_rate = (len(passed) / total_indicators * 100) if total_indicators > 0 else 0
                
                analysis_results.append({
                    'trade_id': trade_id,
                    'symbol': symbol,
                    'direction': direction,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'pnl_percentage': pnl_percentage,
                    'exit_reason': exit_reason,
                    'entry_time': entry_time,
                    'exit_time': exit_time,
                    'indicators': indicators,
                    'passed_indicators': passed,
                    'failed_indicators': failed,
                    'pass_rate': pass_rate,
                    'total_indicators': total_indicators,
                    'ai_entry_reasoning': ai_entry_reasoning,
                    'ai_exit_reasoning': ai_exit_reasoning,
                    'mode': mode,
                    # Market data
                    'market_cap': market_cap,
                    'market_cap_rank': market_cap_rank,
                    'total_volume_24h': total_volume_24h,
                    'liquidity_score': liquidity_score,
                    'volatility_score': volatility_score,
                    'market_dominance': market_dominance,
                    'market_cap_category': market_cap_category,
                    'volume_category': volume_category
                })
            
            return analysis_results
            
        except Exception as e:
            print(f"❌ Error analyzing trade history: {e}")
            return []
    
    def get_symbol_performance_analysis(self, symbol: str = None, mode: str = "dry_run", days: int = 7) -> Dict:
        """
        Menganalisis performa indikator per symbol atau keseluruhan
        """
        trades = self.get_trade_history_analysis(mode, days)
        
        if symbol:
            trades = [t for t in trades if t['symbol'] == symbol]
        
        if not trades:
            return {}
        
        # Group by symbol
        symbol_stats = {}
        
        for trade in trades:
            sym = trade['symbol']
            if sym not in symbol_stats:
                symbol_stats[sym] = {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'total_pnl': 0,
                    'avg_pass_rate': 0,
                    'indicator_performance': {},
                    'trades': []
                }
            
            stats = symbol_stats[sym]
            stats['total_trades'] += 1
            stats['total_pnl'] += trade['pnl']
            stats['avg_pass_rate'] += trade['pass_rate']
            stats['trades'].append(trade)
            
            if trade['pnl'] > 0:
                stats['winning_trades'] += 1
            else:
                stats['losing_trades'] += 1
            
            # Analyze indicator performance
            for indicator in trade['passed_indicators']:
                ind_name = indicator['name']
                if ind_name not in stats['indicator_performance']:
                    stats['indicator_performance'][ind_name] = {'passed': 0, 'total': 0, 'win_when_passed': 0}
                
                stats['indicator_performance'][ind_name]['passed'] += 1
                stats['indicator_performance'][ind_name]['total'] += 1
                if trade['pnl'] > 0:
                    stats['indicator_performance'][ind_name]['win_when_passed'] += 1
            
            for indicator in trade['failed_indicators']:
                ind_name = indicator['name']
                if ind_name not in stats['indicator_performance']:
                    stats['indicator_performance'][ind_name] = {'passed': 0, 'total': 0, 'win_when_passed': 0}
                
                stats['indicator_performance'][ind_name]['total'] += 1
        
        # Calculate averages and percentages
        for sym, stats in symbol_stats.items():
            if stats['total_trades'] > 0:
                stats['win_rate'] = (stats['winning_trades'] / stats['total_trades']) * 100
                stats['avg_pass_rate'] = stats['avg_pass_rate'] / stats['total_trades']
                stats['avg_pnl'] = stats['total_pnl'] / stats['total_trades']
                
                # Calculate indicator success rates
                for ind_name, ind_stats in stats['indicator_performance'].items():
                    if ind_stats['total'] > 0:
                        ind_stats['pass_rate'] = (ind_stats['passed'] / ind_stats['total']) * 100
                    if ind_stats['passed'] > 0:
                        ind_stats['win_rate_when_passed'] = (ind_stats['win_when_passed'] / ind_stats['passed']) * 100
                    else:
                        ind_stats['win_rate_when_passed'] = 0
        
        return symbol_stats
    
    def get_market_cap_analysis(self, mode: str = "dry_run", days: int = 7) -> Dict:
        """
        Menganalisis performa berdasarkan kategori market cap
        """
        trades = self.get_trade_history_analysis(mode, days)
        
        if not trades:
            return {}
        
        # Group by market cap category
        market_cap_stats = {}
        
        for trade in trades:
            category = trade.get('market_cap_category', 'Unknown')
            if not category:
                category = 'Unknown'
                
            if category not in market_cap_stats:
                market_cap_stats[category] = {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'total_pnl': 0,
                    'avg_pass_rate': 0,
                    'avg_market_cap': 0,
                    'trades': []
                }
            
            stats = market_cap_stats[category]
            stats['total_trades'] += 1
            stats['total_pnl'] += trade['pnl']
            stats['avg_pass_rate'] += trade['pass_rate']
            stats['avg_market_cap'] += trade.get('market_cap', 0)
            stats['trades'].append(trade)
            
            if trade['pnl'] > 0:
                stats['winning_trades'] += 1
        
        # Calculate percentages and averages
        for category, stats in market_cap_stats.items():
            if stats['total_trades'] > 0:
                stats['win_rate'] = (stats['winning_trades'] / stats['total_trades']) * 100
                stats['avg_pass_rate'] = stats['avg_pass_rate'] / stats['total_trades']
                stats['avg_pnl'] = stats['total_pnl'] / stats['total_trades']
                stats['avg_market_cap'] = stats['avg_market_cap'] / stats['total_trades']
        
        return market_cap_stats
    
    def get_volume_analysis(self, mode: str = "dry_run", days: int = 7) -> Dict:
        """
        Menganalisis performa berdasarkan kategori volume
        """
        trades = self.get_trade_history_analysis(mode, days)
        
        if not trades:
            return {}
        
        # Group by volume category
        volume_stats = {}
        
        for trade in trades:
            category = trade.get('volume_category', 'Unknown')
            if not category:
                category = 'Unknown'
                
            if category not in volume_stats:
                volume_stats[category] = {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'total_pnl': 0,
                    'avg_pass_rate': 0,
                    'avg_volume': 0,
                    'avg_liquidity_score': 0,
                    'trades': []
                }
            
            stats = volume_stats[category]
            stats['total_trades'] += 1
            stats['total_pnl'] += trade['pnl']
            stats['avg_pass_rate'] += trade['pass_rate']
            stats['avg_volume'] += trade.get('total_volume_24h', 0)
            stats['avg_liquidity_score'] += trade.get('liquidity_score', 0)
            stats['trades'].append(trade)
            
            if trade['pnl'] > 0:
                stats['winning_trades'] += 1
        
        # Calculate percentages and averages
        for category, stats in volume_stats.items():
            if stats['total_trades'] > 0:
                stats['win_rate'] = (stats['winning_trades'] / stats['total_trades']) * 100
                stats['avg_pass_rate'] = stats['avg_pass_rate'] / stats['total_trades']
                stats['avg_pnl'] = stats['total_pnl'] / stats['total_trades']
                stats['avg_volume'] = stats['avg_volume'] / stats['total_trades']
                stats['avg_liquidity_score'] = stats['avg_liquidity_score'] / stats['total_trades']
        
        return volume_stats
    
    def get_market_conditions_analysis(self, mode: str = "dry_run", days: int = 7) -> Dict:
        """
        Menganalisis performa berdasarkan kondisi pasar (volatility, market dominance, dll)
        """
        trades = self.get_trade_history_analysis(mode, days)
        
        if not trades:
            return {}
        
        # Categorize by volatility and market dominance
        conditions_stats = {
            'high_volatility': {'trades': [], 'threshold': 5.0},  # >5% volatility
            'low_volatility': {'trades': [], 'threshold': 5.0},   # <=5% volatility
            'high_dominance': {'trades': [], 'threshold': 50.0},  # >50% market dominance
            'low_dominance': {'trades': [], 'threshold': 50.0},   # <=50% market dominance
            'high_liquidity': {'trades': [], 'threshold': 10.0},  # >10 liquidity score
            'low_liquidity': {'trades': [], 'threshold': 10.0}    # <=10 liquidity score
        }
        
        for trade in trades:
            volatility = trade.get('volatility_score', 0)
            dominance = trade.get('market_dominance', 0)
            liquidity = trade.get('liquidity_score', 0)
            
            # Categorize by volatility
            if volatility > conditions_stats['high_volatility']['threshold']:
                conditions_stats['high_volatility']['trades'].append(trade)
            else:
                conditions_stats['low_volatility']['trades'].append(trade)
            
            # Categorize by market dominance
            if dominance > conditions_stats['high_dominance']['threshold']:
                conditions_stats['high_dominance']['trades'].append(trade)
            else:
                conditions_stats['low_dominance']['trades'].append(trade)
            
            # Categorize by liquidity
            if liquidity > conditions_stats['high_liquidity']['threshold']:
                conditions_stats['high_liquidity']['trades'].append(trade)
            else:
                conditions_stats['low_liquidity']['trades'].append(trade)
        
        # Calculate stats for each condition
        for condition, data in conditions_stats.items():
            trades_list = data['trades']
            if trades_list:
                winning_trades = len([t for t in trades_list if t['pnl'] > 0])
                total_pnl = sum(t['pnl'] for t in trades_list)
                avg_pass_rate = sum(t['pass_rate'] for t in trades_list) / len(trades_list)
                
                data.update({
                    'total_trades': len(trades_list),
                    'winning_trades': winning_trades,
                    'win_rate': (winning_trades / len(trades_list)) * 100,
                    'total_pnl': total_pnl,
                    'avg_pnl': total_pnl / len(trades_list),
                    'avg_pass_rate': avg_pass_rate
                })
            else:
                data.update({
                    'total_trades': 0,
                    'winning_trades': 0,
                    'win_rate': 0,
                    'total_pnl': 0,
                    'avg_pnl': 0,
                    'avg_pass_rate': 0
                })
        
        return conditions_stats
    
    def generate_strategy_report(self, mode: str = "dry_run", days: int = 7) -> str:
        """
        Generate comprehensive strategy analysis report
        """
        open_positions = self.get_open_positions_analysis(mode)
        trade_history = self.get_trade_history_analysis(mode, days)
        symbol_performance = self.get_symbol_performance_analysis(None, mode, days)
        
        report = f"""
📊 STRATEGY ANALYSIS REPORT ({mode.upper()})
{'='*60}
📅 Period: Last {days} days
⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🔄 OPEN POSITIONS ({len(open_positions)})
{'-'*40}
"""
        
        for pos in open_positions[:5]:  # Show top 5
            report += f"""
🎯 {pos['symbol']} {pos['direction']} | Pass Rate: {pos['pass_rate']:.1f}%
   💰 Entry: ${pos['entry_price']:.4f} | Current: ${pos['current_price']:.4f}
   📈 PnL: {pos['pnl_percentage']:.2f}%
   ✅ Passed: {len(pos['passed_indicators'])}/{pos['total_indicators']}
   ❌ Failed: {len(pos['failed_indicators'])}/{pos['total_indicators']}
"""
        
        report += f"""

📈 TRADE HISTORY ({len(trade_history)} trades)
{'-'*40}
"""
        
        if trade_history:
            total_pnl = sum(t['pnl'] for t in trade_history)
            winning_trades = len([t for t in trade_history if t['pnl'] > 0])
            win_rate = (winning_trades / len(trade_history)) * 100
            avg_pass_rate = sum(t['pass_rate'] for t in trade_history) / len(trade_history)
            
            report += f"""
📊 Overall Performance:
   💰 Total PnL: ${total_pnl:.2f}
   🎯 Win Rate: {win_rate:.1f}% ({winning_trades}/{len(trade_history)})
   ✅ Avg Pass Rate: {avg_pass_rate:.1f}%
"""
        
        report += f"""

🎯 TOP PERFORMING SYMBOLS
{'-'*40}
"""
        
        # Sort symbols by win rate
        sorted_symbols = sorted(symbol_performance.items(), 
                              key=lambda x: x[1]['win_rate'], reverse=True)
        
        for symbol, stats in sorted_symbols[:5]:
            report += f"""
📊 {symbol}:
   🎯 Win Rate: {stats['win_rate']:.1f}% ({stats['winning_trades']}/{stats['total_trades']})
   💰 Avg PnL: ${stats['avg_pnl']:.2f}
   ✅ Avg Pass Rate: {stats['avg_pass_rate']:.1f}%
"""
        
        return report

# Global instance
indicator_analyzer = IndicatorAnalysisSystem()

def get_indicator_analyzer():
    """Get global indicator analyzer instance"""
    return indicator_analyzer

if __name__ == "__main__":
    # Test the system
    analyzer = IndicatorAnalysisSystem()
    
    print("🧪 Testing Indicator Analysis System...")
    
    # Test open positions
    open_positions = analyzer.get_open_positions_analysis("dry_run")
    print(f"📊 Found {len(open_positions)} open positions")
    
    # Test trade history
    trade_history = analyzer.get_trade_history_analysis("dry_run", 7)
    print(f"📈 Found {len(trade_history)} trades in last 7 days")
    
    # Generate report
    report = analyzer.generate_strategy_report("dry_run", 7)
    print("\n" + report)