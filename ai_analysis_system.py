#!/usr/bin/env python3
"""
AI Analysis System
Sistem analisis AI yang membedakan antara real-time dan historical analysis
"""
import sqlite3
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from indicator_analysis_system import get_indicator_analyzer
from market_data_system import get_market_data_system

class AIAnalysisSystem:
    def __init__(self):
        self.dry_run_db = "dry_run_trades.db"
        self.real_db = "real_trades.db"
    
    async def get_realtime_analysis(self, symbol: str, direction: str = None) -> Dict:
        """
        Analisis real-time untuk koin tertentu
        Mengambil data market langsung dari API
        """
        try:
            # Get real-time market data
            market_system = get_market_data_system()
            market_data = await market_system.get_market_data(symbol)
            
            # Get historical performance for this symbol
            analyzer = get_indicator_analyzer()
            
            # Analyze both dry run and real trades
            dry_run_performance = analyzer.get_symbol_performance_analysis(symbol, "dry_run", 30)
            real_performance = analyzer.get_symbol_performance_analysis(symbol, "real", 30)
            
            # Get market conditions analysis
            market_cap_analysis = analyzer.get_market_cap_analysis("dry_run", 30)
            volume_analysis = analyzer.get_volume_analysis("dry_run", 30)
            conditions_analysis = analyzer.get_market_conditions_analysis("dry_run", 30)
            
            # Categorize current market data
            market_cap_category = market_system.categorize_market_cap(market_data.get('market_cap', 0))
            volume_category = market_system.categorize_volume(market_data.get('total_volume_24h', 0))
            
            analysis = {
                'symbol': symbol,
                'analysis_type': 'realtime',
                'timestamp': datetime.now().isoformat(),
                'current_market_data': {
                    'market_cap': market_data.get('market_cap', 0),
                    'market_cap_category': market_cap_category,
                    'market_cap_rank': market_data.get('market_cap_rank', 0),
                    'volume_24h': market_data.get('total_volume_24h', 0),
                    'volume_category': volume_category,
                    'liquidity_score': market_data.get('liquidity_score', 0),
                    'volatility_score': market_data.get('volatility_score', 0),
                    'market_dominance': market_data.get('market_dominance', 0),
                    'price_change_24h': market_data.get('price_change_percentage_24h', 0),
                    'price_change_7d': market_data.get('price_change_percentage_7d', 0)
                },
                'historical_performance': {
                    'dry_run': dry_run_performance.get(symbol, {}),
                    'real_trade': real_performance.get(symbol, {})
                },
                'market_category_performance': {
                    'market_cap_category': market_cap_analysis.get(market_cap_category, {}),
                    'volume_category': volume_analysis.get(volume_category, {})
                },
                'market_conditions_performance': self._get_current_conditions_performance(
                    market_data, conditions_analysis
                ),
                'risk_assessment': self._assess_current_risk(market_data, market_cap_category, volume_category),
                'trading_recommendation': self._get_trading_recommendation(
                    symbol, direction, market_data, dry_run_performance, real_performance
                )
            }
            
            return analysis
            
        except Exception as e:
            print(f"❌ Error in realtime analysis: {e}")
            return {'error': str(e), 'analysis_type': 'realtime'}
    
    def get_historical_trade_analysis(self, trade_id: str = None, symbol: str = None, 
                                    mode: str = "dry_run", limit: int = 10) -> List[Dict]:
        """
        Analisis historical trades dengan data yang tersimpan
        Menampilkan indikator dan market data saat trade dibuka/ditutup
        """
        try:
            db_path = self.dry_run_db if mode == "dry_run" else self.real_db
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Build query
            if trade_id:
                query = '''
                    SELECT * FROM trade_history WHERE id = ?
                '''
                params = (trade_id,)
            elif symbol:
                query = '''
                    SELECT * FROM trade_history WHERE symbol = ?
                    ORDER BY entry_time DESC LIMIT ?
                '''
                params = (symbol, limit)
            else:
                query = '''
                    SELECT * FROM trade_history
                    ORDER BY entry_time DESC LIMIT ?
                '''
                params = (limit,)
            
            cursor.execute(query, params)
            trades = cursor.fetchall()
            conn.close()
            
            analysis_results = []
            
            for trade in trades:
                trade_analysis = self._analyze_historical_trade(trade, mode)
                if trade_analysis:
                    analysis_results.append(trade_analysis)
            
            return analysis_results
            
        except Exception as e:
            print(f"❌ Error in historical trade analysis: {e}")
            return [{'error': str(e), 'analysis_type': 'historical'}]
    
    def get_open_position_analysis(self, position_id: str = None, symbol: str = None, 
                                 mode: str = "dry_run") -> List[Dict]:
        """
        Analisis posisi yang masih terbuka dengan data saat dibuka
        """
        try:
            db_path = self.dry_run_db if mode == "dry_run" else self.real_db
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Build query
            if position_id:
                query = '''
                    SELECT * FROM open_positions WHERE id = ?
                '''
                params = (position_id,)
            elif symbol:
                query = '''
                    SELECT * FROM open_positions WHERE symbol = ?
                    ORDER BY entry_time DESC
                '''
                params = (symbol,)
            else:
                query = '''
                    SELECT * FROM open_positions
                    ORDER BY entry_time DESC
                '''
                params = ()
            
            cursor.execute(query, params)
            positions = cursor.fetchall()
            conn.close()
            
            analysis_results = []
            
            for position in positions:
                position_analysis = self._analyze_open_position(position, mode)
                if position_analysis:
                    analysis_results.append(position_analysis)
            
            return analysis_results
            
        except Exception as e:
            print(f"❌ Error in open position analysis: {e}")
            return [{'error': str(e), 'analysis_type': 'open_position'}]
    
    def _analyze_historical_trade(self, trade_row: tuple, mode: str) -> Dict:
        """Analyze a single historical trade"""
        try:
            # Handle different schema lengths
            if len(trade_row) >= 20:  # New schema with market data
                (trade_id, symbol, direction, entry_price, exit_price, pnl, pnl_percentage,
                 exit_reason, indicators_json, entry_time, exit_time, ai_entry_reasoning, ai_exit_reasoning,
                 market_cap, market_cap_rank, total_volume_24h, liquidity_score, volatility_score,
                 market_dominance, market_cap_category, volume_category) = trade_row[:21]
            else:  # Old schema
                (trade_id, symbol, direction, entry_price, exit_price, pnl, pnl_percentage,
                 exit_reason, indicators_json, entry_time, exit_time) = trade_row[:11]
                ai_entry_reasoning = ai_exit_reasoning = ""
                market_cap = market_cap_rank = total_volume_24h = liquidity_score = volatility_score = market_dominance = 0
                market_cap_category = volume_category = ""
            
            # Parse indicators
            if isinstance(indicators_json, str):
                indicators = json.loads(indicators_json)
            else:
                indicators = indicators_json or {}
            
            # Analyze indicators performance
            analyzer = get_indicator_analyzer()
            passed_indicators, failed_indicators = analyzer.analyze_indicators(indicators, direction)
            
            # Calculate trade duration
            try:
                entry_dt = datetime.fromisoformat(entry_time)
                exit_dt = datetime.fromisoformat(exit_time)
                duration_minutes = int((exit_dt - entry_dt).total_seconds() / 60)
            except:
                duration_minutes = 0
            
            analysis = {
                'trade_id': trade_id,
                'symbol': symbol,
                'direction': direction,
                'analysis_type': 'historical_trade',
                'mode': mode,
                'trade_outcome': {
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'pnl_percentage': pnl_percentage,
                    'exit_reason': exit_reason,
                    'duration_minutes': duration_minutes,
                    'is_profitable': pnl > 0
                },
                'entry_conditions': {
                    'timestamp': entry_time,
                    'indicators': indicators,
                    'passed_indicators': passed_indicators,
                    'failed_indicators': failed_indicators,
                    'pass_rate': (len(passed_indicators) / (len(passed_indicators) + len(failed_indicators)) * 100) if (passed_indicators or failed_indicators) else 0
                },
                'market_conditions_at_entry': {
                    'market_cap': market_cap,
                    'market_cap_category': market_cap_category,
                    'market_cap_rank': market_cap_rank,
                    'volume_24h': total_volume_24h,
                    'volume_category': volume_category,
                    'liquidity_score': liquidity_score,
                    'volatility_score': volatility_score,
                    'market_dominance': market_dominance
                },
                'ai_reasoning': {
                    'entry_reasoning': ai_entry_reasoning,
                    'exit_reasoning': ai_exit_reasoning
                },
                'indicator_analysis': self._analyze_indicator_effectiveness(
                    passed_indicators, failed_indicators, pnl > 0
                )
            }
            
            return analysis
            
        except Exception as e:
            print(f"❌ Error analyzing historical trade: {e}")
            return None
    
    def _analyze_open_position(self, position_row: tuple, mode: str) -> Dict:
        """Analyze a single open position"""
        try:
            # Handle different schema lengths
            if len(position_row) >= 36:  # New schema with market data
                (pos_id, symbol, direction, entry_price, quantity, leverage, 
                 tp_price, sl_price, entry_time, current_price, unrealized_pnl, 
                 indicators_json, position_value_usd, ai_entry_reasoning) = position_row[:14]
                
                # Extract market data
                market_data_cols = position_row[14:36]
                (market_cap, market_cap_rank, total_volume_24h, circulating_supply, total_supply, max_supply,
                 price_change_24h, price_change_percentage_24h, price_change_percentage_7d, price_change_percentage_30d,
                 ath, ath_change_percentage, atl, atl_change_percentage, bybit_volume_24h, bybit_turnover_24h,
                 liquidity_score, volatility_score, market_dominance, market_cap_category, volume_category, market_data_timestamp) = market_data_cols
            else:  # Old schema
                (pos_id, symbol, direction, entry_price, quantity, leverage, 
                 tp_price, sl_price, entry_time, current_price, unrealized_pnl, 
                 indicators_json, position_value_usd) = position_row[:13]
                ai_entry_reasoning = ""
                market_cap = market_cap_rank = total_volume_24h = liquidity_score = volatility_score = market_dominance = 0
                market_cap_category = volume_category = ""
            
            # Parse indicators
            if isinstance(indicators_json, str):
                indicators = json.loads(indicators_json)
            else:
                indicators = indicators_json or {}
            
            # Analyze indicators performance
            analyzer = get_indicator_analyzer()
            passed_indicators, failed_indicators = analyzer.analyze_indicators(indicators, direction)
            
            # Calculate current PnL percentage
            current_pnl_percentage = 0
            if entry_price and current_price:
                if direction == "LONG":
                    current_pnl_percentage = ((current_price - entry_price) / entry_price) * 100
                else:  # SHORT
                    current_pnl_percentage = ((entry_price - current_price) / entry_price) * 100
            
            # Calculate time since entry
            try:
                entry_dt = datetime.fromisoformat(entry_time)
                duration_minutes = int((datetime.now() - entry_dt).total_seconds() / 60)
            except:
                duration_minutes = 0
            
            analysis = {
                'position_id': pos_id,
                'symbol': symbol,
                'direction': direction,
                'analysis_type': 'open_position',
                'mode': mode,
                'position_status': {
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'tp_price': tp_price,
                    'sl_price': sl_price,
                    'quantity': quantity,
                    'leverage': leverage,
                    'position_value_usd': position_value_usd,
                    'unrealized_pnl': unrealized_pnl,
                    'current_pnl_percentage': current_pnl_percentage,
                    'duration_minutes': duration_minutes
                },
                'entry_conditions': {
                    'timestamp': entry_time,
                    'indicators': indicators,
                    'passed_indicators': passed_indicators,
                    'failed_indicators': failed_indicators,
                    'pass_rate': (len(passed_indicators) / (len(passed_indicators) + len(failed_indicators)) * 100) if (passed_indicators or failed_indicators) else 0
                },
                'market_conditions_at_entry': {
                    'market_cap': market_cap,
                    'market_cap_category': market_cap_category,
                    'market_cap_rank': market_cap_rank,
                    'volume_24h': total_volume_24h,
                    'volume_category': volume_category,
                    'liquidity_score': liquidity_score,
                    'volatility_score': volatility_score,
                    'market_dominance': market_dominance
                },
                'ai_reasoning': {
                    'entry_reasoning': ai_entry_reasoning
                },
                'risk_assessment': self._assess_position_risk(
                    current_pnl_percentage, duration_minutes, tp_price, sl_price, current_price, direction
                )
            }
            
            return analysis
            
        except Exception as e:
            print(f"❌ Error analyzing open position: {e}")
            return None
    
    def _get_current_conditions_performance(self, market_data: Dict, conditions_analysis: Dict) -> Dict:
        """Get performance for current market conditions"""
        volatility_score = market_data.get('volatility_score', 0)
        liquidity_score = market_data.get('liquidity_score', 0)
        dominance_score = market_data.get('market_dominance', 0)
        
        performance = {}
        
        # Volatility condition
        vol_condition = 'high_volatility' if volatility_score > 5.0 else 'low_volatility'
        performance['volatility'] = {
            'condition': vol_condition,
            'score': volatility_score,
            'performance': conditions_analysis.get(vol_condition, {})
        }
        
        # Liquidity condition
        liq_condition = 'high_liquidity' if liquidity_score > 10.0 else 'low_liquidity'
        performance['liquidity'] = {
            'condition': liq_condition,
            'score': liquidity_score,
            'performance': conditions_analysis.get(liq_condition, {})
        }
        
        # Dominance condition
        dom_condition = 'high_dominance' if dominance_score > 50.0 else 'low_dominance'
        performance['dominance'] = {
            'condition': dom_condition,
            'score': dominance_score,
            'performance': conditions_analysis.get(dom_condition, {})
        }
        
        return performance
    
    def _assess_current_risk(self, market_data: Dict, market_cap_category: str, volume_category: str) -> Dict:
        """Assess current risk based on market data"""
        risk_factors = []
        risk_score = 0
        
        volatility_score = market_data.get('volatility_score', 0)
        liquidity_score = market_data.get('liquidity_score', 0)
        market_cap = market_data.get('market_cap', 0)
        volume_24h = market_data.get('total_volume_24h', 0)
        
        # Volatility risk
        if volatility_score > 15.0:
            risk_factors.append("Extremely high volatility - very high risk")
            risk_score += 40
        elif volatility_score > 10.0:
            risk_factors.append("Very high volatility - high risk")
            risk_score += 30
        elif volatility_score > 5.0:
            risk_factors.append("High volatility - medium risk")
            risk_score += 20
        
        # Liquidity risk
        if liquidity_score < 2.0:
            risk_factors.append("Very low liquidity - high slippage risk")
            risk_score += 30
        elif liquidity_score < 5.0:
            risk_factors.append("Low liquidity - potential slippage")
            risk_score += 20
        elif liquidity_score < 10.0:
            risk_factors.append("Medium liquidity - monitor closely")
            risk_score += 10
        
        # Market cap risk
        if market_cap_category in ['Nano Cap']:
            risk_factors.append("Nano cap - extreme manipulation risk")
            risk_score += 35
        elif market_cap_category in ['Micro Cap']:
            risk_factors.append("Micro cap - high manipulation risk")
            risk_score += 25
        elif market_cap_category in ['Small Cap']:
            risk_factors.append("Small cap - increased volatility")
            risk_score += 15
        
        # Volume risk
        if volume_category in ['Very Low Volume']:
            risk_factors.append("Very low volume - exit difficulty")
            risk_score += 25
        elif volume_category in ['Low Volume']:
            risk_factors.append("Low volume - limited liquidity")
            risk_score += 15
        
        # Overall risk level
        if risk_score >= 80:
            risk_level = "EXTREME"
        elif risk_score >= 60:
            risk_level = "HIGH"
        elif risk_score >= 40:
            risk_level = "MEDIUM"
        elif risk_score >= 20:
            risk_level = "LOW"
        else:
            risk_level = "MINIMAL"
        
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'recommendation': self._get_risk_recommendation(risk_level, risk_factors)
        }
    
    def _get_risk_recommendation(self, risk_level: str, risk_factors: List[str]) -> str:
        """Get risk-based recommendation"""
        if risk_level == "EXTREME":
            return "AVOID trading - conditions too risky"
        elif risk_level == "HIGH":
            return "Use smaller position size and tight stop loss"
        elif risk_level == "MEDIUM":
            return "Normal position size with careful monitoring"
        elif risk_level == "LOW":
            return "Good conditions for trading"
        else:
            return "Excellent conditions for trading"
    
    def _get_trading_recommendation(self, symbol: str, direction: str, market_data: Dict, 
                                  dry_run_perf: Dict, real_perf: Dict) -> Dict:
        """Get trading recommendation based on all factors"""
        recommendation = {
            'action': 'NEUTRAL',
            'confidence': 50,
            'reasons': []
        }
        
        # Historical performance factor
        if symbol in dry_run_perf:
            dry_stats = dry_run_perf[symbol]
            if dry_stats.get('win_rate', 0) > 70:
                recommendation['reasons'].append(f"High win rate in dry run: {dry_stats['win_rate']:.1f}%")
                recommendation['confidence'] += 15
            elif dry_stats.get('win_rate', 0) < 30:
                recommendation['reasons'].append(f"Low win rate in dry run: {dry_stats['win_rate']:.1f}%")
                recommendation['confidence'] -= 15
        
        if symbol in real_perf:
            real_stats = real_perf[symbol]
            if real_stats.get('win_rate', 0) > 70:
                recommendation['reasons'].append(f"High win rate in real trades: {real_stats['win_rate']:.1f}%")
                recommendation['confidence'] += 20
            elif real_stats.get('win_rate', 0) < 30:
                recommendation['reasons'].append(f"Low win rate in real trades: {real_stats['win_rate']:.1f}%")
                recommendation['confidence'] -= 20
        
        # Market conditions factor
        volatility = market_data.get('volatility_score', 0)
        liquidity = market_data.get('liquidity_score', 0)
        
        if volatility > 10:
            recommendation['reasons'].append("High volatility - increased risk")
            recommendation['confidence'] -= 10
        
        if liquidity < 5:
            recommendation['reasons'].append("Low liquidity - potential slippage")
            recommendation['confidence'] -= 10
        elif liquidity > 15:
            recommendation['reasons'].append("High liquidity - good for trading")
            recommendation['confidence'] += 10
        
        # Determine action
        if recommendation['confidence'] >= 70:
            recommendation['action'] = 'BUY' if direction == 'LONG' else 'SELL'
        elif recommendation['confidence'] <= 30:
            recommendation['action'] = 'AVOID'
        else:
            recommendation['action'] = 'NEUTRAL'
        
        return recommendation
    
    def _analyze_indicator_effectiveness(self, passed_indicators: List[Dict], 
                                       failed_indicators: List[Dict], is_profitable: bool) -> Dict:
        """Analyze effectiveness of indicators for this trade"""
        analysis = {
            'total_indicators': len(passed_indicators) + len(failed_indicators),
            'passed_count': len(passed_indicators),
            'failed_count': len(failed_indicators),
            'pass_rate': 0,
            'indicator_performance': {}
        }
        
        if analysis['total_indicators'] > 0:
            analysis['pass_rate'] = (analysis['passed_count'] / analysis['total_indicators']) * 100
        
        # Analyze each indicator's contribution
        for indicator in passed_indicators:
            name = indicator['name']
            analysis['indicator_performance'][name] = {
                'status': 'passed',
                'expected': indicator['expected'],
                'actual': indicator['actual'],
                'contributed_to_profit': is_profitable
            }
        
        for indicator in failed_indicators:
            name = indicator['name']
            analysis['indicator_performance'][name] = {
                'status': 'failed',
                'expected': indicator['expected'],
                'actual': indicator['actual'],
                'may_have_caused_loss': not is_profitable
            }
        
        return analysis
    
    def _assess_position_risk(self, current_pnl_pct: float, duration_minutes: int, 
                            tp_price: float, sl_price: float, current_price: float, direction: str) -> Dict:
        """Assess risk for open position"""
        risk_assessment = {
            'current_risk_level': 'MEDIUM',
            'factors': [],
            'recommendations': []
        }
        
        # PnL-based risk
        if current_pnl_pct < -10:
            risk_assessment['factors'].append("Large unrealized loss")
            risk_assessment['current_risk_level'] = 'HIGH'
        elif current_pnl_pct < -5:
            risk_assessment['factors'].append("Moderate unrealized loss")
        elif current_pnl_pct > 10:
            risk_assessment['factors'].append("Good profit - consider partial TP")
            risk_assessment['recommendations'].append("Consider taking partial profits")
        
        # Time-based risk
        if duration_minutes > 1440:  # > 24 hours
            risk_assessment['factors'].append("Position held for long time")
            risk_assessment['recommendations'].append("Review position - consider exit")
        elif duration_minutes > 240:  # > 4 hours
            risk_assessment['factors'].append("Position aging")
        
        # Distance to SL/TP
        if current_price and tp_price and sl_price:
            if direction == "LONG":
                distance_to_sl = ((current_price - sl_price) / current_price) * 100
                distance_to_tp = ((tp_price - current_price) / current_price) * 100
            else:  # SHORT
                distance_to_sl = ((sl_price - current_price) / current_price) * 100
                distance_to_tp = ((current_price - tp_price) / current_price) * 100
            
            if distance_to_sl < 2:
                risk_assessment['factors'].append("Very close to stop loss")
                risk_assessment['current_risk_level'] = 'HIGH'
                risk_assessment['recommendations'].append("Monitor closely - near SL")
            elif distance_to_tp < 2:
                risk_assessment['factors'].append("Very close to take profit")
                risk_assessment['recommendations'].append("Consider taking profits soon")
        
        return risk_assessment

# Global instance
ai_analysis_system = AIAnalysisSystem()

def get_ai_analysis_system():
    """Get global AI analysis system instance"""
    return ai_analysis_system

if __name__ == "__main__":
    import asyncio
    
    async def test_ai_analysis():
        system = AIAnalysisSystem()
        
        print("🧪 Testing AI Analysis System...")
        
        # Test real-time analysis
        print("\n1. Testing real-time analysis:")
        realtime = await system.get_realtime_analysis('BTCUSDT', 'LONG')
        print(f"   Real-time analysis for BTCUSDT: {realtime.get('current_market_data', {}).get('market_cap_category', 'N/A')}")
        
        # Test historical analysis
        print("\n2. Testing historical analysis:")
        historical = system.get_historical_trade_analysis(symbol='BTCUSDT', limit=3)
        print(f"   Found {len(historical)} historical trades")
        
        # Test open position analysis
        print("\n3. Testing open position analysis:")
        positions = system.get_open_position_analysis(limit=3)
        print(f"   Found {len(positions)} open positions")
    
    asyncio.run(test_ai_analysis())