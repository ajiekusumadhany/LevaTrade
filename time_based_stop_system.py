"""
Time-Based Stop System
Menutup posisi berdasarkan durasi maksimum per session
"""

import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import asyncio

# WIB = UTC+7
WIB = timezone(timedelta(hours=7))

def now_wib() -> datetime:
    """Waktu sekarang dalam WIB (UTC+7)"""
    return datetime.now(WIB)

class TimeBasedStopSystem:
    def __init__(self):
        # Session-based maximum duration (in minutes) — swing trading
        self.session_max_duration = {
            'DEAD_ZONE': 14400,  # 10 hari
            'ASIA':      10080,  # 7 hari
            'LONDON':    10080,  # 7 hari
            'NEWYORK':   10080   # 7 hari
        }
        
        # Track position entry times
        self.position_entry_times = {}
        
        # Warning thresholds (percentage of max duration)
        self.warning_thresholds = [0.75, 0.90]  # 75% and 90% warnings
        
    def register_position_entry(self, symbol: str, entry_time: datetime, session: str):
        """Register when a position was opened"""
        # Pastikan entry_time aware WIB
        if entry_time.tzinfo is None:
            entry_time = entry_time.replace(tzinfo=WIB)
        self.position_entry_times[symbol] = {
            'entry_time': entry_time,
            'session': session,
            'max_duration_minutes': self.session_max_duration.get(session, 120),
            'warnings_sent': []
        }
        print(f"Time-based stop registered for {symbol}: Max {self.session_max_duration.get(session, 120)}m in {session}")
    
    def check_time_based_exits(self, open_positions: List[Dict]) -> List[Dict]:
        """Check which positions should be closed due to time limits"""
        current_time = now_wib()
        positions_to_close = []
        
        for position in open_positions:
            symbol = position.get('symbol')
            if not symbol:
                continue
                
            # Get position entry info
            entry_info = self.position_entry_times.get(symbol)
            if not entry_info:
                # If no entry time recorded, try to get current session or use default
                try:
                    from session_management_system import get_current_session_parameters
                    current_balance = 1000000  # Default for session check
                    session_params = get_current_session_parameters(current_balance, {}, {})
                    current_session = session_params['session']
                    max_duration = self.session_max_duration.get(current_session, 120)
                except ImportError:
                    # Fallback if session_management_system is not available
                    current_session = 'LONDON'  # Default session
                    max_duration = self.session_max_duration.get(current_session, 120)
                    print(f"session_management_system not available, using default session: {current_session}")
                except Exception as e:
                    print(f"Error getting session for {symbol}: {e}")
                    continue
                
                # Estimate entry time (assume position opened recently)
                estimated_entry = current_time - timedelta(minutes=30)  # Conservative estimate
                entry_info = {
                    'entry_time': estimated_entry,
                    'session': current_session,
                    'max_duration_minutes': max_duration,
                    'warnings_sent': []
                }
                self.position_entry_times[symbol] = entry_info
                print(f"Estimated entry time for {symbol}: {max_duration}m limit in {current_session}")
            
            # Calculate position duration
            entry_time = entry_info['entry_time']
            duration_minutes = (current_time - entry_time).total_seconds() / 60
            max_duration = entry_info['max_duration_minutes']
            duration_percentage = duration_minutes / max_duration
            
            # Check for warnings first
            warnings_sent = entry_info.get('warnings_sent', [])
            for threshold in self.warning_thresholds:
                if duration_percentage >= threshold and threshold not in warnings_sent:
                    # Send async warning notification
                    asyncio.create_task(self._send_time_warning(symbol, duration_minutes, max_duration, threshold, entry_info['session']))
                    warnings_sent.append(threshold)
                    entry_info['warnings_sent'] = warnings_sent
            
            # Check if position should be closed
            if duration_minutes > max_duration:
                positions_to_close.append({
                    'symbol': symbol,
                    'reason': 'TIME_STOP',
                    'duration_minutes': duration_minutes,
                    'max_duration': max_duration,
                    'session': entry_info['session'],
                    'entry_time': entry_time,
                    'position_data': position
                })
                
                print(f"TIME STOP: {symbol} duration {duration_minutes:.1f}m > {max_duration}m limit")
        
        return positions_to_close
    
    def remove_position(self, symbol: str):
        """Remove position from tracking when closed"""
        if symbol in self.position_entry_times:
            del self.position_entry_times[symbol]
            print(f"Removed time tracking for {symbol}")
    
    def get_position_duration(self, symbol: str) -> Optional[float]:
        """Get current duration of a position in minutes"""
        entry_info = self.position_entry_times.get(symbol)
        if not entry_info:
            return None
        current_time = now_wib()
        entry_time = entry_info['entry_time']
        if entry_time.tzinfo is None:
            entry_time = entry_time.replace(tzinfo=WIB)
        duration_minutes = (current_time - entry_time).total_seconds() / 60
        return duration_minutes
    
    def get_time_remaining(self, symbol: str) -> Optional[float]:
        """Get remaining time before time stop in minutes"""
        entry_info = self.position_entry_times.get(symbol)
        if not entry_info:
            return None
            
        duration = self.get_position_duration(symbol)
        if duration is None:
            return None
            
        remaining = entry_info['max_duration_minutes'] - duration
        return max(0, remaining)
    
    async def send_time_stop_notification(self, position_to_close: Dict):
        """Send notification when position is closed due to time limit"""
        try:
            from telegram import Bot
            from telegram.error import TelegramError
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
            TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
            
            if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
                print("Telegram credentials not found for time stop notification")
                return False
            
            symbol = position_to_close['symbol']
            duration = position_to_close['duration_minutes']
            max_duration = position_to_close['max_duration']
            session = position_to_close['session']
            position = position_to_close['position_data']
            
            # Calculate PnL info
            entry_price = position.get('entry_price', 0)
            current_price = position.get('current_price', entry_price)
            unrealized_pnl = position.get('unrealized_pnl', 0)
            direction = position.get('direction', 'UNKNOWN')
            
            pnl_emoji = "💰" if unrealized_pnl >= 0 else "💸"
            direction_emoji = "📈" if direction == "LONG" else "📉"
            
            message = f"""⏰ TIME STOP
⏱️ {symbol} {direction} — {session}
━━━━━━━━━━━━━━━━━━━━━━

{direction_emoji} Durasi: {duration:.0f}m / {max_duration}m
💰 Entry: ${entry_price:.6f}
🎯 Exit:  ${current_price:.6f}
{pnl_emoji} PnL: ${unrealized_pnl:.2f}

⏰ {now_wib().strftime('%d %b %Y  %H:%M:%S')} WIB
<i>LevaTrade · ICT/SMC Engine</i>"""
            
            bot = Bot(token=TELEGRAM_BOT_TOKEN)
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message
            )
            
            print(f"Time stop notification sent for {symbol}")
            return True
            
        except Exception as e:
            print(f"Error sending time stop notification for {symbol}: {e}")
            return False
    
    async def _send_time_warning(self, symbol: str, duration: float, max_duration: int, threshold: float, session: str):
        """Send warning when position approaches time limit"""
        try:
            from telegram import Bot
            from telegram.error import TelegramError
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
            TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
            
            if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
                return False
            
            remaining_minutes = max_duration - duration
            percentage = int(threshold * 100)
            
            warning_emoji = "⚠️" if threshold < 0.9 else "🚨"
            
            message = f"""{warning_emoji} TIME WARNING - {symbol}

⏱️ Duration: {duration:.1f} / {max_duration} minutes ({percentage}%)
⏳ Remaining: {remaining_minutes:.1f} minutes
📅 Session: {session}

💡 Position will be auto-closed when time limit is reached

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            
            bot = Bot(token=TELEGRAM_BOT_TOKEN)
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message
            )
            
            print(f"Time warning sent for {symbol} ({percentage}%)")
            return True
            
        except Exception as e:
            print(f"Error sending time warning for {symbol}: {e}")
            return False

# Global instance
time_based_stop_system = TimeBasedStopSystem()

def register_position_entry(symbol: str, entry_time: datetime, session: str):
    """Register position entry for time-based tracking"""
    time_based_stop_system.register_position_entry(symbol, entry_time, session)

def check_time_based_exits(open_positions: List[Dict]) -> List[Dict]:
    """Check for positions that should be closed due to time limits"""
    return time_based_stop_system.check_time_based_exits(open_positions)

def remove_position_tracking(symbol: str):
    """Remove position from time-based tracking"""
    time_based_stop_system.remove_position(symbol)

def get_position_time_info(symbol: str) -> Dict:
    """Get comprehensive time information for a position"""
    entry_info = time_based_stop_system.position_entry_times.get(symbol)
    if not entry_info:
        return {
            'duration_minutes': None,
            'remaining_minutes': None,
            'has_tracking': False,
            'session': None,
            'max_duration': None,
            'percentage_used': None
        }
    
    duration = time_based_stop_system.get_position_duration(symbol)
    remaining = time_based_stop_system.get_time_remaining(symbol)
    max_duration = entry_info['max_duration_minutes']
    percentage_used = (duration / max_duration * 100) if duration and max_duration else 0
    
    return {
        'duration_minutes': duration,
        'remaining_minutes': remaining,
        'has_tracking': True,
        'session': entry_info['session'],
        'max_duration': max_duration,
        'percentage_used': percentage_used,
        'warnings_sent': entry_info.get('warnings_sent', []),
        'entry_time': entry_info['entry_time']
    }

def get_all_positions_time_info() -> Dict[str, Dict]:
    """Get time information for all tracked positions"""
    result = {}
    for symbol in time_based_stop_system.position_entry_times.keys():
        result[symbol] = get_position_time_info(symbol)
    return result

async def send_time_stop_notification(position_to_close: Dict):
    """Send time stop notification"""
    return await time_based_stop_system.send_time_stop_notification(position_to_close)

if __name__ == "__main__":
    print("Time-based stop system loaded successfully")
    print("Available functions:", [name for name in globals() if callable(globals()[name]) and not name.startswith('_')])