#!/usr/bin/env python3
"""
Test AI Reasoning Telegram Notifications
"""
import asyncio
from crypto_bot_parallel import send_ai_entry_reasoning_telegram, send_ai_exit_reasoning_telegram

async def test_ai_telegram_notifications():
    """Test AI reasoning notifications to Telegram"""
    print("🧪 Testing AI Reasoning Telegram Notifications...")
    
    # Test Entry Reasoning
    print("\n📤 Testing AI Entry Reasoning Notification...")
    
    sample_entry_reasoning = """
<b>Alasan Entry:</b><br>
Entry LONG pada harga $95000.50 menunjukkan potensi kenaikan berdasarkan konfirmasi teknikal.<br><br>

<b>Analisis Teknikal:</b><br>
EMA Fast berada di atas EMA Slow mengkonfirmasi tren bullish. RSI di zona netral (42.5) memberikan ruang untuk pergerakan naik. MACD bullish menunjukkan momentum positif.<br><br>

<b>Konteks Pasar:</b><br>
Volume di atas rata-rata dan volatilitas memadai mendukung pergerakan harga. Harga mendekati level support memberikan entry yang strategis.<br><br>

<b>Penilaian Risiko:</b><br>
Stop Loss di $94200 membatasi risiko. Leverage 5x meningkatkan potensi profit namun juga risiko.<br><br>

<b>Ekspektasi Hasil:</b><br>
Target TP $95800 dengan R:R ratio 1:1.33. Timeline estimasi beberapa jam hingga hari.
"""
    
    try:
        success = await send_ai_entry_reasoning_telegram("BTCUSDT", "LONG", sample_entry_reasoning)
        if success:
            print("✅ AI Entry Reasoning notification sent successfully!")
        else:
            print("❌ Failed to send AI Entry Reasoning notification")
    except Exception as e:
        print(f"❌ Error testing entry reasoning: {e}")
    
    # Wait a bit between messages
    await asyncio.sleep(2)
    
    # Test Exit Reasoning
    print("\n📤 Testing AI Exit Reasoning Notification...")
    
    sample_exit_reasoning = """
<b>Apa yang Terjadi:</b><br>
Posisi LONG BTCUSDT dibuka pada $95000.50 dan ditutup pada $95750.25 setelah 27 menit trading. Harga bergerak sesuai ekspektasi mencapai target profit.<br><br>

<b>Analisis Exit:</b><br>
Posisi ditutup karena TP_HIT yang menunjukkan target profit tercapai. Strategi exit yang disiplin mengunci keuntungan sesuai rencana.<br><br>

<b>Faktor Pasar:</b><br>
Momentum bullish dari EMA dan MACD terkonfirmasi dengan pergerakan harga naik. Volume mendukung breakout ke level target.<br><br>

<b>Review Performa:</b><br>
Trade sukses dengan profit $78.75 (1.65%) dalam waktu singkat. Eksekusi sesuai analisis teknikal awal.<br><br>

<b>Pelajaran Penting:</b><br>
Disiplin mengikuti TP sangat penting. Analisis teknikal yang tepat memberikan hasil positif.
"""
    
    try:
        success = await send_ai_exit_reasoning_telegram(
            "BTCUSDT", "LONG", "TP_HIT", 78.75, sample_exit_reasoning,
            95000.50, 95750.25, 27
        )
        if success:
            print("✅ AI Exit Reasoning notification sent successfully!")
        else:
            print("❌ Failed to send AI Exit Reasoning notification")
    except Exception as e:
        print(f"❌ Error testing exit reasoning: {e}")
    
    print("\n🎉 AI Telegram Notifications test completed!")
    print("📱 Check your Telegram for the AI reasoning messages")

if __name__ == "__main__":
    asyncio.run(test_ai_telegram_notifications())