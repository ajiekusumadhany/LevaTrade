#!/usr/bin/env python3
"""
Dashboard AI Chat Integration
- Mode-aware AI chat (dry run vs real trading)
- Real-time market data access
- Trading system integration
"""
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import asyncio
import json
from datetime import datetime
from gemini_ai_system import get_gemini_analyst
from dry_run_system import dry_run_system
from real_trade_system import real_trade_system

class DashboardAIChat:
    def __init__(self, socketio):
        self.socketio = socketio
        self.gemini_analyst = get_gemini_analyst()
        
    async def handle_chat_message(self, data):
        """Handle incoming chat messages from dashboard"""
        try:
            user_message = data.get('message', '')
            trading_mode = data.get('mode', 'dry_run')  # 'dry_run' or 'real_trading'
            context = data.get('context', {})
            
            if not user_message.strip():
                return {
                    'success': False,
                    'error': 'Empty message'
                }
            
            # Check if Gemini AI is available
            if not self.gemini_analyst:
                return {
                    'success': False,
                    'error': 'Gemini AI not available. Please check API key configuration.'
                }
            
            # Generate AI response
            ai_response = await self.gemini_analyst.chat_with_market_data(
                user_message, 
                context, 
                trading_mode
            )
            
            # Prepare response data
            response_data = {
                'success': True,
                'user_message': user_message,
                'ai_response': ai_response,
                'trading_mode': trading_mode,
                'timestamp': datetime.now().isoformat(),
                'context': context
            }
            
            return response_data
            
        except Exception as e:
            print(f"❌ Error in AI chat: {e}")
            return {
                'success': False,
                'error': f'AI chat error: {str(e)}'
            }
    
    async def get_quick_insights(self, trading_mode: str = 'dry_run'):
        """Get quick AI insights for dashboard"""
        try:
            if not self.gemini_analyst:
                return "Gemini AI not available"
            
            # Generate quick market analysis
            insights = await self.gemini_analyst.analyze_market_conditions()
            
            # Add mode-specific performance summary
            if trading_mode == 'dry_run':
                positions = dry_run_system.get_open_positions()
                closed_positions = dry_run_system.get_closed_positions()
            else:
                positions = real_trade_system.get_open_positions()
                closed_positions = real_trade_system.get_closed_positions()
            
            mode_name = "Simulation" if trading_mode == 'dry_run' else "Real Trading"
            
            summary = f"""
            **{mode_name} Quick Insights:**
            
            {insights}
            
            **Current Status:**
            - Open Positions: {len(positions)}
            - Total Trades: {len(closed_positions)}
            """
            
            return summary
            
        except Exception as e:
            return f"Quick insights error: {str(e)}"
    
    async def analyze_position(self, symbol: str, trading_mode: str = 'dry_run'):
        """Get AI analysis for specific position"""
        try:
            if not self.gemini_analyst:
                return "Gemini AI not available"
            
            # Find position in the specified mode
            if trading_mode == 'dry_run':
                positions = dry_run_system.get_open_positions()
            else:
                positions = real_trade_system.get_open_positions()
            
            position = next((p for p in positions if p['symbol'] == symbol), None)
            
            if not position:
                return f"No open position found for {symbol} in {trading_mode.replace('_', ' ')}"
            
            # Generate position analysis
            question = f"Analyze my current {symbol} position. What's the market outlook and should I hold or consider exiting?"
            
            analysis = await self.gemini_analyst.chat_with_market_data(
                question,
                {'symbol': symbol},
                trading_mode
            )
            
            return analysis
            
        except Exception as e:
            return f"Position analysis error: {str(e)}"

# Flask routes for AI chat
def setup_ai_chat_routes(app, socketio):
    """Setup AI chat routes for Flask app"""
    
    ai_chat = DashboardAIChat(socketio)
    
    @app.route('/api/ai/chat', methods=['POST'])
    def ai_chat_endpoint():
        """AI chat endpoint"""
        try:
            data = request.get_json()
            
            # Run async function in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(ai_chat.handle_chat_message(data))
            loop.close()
            
            return jsonify(response)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/ai/insights/<mode>')
    def ai_insights_endpoint(mode):
        """Quick insights endpoint"""
        try:
            # Validate mode
            if mode not in ['dry_run', 'real_trading']:
                return jsonify({
                    'success': False,
                    'error': 'Invalid trading mode'
                }), 400
            
            # Run async function in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            insights = loop.run_until_complete(ai_chat.get_quick_insights(mode))
            loop.close()
            
            return jsonify({
                'success': True,
                'insights': insights,
                'mode': mode,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/ai/analyze/<mode>/<symbol>')
    def ai_analyze_position_endpoint(mode, symbol):
        """Position analysis endpoint"""
        try:
            # Validate mode
            if mode not in ['dry_run', 'real_trading']:
                return jsonify({
                    'success': False,
                    'error': 'Invalid trading mode'
                }), 400
            
            # Run async function in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            analysis = loop.run_until_complete(ai_chat.analyze_position(symbol, mode))
            loop.close()
            
            return jsonify({
                'success': True,
                'analysis': analysis,
                'symbol': symbol,
                'mode': mode,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # Socket.IO events for real-time chat
    @socketio.on('ai_chat_message')
    def handle_ai_chat_message(data):
        """Handle real-time AI chat messages"""
        try:
            # Run async function in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(ai_chat.handle_chat_message(data))
            loop.close()
            
            # Emit response back to client
            emit('ai_chat_response', response)
            
        except Exception as e:
            emit('ai_chat_error', {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    return ai_chat

# Test function
async def test_ai_chat():
    """Test AI chat functionality"""
    print("🧪 Testing AI Chat System...")
    
    try:
        socketio = None  # Mock for testing
        ai_chat = DashboardAIChat(socketio)
        
        # Test dry run chat
        print("\n📊 Testing dry run chat...")
        response = await ai_chat.handle_chat_message({
            'message': 'What is my current performance?',
            'mode': 'dry_run'
        })
        print(f"Response: {response.get('ai_response', 'No response')[:100]}...")
        
        # Test real trading chat
        print("\n💰 Testing real trading chat...")
        response = await ai_chat.handle_chat_message({
            'message': 'Show me my open positions',
            'mode': 'real_trading'
        })
        print(f"Response: {response.get('ai_response', 'No response')[:100]}...")
        
        # Test quick insights
        print("\n🔍 Testing quick insights...")
        insights = await ai_chat.get_quick_insights('dry_run')
        print(f"Insights: {insights[:100]}...")
        
        print("✅ AI Chat test completed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_ai_chat())