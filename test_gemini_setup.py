#!/usr/bin/env python3
"""
Test script to verify Gemini AI setup and API key rotation
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_gemini_setup():
    """Test Gemini AI setup with API key rotation"""
    print("🧪 Testing Gemini AI Setup...")
    print("=" * 50)
    
    try:
        # Check environment variables
        api_keys_str = os.getenv('GEMINI_API_KEYS', '')
        if not api_keys_str:
            print("❌ GEMINI_API_KEYS not found in .env file")
            print("💡 Please add your Gemini API keys to .env file:")
            print("   GEMINI_API_KEYS=your_key_1,your_key_2,your_key_3")
            return False
        
        # Parse API keys
        api_keys = [key.strip() for key in api_keys_str.split(',') if key.strip()]
        print(f"✅ Found {len(api_keys)} API key(s) in configuration")
        
        # Check if keys look valid (basic format check)
        valid_keys = []
        for i, key in enumerate(api_keys):
            if key.startswith('AIzaSy') and len(key) >= 35:
                valid_keys.append(key)
                print(f"   Key {i+1}: {key[:10]}...{key[-4:]} ✅")
            else:
                print(f"   Key {i+1}: {key[:10]}... ❌ (Invalid format)")
        
        if not valid_keys:
            print("❌ No valid API keys found")
            print("💡 Gemini API keys should start with 'AIzaSy' and be ~39 characters long")
            return False
        
        print(f"✅ {len(valid_keys)} valid API key(s) found")
        
        # Test Gemini AI initialization
        print("\n🤖 Testing Gemini AI initialization...")
        from gemini_ai_system import get_gemini_analyst
        
        analyst = get_gemini_analyst()
        if not analyst:
            print("❌ Failed to initialize Gemini AI analyst")
            return False
        
        print("✅ Gemini AI analyst initialized successfully")
        
        # Test basic chat functionality
        print("\n💬 Testing basic chat functionality...")
        test_message = "Hello! This is a test message. Please respond with 'Test successful' if you can read this."
        
        response = await analyst.chat_with_market_data(test_message, trading_mode="dry_run")
        
        if response and len(response) > 10:
            print("✅ Chat test successful!")
            print(f"   Response: {response[:100]}...")
        else:
            print("❌ Chat test failed - no response or very short response")
            print(f"   Response: {response}")
            return False
        
        # Test API key rotation (if multiple keys)
        if len(valid_keys) > 1:
            print(f"\n🔄 Testing API key rotation with {len(valid_keys)} keys...")
            
            for i in range(min(3, len(valid_keys))):  # Test up to 3 rotations
                test_msg = f"Test message #{i+1} for key rotation testing."
                response = await analyst.chat_with_market_data(test_msg, trading_mode="dry_run")
                
                if response and len(response) > 10:
                    print(f"   Rotation {i+1}: ✅")
                else:
                    print(f"   Rotation {i+1}: ❌")
                    return False
            
            print("✅ API key rotation working correctly")
        else:
            print("\n⚠️  Only 1 API key configured - rotation not available")
            print("💡 Add more keys for better rate limit handling:")
            print("   GEMINI_API_KEYS=key1,key2,key3")
        
        # Test market analysis
        print("\n📊 Testing market analysis...")
        analysis = await analyst.analyze_market_conditions(['BTCUSDT', 'ETHUSDT'])
        
        if analysis and len(analysis) > 50:
            print("✅ Market analysis test successful!")
            print(f"   Analysis: {analysis[:100]}...")
        else:
            print("❌ Market analysis test failed")
            print(f"   Analysis: {analysis}")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! Gemini AI is ready to use.")
        print("\n📋 Configuration Summary:")
        print(f"   • API Keys: {len(valid_keys)} configured")
        print(f"   • Model: {analyst.model_name}")
        print(f"   • Temperature: {analyst.temperature}")
        print(f"   • Max Tokens: {analyst.max_tokens}")
        print(f"   • Rotation: {'Enabled' if len(valid_keys) > 1 else 'Disabled (single key)'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check your .env file has GEMINI_API_KEYS")
        print("2. Verify API keys are valid and active")
        print("3. Check internet connection")
        print("4. Ensure google-generativeai package is installed")
        return False

async def test_rate_limit_handling():
    """Test rate limit handling with rapid requests"""
    print("\n🚀 Testing rate limit handling...")
    
    try:
        from gemini_ai_system import get_gemini_analyst
        analyst = get_gemini_analyst()
        
        if not analyst or len(analyst.api_keys) < 2:
            print("⚠️  Skipping rate limit test - need multiple API keys")
            return
        
        print(f"   Making 5 rapid requests to test rotation...")
        
        for i in range(5):
            response = await analyst.chat_with_market_data(
                f"Quick test #{i+1}", 
                trading_mode="dry_run"
            )
            
            if response:
                print(f"   Request {i+1}: ✅ ({len(response)} chars)")
            else:
                print(f"   Request {i+1}: ❌")
            
            # Small delay between requests
            await asyncio.sleep(0.5)
        
        print("✅ Rate limit handling test completed")
        
    except Exception as e:
        print(f"❌ Rate limit test failed: {e}")

if __name__ == "__main__":
    print("🚀 Gemini AI Setup Test")
    print("This script will test your Gemini AI configuration")
    print()
    
    # Run main test
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    success = loop.run_until_complete(test_gemini_setup())
    
    if success:
        # Run additional tests
        loop.run_until_complete(test_rate_limit_handling())
        
        print("\n✅ Setup complete! You can now use Gemini AI features:")
        print("   • Entry/Exit reasoning for trades")
        print("   • Interactive dashboard chat")
        print("   • Market analysis and insights")
        print("   • Performance analytics")
    else:
        print("\n❌ Setup incomplete. Please fix the issues above.")
        print("\n📖 For help, see: GEMINI_AI_SETUP.md")
    
    loop.close()