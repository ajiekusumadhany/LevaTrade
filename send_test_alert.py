"""
Script untuk test kirim alert ke Telegram
"""
import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

async def send_test():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    # Test message 1: Simple
    message1 = "🤖 <b>Test Alert - Bot Aktif!</b>\n\n✅ Koneksi berhasil!\n📊 Bot siap monitoring market."
    
    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message1,
        parse_mode='HTML'
    )
    print("✅ Test message 1 sent!")
    
    await asyncio.sleep(2)
    
    # Test message 2: Trading alert format
    message2 = """
📈 <b>LONG SETUP - BTCUSDT</b>

💰 <b>Price:</b> $89954.80
🎯 <b>Entry Zone:</b> $89500.00 - $90000.00
🛑 <b>Stop Loss:</b> $88800.00
✅ <b>Take Profit:</b> $92000.00

⚡ <b>Leverage:</b> 5x (NORMAL)
💵 <b>Risk Amount:</b> $20.00
📊 <b>Position Size:</b> 0.125
📉 <b>SL %:</b> 1.28%
🎲 <b>R:R:</b> 1:1.67

⏰ Test Alert - Bot Ready!
"""
    
    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message2,
        parse_mode='HTML'
    )
    print("✅ Test message 2 sent!")
    print(f"\n📱 Cek Telegram Anda (@aurora_qa_bot)")

if __name__ == "__main__":
    asyncio.run(send_test())
