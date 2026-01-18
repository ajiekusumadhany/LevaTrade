"""
Error Notification System - Sistem notifikasi untuk error trading
"""
import asyncio
from datetime import datetime
from typing import Dict, Optional
from telegram import Bot
from telegram.error import TelegramError
import os
from dotenv import load_dotenv
import traceback

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None

class ErrorNotificationSystem:
    def __init__(self):
        self.error_counts = {}  # Track error frequency
        self.last_notification = {}  # Prevent spam
        
    async def notify_trading_error(self, error_type: str, symbol: str, 
                                 error_details: Dict, exception: Optional[Exception] = None):
        """
        Send notification for trading errors
        
        Args:
            error_type: Type of error (balance, order_rejected, api_limit, etc.)
            symbol: Trading symbol where error occurred
            error_details: Dictionary with error details
            exception: Optional exception object
        """
        if not telegram_bot or not TELEGRAM_CHAT_ID:
            print(f"❌ {error_type} error for {symbol}: {error_details}")
            return
        
        # Prevent spam - max 1 notification per error type per 5 minutes
        current_time = datetime.now()
        last_notif_key = f"{error_type}_{symbol}"
        
        if last_notif_key in self.last_notification:
            time_diff = (current_time - self.last_notification[last_notif_key]).total_seconds()
            if time_diff < 300:  # 5 minutes
                return
        
        self.last_notification[last_notif_key] = current_time
        
        # Count errors
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1
        
        try:
            message = self._format_error_message(error_type, symbol, error_details, exception)
            
            await telegram_bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='HTML'
            )
            print(f"📱 Error notification sent: {error_type} for {symbol}")
            
        except TelegramError as e:
            print(f"❌ Failed to send error notification: {e}")
        except Exception as e:
            print(f"❌ Error in error notification system: {e}")
    
    def _format_error_message(self, error_type: str, symbol: str, 
                            error_details: Dict, exception: Optional[Exception]) -> str:
        """Format error message based on error type"""
        
        # Common header
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_count = self.error_counts.get(error_type, 1)
        
        if error_type == "insufficient_balance":
            emoji = "💸❌"
            title = "INSUFFICIENT BALANCE"
            details = f"""
💰 <b>Required:</b> ${error_details.get('required_amount', 0):.2f}
💳 <b>Available:</b> ${error_details.get('available_balance', 0):.2f}
📊 <b>Position Size:</b> {error_details.get('position_size', 0):.3f}
⚡ <b>Leverage:</b> {error_details.get('leverage', 1)}x
"""
        
        elif error_type == "order_rejected":
            emoji = "🚫❌"
            title = "ORDER REJECTED"
            details = f"""
📝 <b>Order Type:</b> {error_details.get('order_type', 'Unknown')}
💰 <b>Price:</b> ${error_details.get('price', 0):.4f}
📊 <b>Quantity:</b> {error_details.get('quantity', 0):.3f}
❌ <b>Reject Reason:</b> {error_details.get('reject_reason', 'Unknown')}
🔢 <b>Error Code:</b> {error_details.get('error_code', 'N/A')}
"""
        
        elif error_type == "api_rate_limit":
            emoji = "⏰❌"
            title = "API RATE LIMIT"
            details = f"""
🔄 <b>Endpoint:</b> {error_details.get('endpoint', 'Unknown')}
⏱️ <b>Retry After:</b> {error_details.get('retry_after', 'Unknown')} seconds
📊 <b>Request Count:</b> {error_details.get('request_count', 'Unknown')}
"""
        
        elif error_type == "network_error":
            emoji = "🌐❌"
            title = "NETWORK ERROR"
            details = f"""
🔗 <b>Connection:</b> {error_details.get('connection_status', 'Failed')}
⏱️ <b>Timeout:</b> {error_details.get('timeout', 'Unknown')}s
🔄 <b>Retry Attempt:</b> {error_details.get('retry_count', 1)}
"""
        
        elif error_type == "invalid_symbol":
            emoji = "🔍❌"
            title = "INVALID SYMBOL"
            details = f"""
📊 <b>Requested Symbol:</b> {symbol}
✅ <b>Available Symbols:</b> Check symbol list
🔄 <b>Action:</b> Symbol removed from scan list
"""
        
        elif error_type == "leverage_error":
            emoji = "⚡❌"
            title = "LEVERAGE ERROR"
            details = f"""
⚡ <b>Requested:</b> {error_details.get('requested_leverage', 'Unknown')}x
✅ <b>Max Allowed:</b> {error_details.get('max_leverage', 'Unknown')}x
💰 <b>Position Value:</b> ${error_details.get('position_value', 0):.2f}
"""
        
        elif error_type == "position_limit":
            emoji = "📊❌"
            title = "POSITION LIMIT REACHED"
            details = f"""
📊 <b>Current Positions:</b> {error_details.get('current_positions', 0)}
🔢 <b>Max Allowed:</b> {error_details.get('max_positions', 0)}
💰 <b>Total Exposure:</b> ${error_details.get('total_exposure', 0):.2f}
"""
        
        else:
            emoji = "⚠️❌"
            title = f"TRADING ERROR - {error_type.upper()}"
            details = f"""
📝 <b>Details:</b> {str(error_details)}
"""
        
        # Add exception details if available
        exception_text = ""
        if exception:
            exception_text = f"""
🐛 <b>Exception:</b> {type(exception).__name__}
📝 <b>Message:</b> {str(exception)}
"""
        
        message = f"""
{emoji} <b>{title}</b>

🎯 <b>Symbol:</b> {symbol}
{details}{exception_text}
🔢 <b>Error Count:</b> {error_count} (last 24h)
⏰ <b>Time:</b> {timestamp}

🤖 <b>Auto Trading Bot</b>
"""
        
        return message
    
    async def notify_system_status(self, status_type: str, details: Dict):
        """Send system status notifications"""
        if not telegram_bot or not TELEGRAM_CHAT_ID:
            return
        
        try:
            if status_type == "bot_started":
                emoji = "🚀✅"
                title = "BOT STARTED"
                message = f"""
{emoji} <b>{title}</b>

📊 <b>Mode:</b> {details.get('mode', 'Unknown')}
🎯 <b>Symbols:</b> {details.get('symbol_count', 0)}
⏰ <b>Timeframe:</b> {details.get('timeframe', 'Unknown')}
🔄 <b>Scan Interval:</b> {details.get('scan_interval', 'Unknown')}
💰 <b>Balance:</b> ${details.get('balance', 0):.2f}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            elif status_type == "bot_stopped":
                emoji = "🛑❌"
                title = "BOT STOPPED"
                message = f"""
{emoji} <b>{title}</b>

📊 <b>Reason:</b> {details.get('reason', 'Manual stop')}
⏱️ <b>Runtime:</b> {details.get('runtime', 'Unknown')}
📈 <b>Total Trades:</b> {details.get('total_trades', 0)}
💰 <b>Final PnL:</b> ${details.get('final_pnl', 0):.2f}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            else:
                return
            
            await telegram_bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='HTML'
            )
            print(f"📱 System status notification sent: {status_type}")
            
        except Exception as e:
            print(f"❌ Error sending system status: {e}")
    
    def get_error_summary(self) -> Dict:
        """Get summary of all errors"""
        return {
            'error_counts': self.error_counts.copy(),
            'total_errors': sum(self.error_counts.values()),
            'last_notifications': self.last_notification.copy()
        }

# Global instance
error_notifier = ErrorNotificationSystem()

# Convenience functions for common errors
async def notify_insufficient_balance(symbol: str, required: float, available: float, 
                                    position_size: float, leverage: int):
    """Quick function for balance errors"""
    await error_notifier.notify_trading_error(
        "insufficient_balance", 
        symbol,
        {
            'required_amount': required,
            'available_balance': available,
            'position_size': position_size,
            'leverage': leverage
        }
    )

async def notify_order_rejected(symbol: str, order_type: str, price: float, 
                              quantity: float, reject_reason: str, error_code: str = ""):
    """Quick function for order rejection errors"""
    await error_notifier.notify_trading_error(
        "order_rejected",
        symbol,
        {
            'order_type': order_type,
            'price': price,
            'quantity': quantity,
            'reject_reason': reject_reason,
            'error_code': error_code
        }
    )

async def notify_api_rate_limit(endpoint: str, retry_after: int = 0, request_count: int = 0):
    """Quick function for API rate limit errors"""
    await error_notifier.notify_trading_error(
        "api_rate_limit",
        "API",
        {
            'endpoint': endpoint,
            'retry_after': retry_after,
            'request_count': request_count
        }
    )