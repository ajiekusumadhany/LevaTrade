"""
Indicator Analysis System - Menganalisis indikator mana yang passed/failed untuk direction tertentu
"""
from typing import Dict, List, Tuple, Any

class IndicatorAnalysisSystem:
    def __init__(self):
        """Initialize indicator analysis system"""
        pass
    
    def analyze_indicators(self, indicators: Dict, direction: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Analyze which indicators passed vs failed for the given direction
        
        Args:
            indicators: Dictionary of indicator values
            direction: 'LONG' or 'SHORT'
            
        Returns:
            Tuple of (passed_indicators, failed_indicators)
        """
        passed_indicators = []
        failed_indicators = []
        
        # Analyze each indicator based on direction
        for indicator_name, value in indicators.items():
            result = self._analyze_single_indicator(indicator_name, value, direction)
            if result:
                if result['passed']:
                    passed_indicators.append(result)
                else:
                    failed_indicators.append(result)
        
        return passed_indicators, failed_indicators
    
    def _analyze_single_indicator(self, indicator_name: str, value: Any, direction: str) -> Dict:
        """
        Analyze single indicator for the given direction
        
        Returns:
            Dict with 'passed', 'description', 'actual', 'expected' keys
        """
        if direction not in ['LONG', 'SHORT']:
            return None
        
        # Boolean indicators analysis
        if indicator_name == 'ema_fast_above_slow':
            if direction == 'LONG':
                return {
                    'passed': bool(value),
                    'description': 'EMA Fast > EMA Slow',
                    'actual': 'True' if value else 'False',
                    'expected': 'True untuk LONG'
                }
            else:  # SHORT
                return {
                    'passed': not bool(value),
                    'description': 'EMA Fast < EMA Slow',
                    'actual': 'False' if value else 'True',
                    'expected': 'False untuk SHORT'
                }
        
        elif indicator_name == 'macd_bullish':
            if direction == 'LONG':
                return {
                    'passed': bool(value),
                    'description': 'MACD Bullish Signal',
                    'actual': 'Bullish' if value else 'Bearish',
                    'expected': 'Bullish untuk LONG'
                }
            else:  # SHORT
                return {
                    'passed': not bool(value),
                    'description': 'MACD Bearish Signal',
                    'actual': 'Bearish' if not value else 'Bullish',
                    'expected': 'Bearish untuk SHORT'
                }
        
        elif indicator_name == 'rsi_oversold':
            if direction == 'LONG':
                return {
                    'passed': bool(value),
                    'description': 'RSI Oversold (Buy Signal)',
                    'actual': 'Oversold' if value else 'Not Oversold',
                    'expected': 'Oversold untuk LONG'
                }
            else:  # SHORT
                return {
                    'passed': False,  # Oversold tidak mendukung SHORT
                    'description': 'RSI Oversold (Tidak untuk SHORT)',
                    'actual': 'Oversold' if value else 'Not Oversold',
                    'expected': 'Not Oversold untuk SHORT'
                }
        
        elif indicator_name == 'rsi_overbought':
            if direction == 'LONG':
                return {
                    'passed': False,  # Overbought tidak mendukung LONG
                    'description': 'RSI Overbought (Tidak untuk LONG)',
                    'actual': 'Overbought' if value else 'Not Overbought',
                    'expected': 'Not Overbought untuk LONG'
                }
            else:  # SHORT
                return {
                    'passed': bool(value),
                    'description': 'RSI Overbought (Sell Signal)',
                    'actual': 'Overbought' if value else 'Not Overbought',
                    'expected': 'Overbought untuk SHORT'
                }
        
        elif indicator_name == 'rsi_neutral':
            # RSI neutral bisa mendukung kedua direction tergantung konteks
            return {
                'passed': bool(value),
                'description': 'RSI Neutral Zone',
                'actual': 'Neutral' if value else 'Extreme',
                'expected': 'Neutral untuk stabilitas'
            }
        
        elif indicator_name == 'volume_confirmation':
            return {
                'passed': bool(value),
                'description': 'Volume Confirmation',
                'actual': 'High Volume' if value else 'Low Volume',
                'expected': 'High Volume untuk konfirmasi'
            }
        
        elif indicator_name == 'volatility_confirmation':
            return {
                'passed': bool(value),
                'description': 'Volatility Confirmation',
                'actual': 'High Volatility' if value else 'Low Volatility',
                'expected': 'High Volatility untuk momentum'
            }
        
        elif indicator_name == 'price_near_support':
            if direction == 'LONG':
                return {
                    'passed': bool(value),
                    'description': 'Price Near Support Level',
                    'actual': 'Near Support' if value else 'Away from Support',
                    'expected': 'Near Support untuk LONG'
                }
            else:  # SHORT
                return {
                    'passed': False,  # Near support tidak mendukung SHORT
                    'description': 'Price Near Support (Tidak untuk SHORT)',
                    'actual': 'Near Support' if value else 'Away from Support',
                    'expected': 'Away from Support untuk SHORT'
                }
        
        elif indicator_name == 'price_near_resistance':
            if direction == 'LONG':
                return {
                    'passed': False,  # Near resistance tidak mendukung LONG
                    'description': 'Price Near Resistance (Tidak untuk LONG)',
                    'actual': 'Near Resistance' if value else 'Away from Resistance',
                    'expected': 'Away from Resistance untuk LONG'
                }
            else:  # SHORT
                return {
                    'passed': bool(value),
                    'description': 'Price Near Resistance Level',
                    'actual': 'Near Resistance' if value else 'Away from Resistance',
                    'expected': 'Near Resistance untuk SHORT'
                }
        
        elif indicator_name == 'trend_alignment':
            return {
                'passed': bool(value),
                'description': 'Trend Alignment',
                'actual': 'Aligned' if value else 'Not Aligned',
                'expected': f'Aligned dengan {direction}'
            }
        
        elif indicator_name == 'momentum_confirmation':
            return {
                'passed': bool(value),
                'description': 'Momentum Confirmation',
                'actual': 'Strong Momentum' if value else 'Weak Momentum',
                'expected': f'Strong Momentum untuk {direction}'
            }
        
        # Numerical indicators analysis
        elif indicator_name == 'rsi_level':
            rsi_value = float(value) if value else 50
            if direction == 'LONG':
                # RSI < 40 bagus untuk LONG (oversold)
                passed = rsi_value < 40
                return {
                    'passed': passed,
                    'description': f'RSI Level ({rsi_value:.1f})',
                    'actual': f'{rsi_value:.1f}',
                    'expected': '< 40 untuk LONG entry'
                }
            else:  # SHORT
                # RSI > 60 bagus untuk SHORT (overbought)
                passed = rsi_value > 60
                return {
                    'passed': passed,
                    'description': f'RSI Level ({rsi_value:.1f})',
                    'actual': f'{rsi_value:.1f}',
                    'expected': '> 60 untuk SHORT entry'
                }
        
        elif indicator_name == 'atr_value':
            atr_value = float(value) if value else 0
            # ATR > 0 menunjukkan volatilitas yang cukup
            passed = atr_value > 0
            return {
                'passed': passed,
                'description': f'ATR Value ({atr_value:.6f})',
                'actual': f'{atr_value:.6f}',
                'expected': '> 0 untuk volatilitas'
            }
        
        elif indicator_name == 'ema_fast_value':
            ema_fast = float(value) if value else 0
            return {
                'passed': ema_fast > 0,
                'description': f'EMA Fast ({ema_fast:.6f})',
                'actual': f'{ema_fast:.6f}',
                'expected': '> 0 (valid value)'
            }
        
        elif indicator_name == 'ema_slow_value':
            ema_slow = float(value) if value else 0
            return {
                'passed': ema_slow > 0,
                'description': f'EMA Slow ({ema_slow:.6f})',
                'actual': f'{ema_slow:.6f}',
                'expected': '> 0 (valid value)'
            }
        
        elif indicator_name == 'macd_line_value':
            macd_line = float(value) if value else 0
            if direction == 'LONG':
                # MACD line > 0 bagus untuk LONG
                passed = macd_line > 0
                return {
                    'passed': passed,
                    'description': f'MACD Line ({macd_line:.6f})',
                    'actual': f'{macd_line:.6f}',
                    'expected': '> 0 untuk LONG'
                }
            else:  # SHORT
                # MACD line < 0 bagus untuk SHORT
                passed = macd_line < 0
                return {
                    'passed': passed,
                    'description': f'MACD Line ({macd_line:.6f})',
                    'actual': f'{macd_line:.6f}',
                    'expected': '< 0 untuk SHORT'
                }
        
        elif indicator_name == 'signal_line_value':
            signal_line = float(value) if value else 0
            return {
                'passed': True,  # Signal line selalu valid
                'description': f'Signal Line ({signal_line:.6f})',
                'actual': f'{signal_line:.6f}',
                'expected': 'Valid signal line'
            }
        
        elif indicator_name == 'support_resistance':
            sr_level = float(value) if value else 0
            return {
                'passed': sr_level > 0,
                'description': f'Support/Resistance ({sr_level:.6f})',
                'actual': f'{sr_level:.6f}',
                'expected': '> 0 (valid level)'
            }
        
        elif indicator_name == 'price_distance_from_level':
            distance = float(value) if value else 0
            # Distance yang kecil menunjukkan price dekat dengan level
            passed = abs(distance) < 0.02  # 2% threshold
            return {
                'passed': passed,
                'description': f'Price Distance from Level ({distance:.4f})',
                'actual': f'{distance:.4f}',
                'expected': '< 0.02 (close to level)'
            }
        
        # Unknown indicator
        return {
            'passed': False,
            'description': f'Unknown Indicator ({indicator_name})',
            'actual': str(value),
            'expected': 'Known indicator'
        }

# Global instance
_indicator_analyzer = None

def get_indicator_analyzer():
    """Get global indicator analyzer instance"""
    global _indicator_analyzer
    if _indicator_analyzer is None:
        _indicator_analyzer = IndicatorAnalysisSystem()
    return _indicator_analyzer