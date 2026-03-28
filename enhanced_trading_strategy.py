#!/usr/bin/env python3
"""
ENHANCED TRADING STRATEGY
Strategy utama dengan semua critical fixes terintegrasi
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging

from integrated_risk_management_system import (
    SessionType, TradeDirection, Position, MarketData,
    CorrelationRiskManager, ScoringSystem, PsychologicalProtection,
    RealisticRiskReward, MarketRegimeDetector
)

logger = logging.getLogger(__name__)

class EnhancedTradingStrategy:
    """
    Strategy utama dengan semua critical fixes:
    1. Correlation Risk Management
    2. Realistic Risk/Reward Ratios
    3. Scoring System (replace over-confluence)
    4. Psychological Protection
    5. Market Regime Detection
    """
    
    def __init__(self, config_path: str = "strategy_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize all risk management components
        self.correlation_manager = CorrelationRiskManager(
            max_correlated_positions=self.config.get('max_correlated_positions', 3),
            max_total_risk=self.config.get('max_total_risk', 3.0),
            max_group_risk=self.config.get('max_group_risk', 2.0)
        )
        
        self.scoring_system = ScoringSystem()
        self.psychological_protection = PsychologicalProtection()
        self.risk_reward = RealisticRiskReward()
        self.regime_detector = MarketRegimeDetector()
        
        # Strategy state
        self.current_positions: List[Position] = []
        self.base_risk_percent = self.config.get('base_risk_percent', 0.5)
        self.max_positions = self.config.get('max_positions', 8)
        
        # Performance tracking
        self.performance_db = "strategy_performance.db"
        self._init_performance_db()
        
        logger.info("Enhanced Trading Strategy initialized with all risk management components")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load konfigurasi strategy"""
        default_config = {
            'base_risk_percent': 0.5,
            'max_positions': 8,
            'max_correlated_positions': 3,
            'max_total_risk': 3.0,
            'max_group_risk': 2.0,
            'enable_psychological_protection': True,
            'enable_correlation_protection': True,
            'enable_regime_detection': True,
            'min_market_cap': 500_000_000,
            'max_spread': 0.002,
            'session_weights': {
                'dead_zone': 1.0,
                'asia': 0.8,
                'london': 1.2,
                'newyork': 1.0
            }
        }
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                # Merge dengan default config
                default_config.update(config)
                return default_config
        except FileNotFoundError:
            logger.info(f"Config file {self.config_path} not found, using defaults")
            # Save default config
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def _init_performance_db(self):
        """Initialize database untuk tracking performance"""
        conn = sqlite3.connect(self.performance_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                session TEXT,
                action TEXT,
                entry_score INTEGER,
                score_breakdown TEXT,
                regime_data TEXT,
                correlation_check TEXT,
                psychological_state TEXT,
                risk_percent REAL,
                expected_rr REAL,
                actual_result TEXT,
                actual_rr REAL,
                notes TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_performance (
                date TEXT PRIMARY KEY,
                total_signals INTEGER,
                signals_taken INTEGER,
                signals_blocked_correlation INTEGER,
                signals_blocked_psychological INTEGER,
                signals_blocked_regime INTEGER,
                signals_blocked_score INTEGER,
                avg_score REAL,
                total_risk_deployed REAL,
                session_breakdown TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def analyze_opportunity(self, symbol: str, session: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisis lengkap opportunity dengan semua risk checks
        
        Returns:
            Dict dengan action, reason, score, risk_percent, exit_levels, dll
        """
        
        # Convert ke enum dan dataclass
        try:
            session_enum = SessionType(session.lower())
        except ValueError:
            return {
                'action': TradeDirection.HOLD.value,
                'reason': f'Invalid session: {session}',
                'score': 0,
                'timestamp': datetime.now().isoformat()
            }
        
        # Convert market data ke MarketData object
        try:
            market_data_obj = MarketData(
                symbol=symbol,
                price=market_data['price'],
                ema_20=market_data.get('ema_20', market_data['price']),
                ema_50=market_data.get('ema_50', market_data['price']),
                ema_200=market_data.get('ema_200', market_data['price']),
                rsi=market_data.get('rsi', 50),
                atr=market_data.get('atr', market_data['price'] * 0.02),
                volume=market_data.get('volume', 1000000),
                avg_volume=market_data.get('avg_volume', 1000000),
                market_cap=market_data.get('market_cap', 1_000_000_000),
                spread=market_data.get('spread', 0.001),
                volatility=market_data.get('volatility', 0.5),
                price_history=market_data.get('price_history', [market_data['price']] * 100),
                volume_history=market_data.get('volume_history', [1000000] * 100)
            )
        except KeyError as e:
            return {
                'action': TradeDirection.HOLD.value,
                'reason': f'Missing required market data: {e}',
                'score': 0,
                'timestamp': datetime.now().isoformat()
            }
        
        analysis_result = {
            'symbol': symbol,
            'session': session,
            'timestamp': datetime.now().isoformat(),
            'checks_performed': []
        }
        
        # 1. PSYCHOLOGICAL PROTECTION CHECK
        if self.config['enable_psychological_protection']:
            should_pause, pause_reason = self.psychological_protection.should_pause_trading()
            if should_pause:
                analysis_result.update({
                    'action': TradeDirection.HOLD.value,
                    'reason': f'Psychological protection: {pause_reason}',
                    'score': 0,
                    'psychological_state': self.psychological_protection.get_status()
                })
                self._log_analysis(analysis_result, 'blocked_psychological')
                return analysis_result
            
            analysis_result['checks_performed'].append('psychological_protection_passed')
        
        # 2. CORRELATION RISK CHECK
        if self.config['enable_correlation_protection']:
            correlation_allowed, correlation_reason = self.correlation_manager.check_correlation_risk(
                symbol, self.current_positions
            )
            if not correlation_allowed:
                analysis_result.update({
                    'action': TradeDirection.HOLD.value,
                    'reason': f'Correlation risk: {correlation_reason}',
                    'score': 0,
                    'correlation_check': correlation_reason
                })
                self._log_analysis(analysis_result, 'blocked_correlation')
                return analysis_result
            
            analysis_result['checks_performed'].append('correlation_check_passed')
            analysis_result['correlation_check'] = correlation_reason
        
        # 3. MARKET REGIME CHECK
        if self.config['enable_regime_detection']:
            regime = self.regime_detector.detect_regime(
                market_data_obj.price_history,
                market_data_obj.volume_history,
                market_data_obj.volatility
            )
            
            regime_suitable, regime_reason = self.regime_detector.should_trade_session(
                session_enum, regime
            )
            
            if not regime_suitable:
                analysis_result.update({
                    'action': TradeDirection.HOLD.value,
                    'reason': f'Market regime: {regime_reason}',
                    'score': 0,
                    'regime_data': regime
                })
                self._log_analysis(analysis_result, 'blocked_regime')
                return analysis_result
            
            analysis_result['checks_performed'].append('regime_check_passed')
            analysis_result['regime_data'] = regime
        
        # 4. SCORING SYSTEM
        entry_score, score_breakdown = self.scoring_system.calculate_entry_score(
            market_data_obj, session_enum
        )
        
        min_score = self.scoring_system.min_scores[session_enum]
        
        if entry_score < min_score:
            analysis_result.update({
                'action': TradeDirection.HOLD.value,
                'reason': f'Score too low: {entry_score}/{min_score}',
                'score': entry_score,
                'score_breakdown': score_breakdown
            })
            self._log_analysis(analysis_result, 'blocked_score')
            return analysis_result
        
        analysis_result['checks_performed'].append('scoring_passed')
        analysis_result['score'] = entry_score
        analysis_result['score_breakdown'] = score_breakdown
        
        # 5. DETERMINE TRADE DIRECTION
        direction = self._determine_direction(session_enum, market_data_obj)
        
        if direction == TradeDirection.HOLD:
            analysis_result.update({
                'action': TradeDirection.HOLD.value,
                'reason': 'No clear directional signal',
                'score': entry_score
            })
            self._log_analysis(analysis_result, 'no_signal')
            return analysis_result
        
        # 6. CALCULATE POSITION SIZE
        risk_adjustment = self.psychological_protection.get_risk_adjustment()
        session_weight = self.config['session_weights'].get(session, 1.0)
        
        position_risk = self.base_risk_percent * risk_adjustment * session_weight
        
        # 7. GET EXIT LEVELS
        exit_levels = self.risk_reward.get_exit_levels(
            session_enum, market_data_obj.price, direction, market_data_obj.atr
        )
        
        # 8. FINAL RESULT
        analysis_result.update({
            'action': direction.value,
            'reason': f'All checks passed - Score: {entry_score}/{min_score}',
            'score': entry_score,
            'risk_percent': position_risk,
            'risk_adjustment': risk_adjustment,
            'session_weight': session_weight,
            'exit_levels': exit_levels,
            'psychological_state': self.psychological_protection.get_status()
        })
        
        self._log_analysis(analysis_result, 'signal_generated')
        return analysis_result
    
    def _determine_direction(self, session: SessionType, data: MarketData) -> TradeDirection:
        """Tentukan arah trade berdasarkan session dan data"""
        
        price = data.price
        ema_20 = data.ema_20
        rsi = data.rsi
        volume_ratio = data.volume_ratio
        trend_strength = data.trend_strength
        
        if session == SessionType.DEAD_ZONE:
            # Dead zone: conservative, clear trend + extreme RSI
            if (price > ema_20 * 1.01 and rsi < 35 and 
                trend_strength > 0.01 and volume_ratio < 1.5):
                return TradeDirection.LONG
            elif (price < ema_20 * 0.99 and rsi > 65 and 
                  trend_strength < -0.01 and volume_ratio < 1.5):
                return TradeDirection.SHORT
        
        elif session == SessionType.ASIA:
            # Asia: mean reversion, avoid volume spikes
            if (rsi < 40 and volume_ratio < 1.3 and 
                abs(trend_strength) < 0.02):  # Ranging market
                return TradeDirection.LONG
            elif (rsi > 60 and volume_ratio < 1.3 and 
                  abs(trend_strength) < 0.02):
                return TradeDirection.SHORT
        
        elif session == SessionType.LONDON:
            # London: breakout, trend + volume
            if (price > ema_20 and volume_ratio > 1.1 and 
                trend_strength > 0.015):
                return TradeDirection.LONG
            elif (price < ema_20 and volume_ratio > 1.1 and 
                  trend_strength < -0.015):
                return TradeDirection.SHORT
        
        elif session == SessionType.NEWYORK:
            # New York: momentum, RSI + volume + trend
            if (rsi > 45 and volume_ratio > 1.2 and 
                trend_strength > 0.01):
                return TradeDirection.LONG
            elif (rsi < 55 and volume_ratio > 1.2 and 
                  trend_strength < -0.01):
                return TradeDirection.SHORT
        
        return TradeDirection.HOLD
    
    def add_position(self, symbol: str, direction: str, entry_price: float, 
                    risk_amount: float, session: str) -> bool:
        """Tambah posisi ke tracking"""
        
        if len(self.current_positions) >= self.max_positions:
            logger.warning(f"Max positions reached: {len(self.current_positions)}")
            return False
        
        correlation_group = self.correlation_manager.get_correlation_group(symbol)
        
        position = Position(
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            risk_amount=risk_amount,
            session=session,
            timestamp=datetime.now(),
            correlation_group=correlation_group
        )
        
        self.current_positions.append(position)
        logger.info(f"Position added: {symbol} {direction} @ {entry_price}")
        return True
    
    def remove_position(self, symbol: str, result: str, profit_r: float) -> bool:
        """Remove posisi dan update psychological state"""
        
        for i, pos in enumerate(self.current_positions):
            if pos.symbol == symbol:
                self.current_positions.pop(i)
                
                # Update psychological protection
                self.psychological_protection.update_trade_result(symbol, result, profit_r)
                
                logger.info(f"Position removed: {symbol} - {result} ({profit_r:.2f}R)")
                return True
        
        logger.warning(f"Position not found for removal: {symbol}")
        return False
    
    def _log_analysis(self, analysis_result: Dict[str, Any], result_type: str):
        """Log hasil analisis ke database"""
        
        conn = sqlite3.connect(self.performance_db)
        cursor = conn.cursor()
        
        # Convert datetime objects to strings for JSON serialization
        def convert_datetime_to_string(obj):
            if isinstance(obj, dict):
                return {k: convert_datetime_to_string(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime_to_string(item) for item in obj]
            elif isinstance(obj, datetime):
                return obj.isoformat()
            else:
                return obj
        
        # Clean data for JSON serialization
        regime_data = convert_datetime_to_string(analysis_result.get('regime_data', {}))
        psychological_state = convert_datetime_to_string(analysis_result.get('psychological_state', {}))
        
        cursor.execute('''
            INSERT INTO trade_analysis 
            (timestamp, symbol, session, action, entry_score, score_breakdown, 
             regime_data, correlation_check, psychological_state, risk_percent, 
             expected_rr, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            analysis_result['timestamp'],
            analysis_result['symbol'],
            analysis_result['session'],
            analysis_result['action'],
            analysis_result.get('score', 0),
            json.dumps(analysis_result.get('score_breakdown', {})),
            json.dumps(regime_data),
            analysis_result.get('correlation_check', ''),
            json.dumps(psychological_state),
            analysis_result.get('risk_percent', 0),
            analysis_result.get('exit_levels', {}).get('expected_rr', 0),
            result_type
        ))
        
        conn.commit()
        conn.close()
    
    def get_strategy_status(self) -> Dict[str, Any]:
        """Dapatkan status lengkap strategy"""
        
        total_risk = sum(pos.risk_amount for pos in self.current_positions)
        
        # Group positions by correlation
        correlation_groups = {}
        for pos in self.current_positions:
            group = pos.correlation_group or 'uncorrelated'
            if group not in correlation_groups:
                correlation_groups[group] = []
            correlation_groups[group].append(pos.symbol)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_positions': len(self.current_positions),
            'max_positions': self.max_positions,
            'total_risk_deployed': total_risk,
            'max_total_risk': self.config['max_total_risk'],
            'correlation_groups': correlation_groups,
            'psychological_status': self.psychological_protection.get_status(),
            'base_risk_percent': self.base_risk_percent,
            'current_positions': [pos.to_dict() for pos in self.current_positions],
            'config': self.config
        }
    
    def get_performance_summary(self, days: int = 7) -> Dict[str, Any]:
        """Dapatkan ringkasan performance beberapa hari terakhir"""
        
        conn = sqlite3.connect(self.performance_db)
        cursor = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Total signals
        cursor.execute('''
            SELECT COUNT(*) as total_signals,
                   SUM(CASE WHEN action != 'HOLD' THEN 1 ELSE 0 END) as signals_taken,
                   SUM(CASE WHEN notes = 'blocked_correlation' THEN 1 ELSE 0 END) as blocked_correlation,
                   SUM(CASE WHEN notes = 'blocked_psychological' THEN 1 ELSE 0 END) as blocked_psychological,
                   SUM(CASE WHEN notes = 'blocked_regime' THEN 1 ELSE 0 END) as blocked_regime,
                   SUM(CASE WHEN notes = 'blocked_score' THEN 1 ELSE 0 END) as blocked_score,
                   AVG(entry_score) as avg_score
            FROM trade_analysis 
            WHERE timestamp >= ?
        ''', (start_date,))
        
        summary = cursor.fetchone()
        
        # Session breakdown
        cursor.execute('''
            SELECT session, 
                   COUNT(*) as total,
                   SUM(CASE WHEN action != 'HOLD' THEN 1 ELSE 0 END) as taken,
                   AVG(entry_score) as avg_score
            FROM trade_analysis 
            WHERE timestamp >= ?
            GROUP BY session
        ''', (start_date,))
        
        session_breakdown = cursor.fetchall()
        
        conn.close()
        
        return {
            'period_days': days,
            'total_signals': summary[0] or 0,
            'signals_taken': summary[1] or 0,
            'blocked_correlation': summary[2] or 0,
            'blocked_psychological': summary[3] or 0,
            'blocked_regime': summary[4] or 0,
            'blocked_score': summary[5] or 0,
            'avg_score': summary[6] or 0,
            'session_breakdown': {
                row[0]: {
                    'total': row[1],
                    'taken': row[2],
                    'avg_score': row[3]
                } for row in session_breakdown
            }
        }

# Example usage dan testing
if __name__ == "__main__":
    # Initialize strategy
    strategy = EnhancedTradingStrategy()
    
    # Example market data
    market_data = {
        'price': 50000,
        'ema_20': 49500,
        'ema_50': 49000,
        'ema_200': 48000,
        'rsi': 35,
        'atr': 1000,
        'volume': 1100000,
        'avg_volume': 1000000,
        'market_cap': 1_000_000_000,
        'spread': 0.001,
        'volatility': 0.6,
        'price_history': [48000 + i*100 for i in range(100)],
        'volume_history': [1000000] * 100
    }
    
    # Test different sessions
    sessions = ['dead_zone', 'asia', 'london', 'newyork']
    
    print("=== ENHANCED TRADING STRATEGY TEST ===\n")
    
    for session in sessions:
        print(f"--- {session.upper()} SESSION ---")
        result = strategy.analyze_opportunity('BTC', session, market_data)
        
        print(f"Action: {result['action']}")
        print(f"Score: {result.get('score', 0)}")
        print(f"Reason: {result['reason']}")
        
        if result['action'] != 'HOLD':
            print(f"Risk: {result.get('risk_percent', 0):.2f}%")
            print(f"Expected R/R: {result.get('exit_levels', {}).get('expected_rr', 0)}")
        
        print(f"Checks: {result.get('checks_performed', [])}")
        print()
    
    # Show strategy status
    print("--- STRATEGY STATUS ---")
    status = strategy.get_strategy_status()
    print(f"Total Positions: {status['total_positions']}/{status['max_positions']}")
    print(f"Total Risk: {status['total_risk_deployed']:.2f}%/{status['max_total_risk']}%")
    print(f"Psychological State: {status['psychological_status']['emotional_state']}")
    print(f"Risk Adjustment: {status['psychological_status']['risk_adjustment']}")