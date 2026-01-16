"""
Script untuk test Telegram Bot
Jalankan ini untuk mendapatkan Chat ID Anda
"""
import os
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

print("🤖 Testing Telegram Bot...")
print(f"Bot Token: {TELEGRAM_BOT_TOKEN[:20] if TELEGRAM_BOT_TOKEN else 'NOT SET'}...")
print(f"Chat ID: {TELEGRAM_CHAT_ID}")
print("-" * 50)

async def test_telegram():
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        # Get bot info
        bot_info = await bot.get_me()
        print(f"✅ Bot Info:")
        print(f"   Username: @{bot_info.username}")
        print(f"   Name: {bot_info.first_name}")
        print(f"   ID: {bot_info.id}")
        print()
        
        # Get updates to find chat ID
        print("📨 Mencari Chat ID dari pesan terakhir...")
        updates = await bot.get_updates()
        
        if updates:
            print(f"✅ Ditemukan {len(updates)} pesan:")
            for update in updates[-5:]:  # Show last 5
                if update.message:
                    chat = update.message.chat
                    print(f"   Chat ID: {chat.id} | Name: {chat.first_name or chat.title}")
            
            # Use the last chat ID
            last_chat_id = updates[-1].message.chat.id
            print(f"\n💡 Chat ID terakhir: {last_chat_id}")
            print(f"   Tambahkan ini ke .env: TELEGRAM_CHAT_ID={last_chat_id}")
        else:
            print("⚠️  Tidak ada pesan ditemukan.")
            print("   Kirim pesan ke bot Anda dulu, lalu jalankan script ini lagi.")
            return
        
        # Send test message if chat ID is set
        if TELEGRAM_CHAT_ID and TELEGRAM_CHAT_ID != 'your_telegram_chat_id_here':
            print(f"\n📤 Mengirim test message ke {TELEGRAM_CHAT_ID}...")
            
            test_message = """
🤖 <b>Test Alert - Crypto Bot</b>

✅ Bot berhasil terhubung!
📊 Monitoring aktif untuk signal trading.

⏰ Test dilakukan pada: """ + asyncio.get_event_loop().time().__str__()
            
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=test_message,
                parse_mode='HTML'
            )
            print("✅ Test message berhasil dikirim!")
        
    except TelegramError as e:
        print(f"❌ Telegram Error: {e}")
        if "Unauthorized" in str(e):
            print("   Token tidak valid. Cek TELEGRAM_BOT_TOKEN di .env")
        elif "Chat not found" in str(e):
            print("   Chat ID tidak valid. Kirim pesan ke bot dulu.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == 'your_telegram_bot_token_here':
        print("❌ TELEGRAM_BOT_TOKEN belum diset di .env")
        print("\n📝 Cara mendapatkan token:")
        print("   1. Buka @BotFather di Telegram")
        print("   2. Kirim /newbot")
        print("   3. Ikuti instruksi")
        print("   4. Copy token yang diberikan ke .env")
    else:
        asyncio.run(test_telegram())
    
    print("-" * 50)
    print("✅ Test selesai!")
