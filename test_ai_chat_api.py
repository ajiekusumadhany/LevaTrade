#!/usr/bin/env python3
"""
Test AI Chat API endpoint
"""
import requests
import json

def test_ai_chat_api():
    """Test the AI chat API endpoint"""
    print("🧪 Testing AI Chat API...")
    
    try:
        # Test data
        test_data = {
            "message": "Hello, this is a test message",
            "mode": "dry_run",
            "context": {}
        }
        
        # Send request to AI chat endpoint
        response = requests.post(
            'http://127.0.0.1:5000/api/ai/chat',
            json=test_data,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Response received")
            print(f"Success: {data.get('success')}")
            
            if data.get('success'):
                print(f"AI Response: {data.get('ai_response', 'No response')[:100]}...")
                print("✅ AI Chat API is working!")
            else:
                print(f"❌ API Error: {data.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - Dashboard not running?")
        print("💡 Start dashboard with: python dashboard_app.py")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_ai_chat_api()