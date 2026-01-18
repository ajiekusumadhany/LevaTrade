#!/usr/bin/env python3
"""
Test Error Notification System
"""
import asyncio
from error_notification_system import error_notifier

async def test_all_error_types():
    """Test all error notification types"""
    print("🧪 Testing Error Notification System...")
    
    # Test 1: Insufficient Balance
    print("\n1. Testing insufficient balance notification...")
    await error_notifier.notify_trading_error(
        "insufficient_balance",
        "BTCUSDT",
        {
            'required_amount': 150.0,
            'available_balance': 100.0,
            'position_size': 0.005,
            'leverage': 10
        }
    )
    
    # Test 2: Order Rejected
    print("2. Testing order rejected notification...")
    await error_notifier.notify_trading_error(
        "order_rejected",
        "ETHUSDT",
        {
            'order_type': 'Market',
            'price': 2500.0,
            'quantity': 0.1,
            'reject_reason': 'Insufficient margin',
            'error_code': '110001'
        }
    )
    
    # Test 3: API Rate Limit
    print("3. Testing API rate limit notification...")
    await error_notifier.notify_trading_error(
        "api_rate_limit",
        "API",
        {
            'endpoint': '/v5/order/create',
            'retry_after': 60,
            'request_count': 120
        }
    )
    
    # Test 4: Position Limit
    print("4. Testing position limit notification...")
    await error_notifier.notify_trading_error(
        "position_limit",
        "ADAUSDT",
        {
            'current_positions': 10,
            'max_positions': 10,
            'total_exposure': 5000.0
        }
    )
    
    # Test 5: System Status - Bot Started
    print("5. Testing bot started notification...")
    await error_notifier.notify_system_status("bot_started", {
        'mode': 'DRY RUN',
        'symbol_count': 100,
        'timeframe': '15m',
        'scan_interval': '3m 0s',
        'balance': 1000.0
    })
    
    # Test 6: System Status - Bot Stopped
    print("6. Testing bot stopped notification...")
    await error_notifier.notify_system_status("bot_stopped", {
        'reason': 'Manual stop',
        'runtime': '2h 30m',
        'total_trades': 15,
        'final_pnl': 45.67
    })
    
    print("\n✅ All error notification tests completed!")
    print("📱 Check your Telegram for notifications")
    
    # Show error summary
    summary = error_notifier.get_error_summary()
    print(f"\n📊 Error Summary:")
    print(f"   Total Errors: {summary['total_errors']}")
    print(f"   Error Types: {list(summary['error_counts'].keys())}")

if __name__ == "__main__":
    asyncio.run(test_all_error_types())