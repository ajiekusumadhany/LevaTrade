#!/usr/bin/env python3
"""
TRADING SYSTEM WRAPPER
Wrapper untuk mengintegrasikan enhanced strategy dengan sistem yang ada
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from enhanced_trading_strategy import EnhancedTradingStrategy

logger = logging.getLogger(__name__)

class TradingSystemWrapper:
    """
    Wrapper yang mengintegrasikan enhanced strategy dengan sistem trading yang ada
    """
    
    def __init__(self):
        self.enhanced_strategy = EnhancedTradingStrategy()
        logger.info("Trading System Wrapper initialized")
    
    def analyze_trading_opportunity(self, symbol: str, session: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisis opportunity menggunakan enhanced strategy
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            session: Trading session ('dead_zone', 'asia', 'london', 'newyork')
            market_data: Dictionary dengan data market
        
        Returns:
            Dictionary dengan hasil analisis
        """
        
        try:
            # Gunakan enhanced strategy untuk analisis
            result = self.enhanced_strategy.analyze_opportunity(symbol, session, market_data)
            
            # Log hasil analisis
            logger.info(f"Analysis for {symbol} in {session}: {result['action']} (Score: {result.get('score', 0)})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return {
                'action': 'HOLD',
                'reason': f'Analysis error: {str(e)}',
                'score': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    def should_enter_trade(self, symbol: str, session: str, market_data: Dict[str, Any]) -> bool:
        """
        Cek apakah boleh masuk trade
        
        Returns:
            True jika boleh trade, False jika tidak
        """
        
        result = self.analyze_trading_opportunity(symbol, session, market_data)
        return result['action'] in ['LONG', 'SHORT']
    
    def get_trade_parameters(self, symbol: str, session: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Dapatkan parameter trade jika signal valid
        
        Returns:
            Dictionary dengan parameter trade atau None jika tidak ada signal
        """
        
        result = self.analyze_trading_opportunity(symbol, session, market_data)
        
        if result['action'] in ['LONG', 'SHORT']:
            return {
                'symbol': symbol,
                'direction': result['action'],
                'risk_percent': result.get('risk_percent', 0.5),
                'exit_levels': result.get('exit_levels', {}),
                'score': result.get('score', 0),
                'session': session,
                'timestamp': result.get('timestamp')
            }
        
        return None
    
    def add_position(self, symbol: str, direction: str, entry_price: float, 
                    risk_amount: float, session: str) -> bool:
        """Tambah posisi ke tracking"""
        return self.enhanced_strategy.add_position(symbol, direction, entry_price, risk_amount, session)
    
    def close_position(self, symbol: str, result: str, profit_r: float) -> bool:
        """Close posisi dan update psychological state"""
        return self.enhanced_strategy.remove_position(symbol, result, profit_r)
    
    def get_strategy_status(self) -> Dict[str, Any]:
        """Dapatkan status strategy"""
        return self.enhanced_strategy.get_strategy_status()
    
    def get_performance_summary(self, days: int = 7) -> Dict[str, Any]:
        """Dapatkan performance summary"""
        return self.enhanced_strategy.get_performance_summary(days)

# Global instance untuk digunakan di sistem lain
trading_wrapper = TradingSystemWrapper()

# Fungsi-fungsi untuk backward compatibility
def analyze_opportunity(symbol: str, session: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
    """Backward compatibility function"""
    return trading_wrapper.analyze_trading_opportunity(symbol, session, market_data)

def should_trade(symbol: str, session: str, market_data: Dict[str, Any]) -> bool:
    """Backward compatibility function"""
    return trading_wrapper.should_enter_trade(symbol, session, market_data)

def get_trade_params(symbol: str, session: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Backward compatibility function"""
    return trading_wrapper.get_trade_parameters(symbol, session, market_data)
