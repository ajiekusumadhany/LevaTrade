#!/usr/bin/env python3
"""
Test enhanced AI system with trading history and technical analysis
"""
import asyncio
from gemini_ai_system import get_gemini_analyst

async def test_enhanced_ai():
    """Test enhanced AI capabilities"""
    print("🧪 Testing Enhanced AI System...")
    
    try:
        analyst = get_gemini_analyst()
        if not analyst:
            print("❌ Failed to initialize Gemini analyst")
            return
        
        # Test 1: Trading history access
        print("\n📊 Test 1: Trading History Access")
        response = await analyst.chat_with_market_data(
            "Bagaimana riwayat trading saya? Berapa win rate saya?",
            trading_mode="dry_run"
        )
        print(f"Response: {response[:200]}...")
        
        # Test 2: Technical analysis
        print("\n📈 Test 2: Technical Analysis")
        response = await analyst.chat_with_market_data(
            "Analisis teknikal BTCUSDT saat ini",
            trading_mode="dry_run"
        )
        print(f"Response: {response[:200]}...")
        
        # Test 3: Specific symbol analysis
        print("\n🔍 Test 3: Specific Symbol Analysis")
        response = await analyst.chat_with_market_data(
            "Berikan analisis lengkap untuk ETHUSDT termasuk riwayat trading dan kondisi teknikal",
            trading_mode="dry_run"
        )
        print(f"Response: {response[:200]}...")
        
        # Test 4: Market overview
        print("\n🌍 Test 4: Market Overview")
        response = await analyst.chat_with_market_data(
            "Bagaimana kondisi pasar crypto saat ini?",
            trading_mode="dry_run"
        )
        print(f"Response: {response[:200]}...")
        
        print("\n✅ Enhanced AI system tests completed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_ai())