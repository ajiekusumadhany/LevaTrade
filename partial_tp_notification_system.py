#!/usr/bin/env python3
"""
Partial TP Notification System
Handle notifications for partial take profit events
"""
import asyncio
from datetime import datetime
from typing import Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class PartialTPNotificationSystem:
    def __init__(self):
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
        
    async def notify_partial_tp_telegram(self, position_info: Dict, partial_percentage: int, profit_amount: float, profit_atr: float):
        """Send partial TP notification to Telegram"""
        try:
            if not self.telegram_bot_token or not self.telegram_chat_id:
                print("⚠️ Telegram credentials not configured for partial TP notification")
                return False
            
            from telegram import Bot
            
            bot = Bot(token=self.telegram_bot_token)
            
            symbol = position_info.get('symbol', 'UNKNOWN')
            direction = position_info.get('direction', 'UNKNOWN')
            entry_price = position_info.get('entry_price', 0)
            current_price = position_info.get('current_price', 0)
            remaining_percentage = 100 - partial_percentage
            
            # Calculate profit percentage
            if direction == 'LONG':
                profit_pct = ((current_price - entry_price) / entry_price) * 100
            else:
                profit_pct = ((entry_price - current_price) / entry_price) * 100
            
            message = f"""🎯 <b>PARTIAL TAKE PROFIT</b>
            
💰 <b>Position:</b> {symbol} {direction}
📊 <b>Closed:</b> {partial_percentage}% of position
💵 <b>Profit:</b> ${profit_amount:.2f} ({profit_pct:.1f}%)
📈 <b>ATR Profit:</b> {profit_atr:.2f}x ATR

📍 <b>Entry:</b> ${entry_price:.6f}
📍 <b>Current:</b> ${current_price:.6f}
📊 <b>Remaining:</b> {remaining_percentage}% position

⏰ <b>Time:</b> {datetime.now().strftime('%H:%M:%S WIB')}
🎯 <b>Strategy:</b> 1:1 Risk/Reward Partial TP"""
            
            await bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message,
                parse_mode='HTML'
            )
            
            print(f"✅ Partial TP notification sent to Telegram for {symbol}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending partial TP Telegram notification: {e}")
            return False
    
    def notify_partial_tp_dashboard(self, position_info: Dict, partial_percentage: int, profit_amount: float):
        """Add partial TP notification to dashboard notifications"""
        try:
            import json
            
            # Read existing notifications
            notifications_file = 'notifications.json'
            notifications = []
            
            try:
                with open(notifications_file, 'r') as f:
                    notifications = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                notifications = []
            
            # Create partial TP notification
            notification = {
                'id': f"partial_tp_{position_info.get('symbol', 'unknown')}_{datetime.now().timestamp()}",
                'type': 'partial_tp',
                'title': f"Partial TP: {position_info.get('symbol', 'UNKNOWN')}",
                'message': f"Closed {partial_percentage}% of {position_info.get('direction', 'UNKNOWN')} position for ${profit_amount:.2f} profit",
                'timestamp': datetime.now().isoformat(),
                'symbol': position_info.get('symbol', 'UNKNOWN'),
                'direction': position_info.get('direction', 'UNKNOWN'),
                'percentage_closed': partial_percentage,
                'profit_amount': profit_amount,
                'entry_price': position_info.get('entry_price', 0),
                'exit_price': position_info.get('current_price', 0),
                'status': 'success',
                'priority': 'medium'
            }
            
            # Add to notifications list
            notifications.append(notification)
            
            # Keep only last 100 notifications
            notifications = notifications[-100:]
            
            # Save back to file
            with open(notifications_file, 'w') as f:
                json.dump(notifications, f, indent=2)
            
            print(f"✅ Partial TP notification added to dashboard for {position_info.get('symbol', 'UNKNOWN')}")
            return True
            
        except Exception as e:
            print(f"❌ Error adding partial TP dashboard notification: {e}")
            return False
    
    async def notify_time_based_exit_telegram(self, position_info: Dict, hours_held: float, exit_reason: str):
        """Send time-based exit notification to Telegram"""
        try:
            if not self.telegram_bot_token or not self.telegram_chat_id:
                return False
            
            from telegram import Bot
            
            bot = Bot(token=self.telegram_bot_token)
            
            symbol = position_info.get('symbol', 'UNKNOWN')
            direction = position_info.get('direction', 'UNKNOWN')
            entry_price = position_info.get('entry_price', 0)
            current_price = position_info.get('current_price', 0)
            
            # Calculate final P&L
            if direction == 'LONG':
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
            else:
                pnl_pct = ((entry_price - current_price) / entry_price) * 100
            
            pnl_emoji = "💚" if pnl_pct >= 0 else "❤️"
            
            message = f"""⏰ <b>TIME-BASED EXIT</b>
            
📊 <b>Position:</b> {symbol} {direction}
⏱️ <b>Held:</b> {hours_held:.1f} hours
🚪 <b>Reason:</b> {exit_reason}

📍 <b>Entry:</b> ${entry_price:.6f}
📍 <b>Exit:</b> ${current_price:.6f}
{pnl_emoji} <b>P&L:</b> {pnl_pct:.1f}%

⏰ <b>Time:</b> {datetime.now().strftime('%H:%M:%S WIB')}
🎯 <b>Strategy:</b> London 4-Hour Max Hold"""
            
            await bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message,
                parse_mode='HTML'
            )
            
            print(f"✅ Time-based exit notification sent to Telegram for {symbol}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending time-based exit Telegram notification: {e}")
            return False
    
    def notify_time_based_exit_dashboard(self, position_info: Dict, hours_held: float, exit_reason: str):
        """Add time-based exit notification to dashboard"""
        try:
            import json
            
            notifications_file = 'notifications.json'
            notifications = []
            
            try:
                with open(notifications_file, 'r') as f:
                    notifications = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                notifications = []
            
            notification = {
                'id': f"time_exit_{position_info.get('symbol', 'unknown')}_{datetime.now().timestamp()}",
                'type': 'time_based_exit',
                'title': f"Time Exit: {position_info.get('symbol', 'UNKNOWN')}",
                'message': f"Position closed after {hours_held:.1f} hours - {exit_reason}",
                'timestamp': datetime.now().isoformat(),
                'symbol': position_info.get('symbol', 'UNKNOWN'),
                'direction': position_info.get('direction', 'UNKNOWN'),
                'hours_held': hours_held,
                'exit_reason': exit_reason,
                'entry_price': position_info.get('entry_price', 0),
                'exit_price': position_info.get('current_price', 0),
                'status': 'info',
                'priority': 'medium'
            }
            
            notifications.append(notification)
            notifications = notifications[-100:]
            
            with open(notifications_file, 'w') as f:
                json.dump(notifications, f, indent=2)
            
            print(f"✅ Time-based exit notification added to dashboard for {position_info.get('symbol', 'UNKNOWN')}")
            return True
            
        except Exception as e:
            print(f"❌ Error adding time-based exit dashboard notification: {e}")
            return False

# Global instance
partial_tp_notifier = PartialTPNotificationSystem()

def get_partial_tp_notifier():
    """Get partial TP notification system instance"""
    return partial_tp_notifier

async def notify_partial_tp(position_info: Dict, partial_percentage: int, profit_amount: float, profit_atr: float):
    """Unified function to send partial TP notifications to both Telegram and dashboard"""
    notifier = get_partial_tp_notifier()
    
    # Send to both Telegram and dashboard
    telegram_success = await notifier.notify_partial_tp_telegram(position_info, partial_percentage, profit_amount, profit_atr)
    dashboard_success = notifier.notify_partial_tp_dashboard(position_info, partial_percentage, profit_amount)
    
    return telegram_success or dashboard_success

async def notify_time_based_exit(position_info: Dict, hours_held: float, exit_reason: str):
    """Unified function to send time-based exit notifications"""
    notifier = get_partial_tp_notifier()
    
    telegram_success = await notifier.notify_time_based_exit_telegram(position_info, hours_held, exit_reason)
    dashboard_success = notifier.notify_time_based_exit_dashboard(position_info, hours_held, exit_reason)
    
    return telegram_success or dashboard_success

if __name__ == "__main__":
    print("Partial TP Notification System Loaded")
    
    # Test notification
    test_position = {
        'symbol': 'BTCUSDT',
        'direction': 'LONG',
        'entry_price': 45000.0,
        'current_price': 46000.0
    }
    
    # Test would require async context
    print("   ✅ System ready for partial TP notifications")
    print("   📱 Telegram notifications enabled")
    print("   📊 Dashboard notifications enabled")