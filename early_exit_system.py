"""
Early Exit System - Sistem keluar dini untuk optimasi profit scalping
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
from telegram import Bot
from telegram.error import TelegramError
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None

class EarlyExitSystem:
    def __init__(self):
        self.exit_rules = {
            # Partial TP rules
            'partial_tp_1': {'percentage': 25, 'profit_atr': 0.3},  # 25% close di 0.3x ATR
            'partial_tp_2': {'percentage': 50, 'profit_atr': 0.6},  # 50% close di 0.6x ATR
            
            # Time-based exit
            'max_duration_minutes': 120,  # 2 jam max untuk scalping
            
            # Momentum exit
            'momentum_exit_enabled': True,
            
            # Trailing stop
            'trailing_stop_enabled': True,
            'trailing_distance_atr': 0.2,  # 0.2x ATR trailing distance
        }
    
    def check_early_exit(self, position: Dict, current_price: float, 
                        current_indicators: Dict) -> List[Dict]:
        """
        Check apakah posisi perlu early exit
        Returns: List of exit actions
        """
        exit_actions = []
        
        entry_price = position['entry_price']
        direction = position['direction']
        atr_value = position.get('atr_value', 0.01)  # Fallback ATR
        entry_time = datetime.fromisoformat(position['entry_time'])
        current_time = datetime.now()
        
        # Calculate current profit in ATR terms
        if direction == "LONG":
            profit_atr = (current_price - entry_price) / atr_value
        else:  # SHORT
            profit_atr = (entry_price - current_price) / atr_value
        
        # 1. PARTIAL TAKE PROFIT
        if profit_atr >= self.exit_rules['partial_tp_1']['profit_atr']:
            if not position.get('partial_tp_1_executed', False):
                exit_actions.append({
                    'type': 'partial_tp',
                    'percentage': self.exit_rules['partial_tp_1']['percentage'],
                    'reason': f"Partial TP 1 - {profit_atr:.2f}x ATR profit",
                    'price': current_price
                })
        
        if profit_atr >= self.exit_rules['partial_tp_2']['profit_atr']:
            if not position.get('partial_tp_2_executed', False):
                exit_actions.append({
                    'type': 'partial_tp',
                    'percentage': self.exit_rules['partial_tp_2']['percentage'],
                    'reason': f"Partial TP 2 - {profit_atr:.2f}x ATR profit",
                    'price': current_price
                })
        
        # 2. TIME-BASED EXIT
        duration_minutes = (current_time - entry_time).total_seconds() / 60
        if duration_minutes > self.exit_rules['max_duration_minutes']:
            exit_actions.append({
                'type': 'full_exit',
                'percentage': 100,
                'reason': f"Time Exit - {duration_minutes:.0f}m duration",
                'price': current_price
            })
        
        # 3. MOMENTUM EXIT
        if self.exit_rules['momentum_exit_enabled']:
            momentum_exit = self._check_momentum_exit(position, current_indicators)
            if momentum_exit:
                exit_actions.append(momentum_exit)
        
        # 4. TRAILING STOP
        if self.exit_rules['trailing_stop_enabled'] and profit_atr > 0:
            trailing_exit = self._check_trailing_stop(position, current_price, atr_value)
            if trailing_exit:
                exit_actions.append(trailing_exit)
        
        return exit_actions
    
    def _check_momentum_exit(self, position: Dict, current_indicators: Dict) -> Dict:
        """Check momentum-based exit conditions"""
        direction = position['direction']
        
        # Get current EMA and MACD
        ema_fast = current_indicators.get('ema_fast', 0)
        ema_slow = current_indicators.get('ema_slow', 0)
        macd_line = current_indicators.get('macd_line', 0)
        signal_line = current_indicators.get('signal_line', 0)
        
        # Check for momentum reversal
        if direction == "LONG":
            # Exit LONG jika EMA cross down atau MACD cross down
            if ema_fast < ema_slow or macd_line < signal_line:
                return {
                    'type': 'full_exit',
                    'percentage': 100,
                    'reason': "Momentum Reversal - Trend changed",
                    'price': current_indicators.get('current_price', 0)
                }
        else:  # SHORT
            # Exit SHORT jika EMA cross up atau MACD cross up
            if ema_fast > ema_slow or macd_line > signal_line:
                return {
                    'type': 'full_exit',
                    'percentage': 100,
                    'reason': "Momentum Reversal - Trend changed",
                    'price': current_indicators.get('current_price', 0)
                }
        
        return None
    
    def _check_trailing_stop(self, position: Dict, current_price: float, atr_value: float) -> Dict:
        """Check trailing stop conditions"""
        direction = position['direction']
        entry_price = position['entry_price']
        trailing_distance = atr_value * self.exit_rules['trailing_distance_atr']
        
        # Get highest/lowest price since entry (would need to track this)
        # For now, simple trailing based on current profit
        
        if direction == "LONG":
            current_profit = current_price - entry_price
            if current_profit > atr_value * 0.5:  # Only trail if profit > 0.5x ATR
                trailing_stop = current_price - trailing_distance
                if position.get('current_sl', 0) < trailing_stop:
                    return {
                        'type': 'update_sl',
                        'new_sl': trailing_stop,
                        'reason': f"Trailing Stop Updated - ${trailing_stop:.4f}",
                        'price': current_price
                    }
        else:  # SHORT
            current_profit = entry_price - current_price
            if current_profit > atr_value * 0.5:  # Only trail if profit > 0.5x ATR
                trailing_stop = current_price + trailing_distance
                if position.get('current_sl', float('inf')) > trailing_stop:
                    return {
                        'type': 'update_sl',
                        'new_sl': trailing_stop,
                        'reason': f"Trailing Stop Updated - ${trailing_stop:.4f}",
                        'price': current_price
                    }
        
        return None
    
    async def send_early_exit_notification(self, position: Dict, exit_action: Dict):
        """Send Telegram notification for early exit"""
        if not telegram_bot or not TELEGRAM_CHAT_ID:
            return
        
        try:
            symbol = position['symbol']
            direction = position['direction']
            entry_price = position['entry_price']
            
            if exit_action['type'] == 'partial_tp':
                emoji = "🎯📈"
                title = f"PARTIAL TAKE PROFIT - {symbol}"
                action_text = f"Closing {exit_action['percentage']}% of position"
            elif exit_action['type'] == 'update_sl':
                emoji = "📈🔄"
                title = f"TRAILING STOP UPDATE - {symbol}"
                action_text = f"SL updated to ${exit_action['new_sl']:.4f}"
            else:  # full_exit
                emoji = "🚪✅"
                title = f"EARLY EXIT - {symbol}"
                action_text = "Closing full position"
            
            message = f"""
{emoji} <b>{title}</b>

🔄 <b>Action:</b> {action_text}
📊 <b>Direction:</b> {direction}
💰 <b>Entry:</b> ${entry_price:.4f}
💎 <b>Current:</b> ${exit_action['price']:.4f}
📝 <b>Reason:</b> {exit_action['reason']}

🤖 <b>Early Exit System</b>
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            await telegram_bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='HTML'
            )
            print(f"📱 Early exit notification sent for {symbol}")
            
        except TelegramError as e:
            print(f"❌ Telegram error in early exit: {e}")
        except Exception as e:
            print(f"❌ Error sending early exit notification: {e}")

# Global instance
early_exit_system = EarlyExitSystem()