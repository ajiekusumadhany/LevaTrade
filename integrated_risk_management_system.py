#!/usr/bin/env python3
"""
INTEGRATED RISK MANAGEMENT SYSTEM
Implementasi lengkap semua critical fixes untuk trading strategy
"""

import numpy as np
import pandas as pd
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SessionType(Enum):
    DEAD_ZONE = "dead_zone"
    ASIA = "asia"
    LONDON = "london"
    NEWYORK = "newyork"

class TradeDirection(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    HOLD = "HOLD"

@dataclass
class Position:
    symbol: str
    direction: str
    entry_price: float
    risk_amount: float
    session: str
    timestamp: datetime
    correlation_group: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)

@dataclass
class MarketData:
    symbol: str
    price: float
    ema_20: float
    ema_50: float
    ema_200: float
    rsi: float
    atr: float
    volume: float
    avg_volume: float
    market_cap: float
    spread: float
    volatility: float
    price_history: List[float]
    volume_history: List[float]
    
    @property
    def volume_ratio(self) -> float:
        return self.volume / self.avg_volume if self.avg_volume > 0 else 1.0
    
    @property
    def trend_strength(self) -> float:
        return (self.price - self.ema_200) / self.ema_200 if self.ema_200 > 0 else 0.0

class CorrelationRiskManager:
    """Mengelola risiko korelasi antar posisi"""
    
    CORRELATION_GROUPS = {
        'BTC_CORRELATED': ['BTC', 'ETH', 'LTC', 'BCH', 'ETC'],
        'DEFI_TOKENS': ['UNI', 'SUSHI', 'AAVE', 'COMP', 'MKR', 'YFI', 'CRV'],
        'LAYER1_CHAINS': ['ETH', 'BNB', 'ADA', 'SOL', 'AVAX', 'DOT', 'MATIC', 'ATOM'],
        'EXCHANGE_TOKENS': ['BNB', 'FTT', 'CRO', 'LEO', 'HT', 'KCS'],
        'MEME_COINS': ['DOGE', 'SHIB', 'PEPE', 'FLOKI', 'BONK'],
        'GAMING_METAVERSE': ['AXS', 'SAND', 'MANA', 'ENJ', 'GALA'],
        'ORACLE_DATA': ['LINK', 'BAND', 'TRB', 'API3'],
        'PRIVACY_COINS': ['XMR', 'ZEC', 'DASH', 'FIRO']
    }
    
    def __init__(self, max_correlated_positions: int = 3, 
                 max_total_risk: float = 3.0, 
                 max_group_risk: float = 2.0):
        self.max_correlated_positions = max_correlated_positions
        self.max_total_risk = max_total_risk
        self.max_group_risk = max_group_risk
        
    def get_correlation_group(self, symbol: str) -> Optional[str]:
        """Cari grup korelasi untuk symbol"""
        symbol_upper = symbol.upper().replace('USDT', '').replace('USD', '')
        
        for group_name, symbols in self.CORRELATION_GROUPS.items():
            if symbol_upper in symbols:
                return group_name
        return None
    
    def check_correlation_risk(self, new_symbol: str, current_positions: List[Position]) -> Tuple[bool, str]:
        """Cek apakah posisi baru melanggar batas korelasi"""
        
        new_group = self.get_correlation_group(new_symbol)
        
        # Hitung posisi dan risk saat ini
        group_positions = 0
        group_risk = 0.0
        total_risk = 0.0
        
        for pos in current_positions:
            total_risk += pos.risk_amount
            
            if new_group and pos.correlation_group == new_group:
                group_positions += 1
                group_risk += pos.risk_amount
        
        # Cek batas total risk
        if total_risk >= self.max_total_risk:
            return False, f"Total risk limit reached: {total_risk:.2f}% >= {self.max_total_risk}%"
        
        # Jika tidak ada grup korelasi, allow trade
        if not new_group:
            return True, "No correlation group found - trade allowed"
        
        # Cek batas posisi dalam grup
        if group_positions >= self.max_correlated_positions:
            return False, f"Correlation limit reached for {new_group}: {group_positions} positions"
        
        # Cek batas risk dalam grup
        if group_risk >= self.max_group_risk:
            return False, f"Group risk limit reached for {new_group}: {group_risk:.2f}%"
        
        return True, f"Correlation check passed - Group: {new_group}, Positions: {group_positions}, Risk: {group_risk:.2f}%"

class ScoringSystem:
    """Sistem scoring untuk mengganti over-confluence"""
    
    def __init__(self):
        self.min_scores = {
            SessionType.DEAD_ZONE: 65,
            SessionType.ASIA: 55,
            SessionType.LONDON: 70,
            SessionType.NEWYORK: 60
        }
        
        # Weight untuk setiap komponen scoring
        self.weights = {
            'rsi': 30,
            'volume': 25,
            'trend_strength': 25,
            'technical_alignment': 20
        }
    
    def calculate_entry_score(self, data: MarketData, session: SessionType) -> Tuple[int, Dict[str, int]]:
        """Hitung skor entry (0-100) dengan breakdown"""
        
        # Hard filters - harus pass atau return 0
        hard_filter_pass, hard_filter_reason = self._check_hard_filters(data)
        if not hard_filter_pass:
            return 0, {'hard_filter_failed': hard_filter_reason}
        
        # Soft filters - scoring components
        scores = {}
        scores['rsi'] = self._score_rsi(data.rsi, session)
        scores['volume'] = self._score_volume(data.volume_ratio, session)
        scores['trend_strength'] = self._score_trend_strength(data.trend_strength, session)
        scores['technical_alignment'] = self._score_technical_alignment(data)
        
        total_score = sum(scores.values())
        return min(total_score, 100), scores
    
    def _check_hard_filters(self, data: MarketData) -> Tuple[bool, str]:
        """Cek filter wajib"""
        
        # Market cap minimum
        if data.market_cap < 500_000_000:  # $500M minimum
            return False, f"Market cap too low: ${data.market_cap/1_000_000:.0f}M"
        
        # Spread maksimum
        if data.spread > 0.002:  # 0.2% max spread
            return False, f"Spread too high: {data.spread*100:.3f}%"
        
        # Basic trend filter
        if data.ema_50 <= 0 or data.ema_200 <= 0:
            return False, "Invalid EMA values"
        
        # Volatility filter (tidak terlalu ekstrem)
        if data.volatility > 3.0:  # 300% volatility
            return False, f"Volatility too high: {data.volatility*100:.1f}%"
        
        return True, "Hard filters passed"
    
    def _score_rsi(self, rsi: float, session: SessionType) -> int:
        """Score komponen RSI (0-30 points)"""
        
        if session == SessionType.DEAD_ZONE:
            # Dead zone: cari extreme levels
            if 20 <= rsi <= 30 or 70 <= rsi <= 80:
                return 30
            elif 15 <= rsi <= 35 or 65 <= rsi <= 85:
                return 20
            elif 10 <= rsi <= 40 or 60 <= rsi <= 90:
                return 10
            else:
                return 0
                
        elif session == SessionType.ASIA:
            # Asia: mean reversion, tapi tidak terlalu ekstrem
            if 25 <= rsi <= 35 or 65 <= rsi <= 75:
                return 25
            elif 20 <= rsi <= 40 or 60 <= rsi <= 80:
                return 15
            elif 15 <= rsi <= 45 or 55 <= rsi <= 85:
                return 8
            else:
                return 0
                
        elif session in [SessionType.LONDON, SessionType.NEWYORK]:
            # London/NY: momentum, prefer normal range
            if 30 <= rsi <= 70:
                return 25
            elif 20 <= rsi <= 30 or 70 <= rsi <= 80:
                return 15
            elif rsi < 20 or rsi > 80:
                return 5
            else:
                return 0
        
        return 0
    
    def _score_volume(self, volume_ratio: float, session: SessionType) -> int:
        """Score komponen volume (0-25 points)"""
        
        if session == SessionType.DEAD_ZONE:
            # Dead zone: prefer lower volume
            if 0.5 <= volume_ratio <= 1.0:
                return 25
            elif 0.3 <= volume_ratio <= 1.2:
                return 15
            elif volume_ratio <= 1.5:
                return 5
            else:
                return 0
        else:
            # Sessions lain: prefer higher volume
            if volume_ratio >= 1.2:
                return 25
            elif volume_ratio >= 1.0:
                return 20
            elif volume_ratio >= 0.8:
                return 10
            elif volume_ratio >= 0.6:
                return 5
            else:
                return 0
    
    def _score_trend_strength(self, trend_strength: float, session: SessionType) -> int:
        """Score kekuatan trend (0-25 points)"""
        
        abs_strength = abs(trend_strength)
        
        if session == SessionType.DEAD_ZONE:
            # Dead zone: butuh trend yang jelas
            if abs_strength >= 0.02:
                return 25
            elif abs_strength >= 0.015:
                return 20
            elif abs_strength >= 0.01:
                return 15
            elif abs_strength >= 0.005:
                return 10
            else:
                return 0
                
        elif session == SessionType.ASIA:
            # Asia: prefer ranging (weak trend)
            if abs_strength <= 0.01:
                return 25
            elif abs_strength <= 0.02:
                return 15
            elif abs_strength <= 0.03:
                return 5
            else:
                return 0
                
        elif session in [SessionType.LONDON, SessionType.NEWYORK]:
            # London/NY: butuh trend kuat
            if abs_strength >= 0.025:
                return 25
            elif abs_strength >= 0.02:
                return 20
            elif abs_strength >= 0.015:
                return 15
            elif abs_strength >= 0.01:
                return 10
            else:
                return 0
        
        return 0
    
    def _score_technical_alignment(self, data: MarketData) -> int:
        """Score alignment indikator teknikal (0-20 points)"""
        
        alignment_count = 0
        
        # Price vs EMA alignment
        if data.price > data.ema_20:
            alignment_count += 1
        
        # EMA trend alignment
        if data.ema_20 > data.ema_50:
            alignment_count += 1
        
        # Strong trend confirmation
        if data.ema_50 > data.ema_200:
            alignment_count += 1
        
        return min(alignment_count * 7, 20)  # Max 20 points

class PsychologicalProtection:
    """Proteksi psikologis untuk mencegah emotional trading"""
    
    def __init__(self, db_path: str = "psychological_state.db"):
        self.db_path = db_path
        self.consecutive_losses = 0
        self.consecutive_wins = 0
        self.daily_trades = 0
        self.last_big_win = None
        self.emotional_state = 'neutral'
        self.daily_reset_time = None
        self.total_trades_today = 0
        
        # Limits
        self.max_consecutive_losses = 8
        self.max_daily_trades = 30
        self.big_win_threshold = 4.0  # 4R
        self.big_win_cooldown_hours = 1
        
        self._init_database()
        self._load_state()
    
    def _init_database(self):
        """Initialize database untuk menyimpan state"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS psychological_state (
                id INTEGER PRIMARY KEY,
                date TEXT UNIQUE,
                consecutive_losses INTEGER,
                consecutive_wins INTEGER,
                daily_trades INTEGER,
                emotional_state TEXT,
                last_big_win TEXT,
                total_trades INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                result TEXT,
                profit_r REAL,
                emotional_state_before TEXT,
                emotional_state_after TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_state(self):
        """Load state dari database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().date().isoformat()
        cursor.execute(
            "SELECT * FROM psychological_state WHERE date = ?", 
            (today,)
        )
        
        result = cursor.fetchone()
        if result:
            _, _, self.consecutive_losses, self.consecutive_wins, \
            self.daily_trades, self.emotional_state, last_big_win_str, self.total_trades_today = result
            
            if last_big_win_str:
                self.last_big_win = datetime.fromisoformat(last_big_win_str)
        
        conn.close()
    
    def _save_state(self):
        """Save state ke database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().date().isoformat()
        last_big_win_str = self.last_big_win.isoformat() if self.last_big_win else None
        
        cursor.execute('''
            INSERT OR REPLACE INTO psychological_state 
            (date, consecutive_losses, consecutive_wins, daily_trades, 
             emotional_state, last_big_win, total_trades)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (today, self.consecutive_losses, self.consecutive_wins, 
              self.daily_trades, self.emotional_state, last_big_win_str, self.total_trades_today))
        
        conn.commit()
        conn.close()
    
    def update_trade_result(self, symbol: str, result: str, profit_r: float):
        """Update state berdasarkan hasil trade"""
        
        old_state = self.emotional_state
        
        # Reset daily counter jika hari baru
        if (not self.daily_reset_time or 
            datetime.now().date() > self.daily_reset_time.date()):
            self.daily_trades = 0
            self.total_trades_today = 0
            self.daily_reset_time = datetime.now()
        
        if result.lower() == 'win':
            self.consecutive_losses = 0
            self.consecutive_wins += 1
            
            # Deteksi big win
            if profit_r >= self.big_win_threshold:
                self.last_big_win = datetime.now()
                self.emotional_state = 'euphoric'
                logger.info(f"Big win detected: {profit_r:.2f}R - entering cooldown")
            elif self.consecutive_wins >= 5:
                self.emotional_state = 'confident'
            else:
                self.emotional_state = 'positive'
        
        else:  # Loss
            self.consecutive_wins = 0
            self.consecutive_losses += 1
            
            if self.consecutive_losses >= 5:
                self.emotional_state = 'frustrated'
                logger.warning(f"Frustrated state: {self.consecutive_losses} consecutive losses")
            elif self.consecutive_losses >= 3:
                self.emotional_state = 'cautious'
            else:
                self.emotional_state = 'neutral'
        
        self.daily_trades += 1
        self.total_trades_today += 1
        
        # Save ke database
        self._save_trade_result(symbol, result, profit_r, old_state, self.emotional_state)
        self._save_state()
        
        logger.info(f"Trade result updated: {result} ({profit_r:.2f}R) - State: {old_state} -> {self.emotional_state}")
    
    def _save_trade_result(self, symbol: str, result: str, profit_r: float, 
                          old_state: str, new_state: str):
        """Save hasil trade ke database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trade_results 
            (timestamp, symbol, result, profit_r, emotional_state_before, emotional_state_after)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), symbol, result, profit_r, old_state, new_state))
        
        conn.commit()
        conn.close()
    
    def should_pause_trading(self) -> Tuple[bool, str]:
        """Cek apakah trading harus di-pause"""
        
        # Pause setelah consecutive losses
        if self.consecutive_losses >= self.max_consecutive_losses:
            return True, f"{self.consecutive_losses} consecutive losses - cooling down for 1 hour"
        
        # Pause setelah big win
        if (self.last_big_win and 
            datetime.now() - self.last_big_win < timedelta(hours=self.big_win_cooldown_hours)):
            remaining = self.big_win_cooldown_hours * 60 - (datetime.now() - self.last_big_win).total_seconds() / 60
            return True, f"Big win cooldown - {remaining:.0f} minutes remaining"
        
        # Pause jika terlalu banyak trades hari ini
        if self.daily_trades >= self.max_daily_trades:
            return True, f"Daily trade limit reached: {self.daily_trades}/{self.max_daily_trades}"
        
        # Pause dalam frustrated state
        if self.emotional_state == 'frustrated':
            return True, "Emotional protection - taking a break"
        
        return False, ""
    
    def get_risk_adjustment(self) -> float:
        """Dapatkan multiplier risk berdasarkan state psikologis"""
        
        adjustments = {
            'euphoric': 0.6,      # Reduce risk after big win
            'confident': 0.8,     # Slight reduction on win streak
            'positive': 1.0,      # Normal risk
            'neutral': 1.0,       # Normal risk
            'cautious': 0.8,      # Slight reduction after losses
            'frustrated': 0.4     # Major reduction after many losses
        }
        
        return adjustments.get(self.emotional_state, 1.0)
    
    def get_status(self) -> Dict[str, Any]:
        """Dapatkan status lengkap"""
        return {
            'consecutive_losses': self.consecutive_losses,
            'consecutive_wins': self.consecutive_wins,
            'daily_trades': self.daily_trades,
            'total_trades_today': self.total_trades_today,
            'emotional_state': self.emotional_state,
            'risk_adjustment': self.get_risk_adjustment(),
            'last_big_win': self.last_big_win.isoformat() if self.last_big_win else None,
            'should_pause': self.should_pause_trading()[0]
        }

class RealisticRiskReward:
    """Sistem R/R yang realistis dengan partial TP"""
    
    def __init__(self):
        self.session_configs = {
            SessionType.DEAD_ZONE: {
                'tp_multiplier': 1.5,      # Reduced from 2.0
                'sl_multiplier': 0.5,      # Increased from 0.4
                'rr_ratio': 3.0,           # Reduced from 5.0
                'partial_tp_1': {'level': 1.5, 'percentage': 50},
                'partial_tp_2': {'level': 2.5, 'percentage': 30},
                'trailing_start': 1.5,
                'trailing_step': 0.3
            },
            SessionType.ASIA: {
                'tp_multiplier': 1.0,      # Reduced from 0.8
                'sl_multiplier': 0.5,      # Increased from 0.4
                'rr_ratio': 2.0,           # Same
                'partial_tp_1': {'level': 1.0, 'percentage': 50},
                'partial_tp_2': {'level': 1.8, 'percentage': 30},
                'trailing_start': 1.0,
                'trailing_step': 0.2
            },
            SessionType.LONDON: {
                'tp_multiplier': 2.0,      # Same
                'sl_multiplier': 0.8,      # Same
                'rr_ratio': 2.5,           # Same
                'partial_tp_1': {'level': 1.5, 'percentage': 40},
                'partial_tp_2': {'level': 2.2, 'percentage': 30},
                'trailing_start': 1.5,
                'trailing_step': 0.3
            },
            SessionType.NEWYORK: {
                'tp_multiplier': 1.5,      # Same
                'sl_multiplier': 0.5,      # Same
                'rr_ratio': 3.0,           # Same
                'partial_tp_1': {'level': 1.5, 'percentage': 50},
                'partial_tp_2': {'level': 2.5, 'percentage': 25},
                'trailing_start': 1.5,
                'trailing_step': 0.3
            }
        }
    
    def get_exit_levels(self, session: SessionType, entry_price: float, 
                       direction: TradeDirection, atr: float) -> Dict[str, Any]:
        """Hitung level exit yang realistis"""
        
        config = self.session_configs[session]
        
        if direction == TradeDirection.LONG:
            stop_loss = entry_price - (atr * config['sl_multiplier'])
            take_profit = entry_price + (atr * config['tp_multiplier'])
            partial_tp_1 = entry_price + (atr * config['partial_tp_1']['level'])
            partial_tp_2 = entry_price + (atr * config['partial_tp_2']['level'])
        else:  # SHORT
            stop_loss = entry_price + (atr * config['sl_multiplier'])
            take_profit = entry_price - (atr * config['tp_multiplier'])
            partial_tp_1 = entry_price - (atr * config['partial_tp_1']['level'])
            partial_tp_2 = entry_price - (atr * config['partial_tp_2']['level'])
        
        return {
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'partial_tp_1': {
                'price': partial_tp_1,
                'percentage': config['partial_tp_1']['percentage']
            },
            'partial_tp_2': {
                'price': partial_tp_2,
                'percentage': config['partial_tp_2']['percentage']
            },
            'trailing_start': config['trailing_start'],
            'trailing_step': config['trailing_step'],
            'expected_rr': config['rr_ratio'],
            'config_used': config
        }

class MarketRegimeDetector:
    """Deteksi kondisi market sebelum apply strategy session"""
    
    def __init__(self):
        self.regime_history = []
        self.max_history = 100
    
    def detect_regime(self, price_data: List[float], volume_data: List[float], 
                     volatility: float) -> Dict[str, Any]:
        """Deteksi regime market saat ini"""
        
        if len(price_data) < 50:
            return {
                'trend': 'unknown',
                'volatility': 'normal',
                'volume': 'normal',
                'confidence': 0.0,
                'timestamp': datetime.now()
            }
        
        # Trend detection
        sma_20 = np.mean(price_data[-20:])
        sma_50 = np.mean(price_data[-50:])
        
        trend_threshold = 0.015  # 1.5%
        if sma_20 > sma_50 * (1 + trend_threshold):
            trend = 'uptrend'
            trend_strength = (sma_20 - sma_50) / sma_50
        elif sma_20 < sma_50 * (1 - trend_threshold):
            trend = 'downtrend'
            trend_strength = (sma_50 - sma_20) / sma_50
        else:
            trend = 'sideways'
            trend_strength = abs(sma_20 - sma_50) / sma_50
        
        # Volatility regime
        if volatility > 1.2:
            vol_regime = 'high_vol'
        elif volatility < 0.4:
            vol_regime = 'low_vol'
        else:
            vol_regime = 'normal_vol'
        
        # Volume regime
        if len(volume_data) >= 20:
            avg_volume = np.mean(volume_data[-20:])
            recent_volume = np.mean(volume_data[-5:])
            
            if recent_volume > avg_volume * 1.3:
                volume_regime = 'high_volume'
            elif recent_volume < avg_volume * 0.8:
                volume_regime = 'low_volume'
            else:
                volume_regime = 'normal_volume'
        else:
            volume_regime = 'normal_volume'
        
        # Confidence calculation
        confidence = min(len(price_data) / 100.0, 1.0)
        
        regime = {
            'trend': trend,
            'trend_strength': trend_strength,
            'volatility': vol_regime,
            'volume': volume_regime,
            'confidence': confidence,
            'timestamp': datetime.now()
        }
        
        # Simpan history
        self.regime_history.append(regime)
        if len(self.regime_history) > self.max_history:
            self.regime_history.pop(0)
        
        return regime
    
    def should_trade_session(self, session: SessionType, regime: Dict[str, Any]) -> Tuple[bool, str]:
        """Cek apakah boleh trade di session ini berdasarkan regime"""
        
        if regime['confidence'] < 0.5:
            return False, "Insufficient data for regime detection"
        
        if session == SessionType.DEAD_ZONE:
            # Dead zone: hanya trade di volatility rendah/normal
            if regime['volatility'] in ['low_vol', 'normal_vol']:
                return True, f"Dead zone suitable - {regime['volatility']}"
            else:
                return False, f"Dead zone not suitable - {regime['volatility']}"
        
        elif session == SessionType.ASIA:
            # Asia: prefer sideways markets
            if regime['trend'] == 'sideways':
                return True, f"Asia suitable - {regime['trend']}"
            else:
                return False, f"Asia not suitable - {regime['trend']}"
        
        elif session == SessionType.LONDON:
            # London: butuh trending markets
            if regime['trend'] in ['uptrend', 'downtrend']:
                return True, f"London suitable - {regime['trend']}"
            else:
                return False, f"London not suitable - {regime['trend']}"
        
        elif session == SessionType.NEWYORK:
            # New York: bisa trade semua regime tapi adjust strategy
            return True, f"NY always suitable - {regime['trend']}, {regime['volatility']}"
        
        return False, "Unknown session type"

# Export semua classes untuk digunakan di file lain
__all__ = [
    'SessionType', 'TradeDirection', 'Position', 'MarketData',
    'CorrelationRiskManager', 'ScoringSystem', 'PsychologicalProtection',
    'RealisticRiskReward', 'MarketRegimeDetector'
]