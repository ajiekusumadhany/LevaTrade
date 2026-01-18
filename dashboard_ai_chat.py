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
from trading_session_system import get_session_analyzer
from indicator_analysis_system import get_indicator_analyzer

class DashboardAIChat:
    def __init__(self, socketio):
        self.socketio = socketio
        self.gemini_analyst = get_gemini_analyst()
        self.session_analyzer = get_session_analyzer()
        self.indicator_analyzer = get_indicator_analyzer()
        
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
    
    async def analyze_session_performance(self, trading_mode: str = 'dry_run', days: int = 30):
        """Get AI analysis for session performance"""
        try:
            if not self.gemini_analyst:
                return "Gemini AI not available"
            
            # Get session performance data
            session_performance = self.session_analyzer.get_session_performance(trading_mode, days)
            
            if not session_performance.get('success'):
                return f"Session analysis error: {session_performance.get('error')}"
            
            # Get best/worst sessions
            best_worst = self.session_analyzer.get_best_worst_sessions(trading_mode, days)
            
            # Format session data for AI context
            session_summary = []
            for session_key, stats in session_performance['sessions'].items():
                if stats['total_trades'] > 0:
                    # Get top symbols for this session
                    top_symbols = sorted(stats['symbols'].items(), 
                                       key=lambda x: x[1]['win_rate'], reverse=True)[:3]
                    
                    # Get top indicators for this session
                    top_indicators = []
                    for ind_name, ind_data in stats['indicator_performance'].items():
                        if ind_data['total_passed'] > 0:
                            win_rate = (ind_data['wins_when_passed'] / ind_data['total_passed']) * 100
                            top_indicators.append((ind_name, win_rate, ind_data['total_passed']))
                    
                    top_indicators = sorted(top_indicators, key=lambda x: x[1], reverse=True)[:3]
                    
                    session_info = {
                        'name': stats['name'],
                        'color': stats['color'],
                        'total_trades': stats['total_trades'],
                        'win_rate': stats['win_rate'],
                        'total_pnl': stats['total_pnl'],
                        'avg_win': stats['avg_win'],
                        'avg_loss': stats['avg_loss'],
                        'max_win': stats['max_win'],
                        'max_loss': stats['max_loss'],
                        'profit_factor': stats['profit_factor'],
                        'top_symbols': top_symbols,
                        'top_indicators': top_indicators,
                        'directions': stats['directions'],
                        'exit_reasons': stats['exit_reasons']
                    }
                    session_summary.append(session_info)
            
            # Create detailed context for AI
            context_text = f"""
ANALISIS PERFORMA SESI TRADING - {trading_mode.upper()} MODE
Periode: {days} hari terakhir
Total Trades: {session_performance['total_trades']}

DETAIL PERFORMA PER SESI:
"""
            
            for session in session_summary:
                context_text += f"""
{session['color']} {session['name']}:
- Total Trades: {session['total_trades']}
- Win Rate: {session['win_rate']:.1f}%
- Total PnL: ${session['total_pnl']:.2f}
- Avg Win: ${session['avg_win']:.2f}
- Avg Loss: ${session['avg_loss']:.2f}
- Max Win: {session['max_win']:.2f}%
- Max Loss: {session['max_loss']:.2f}%
- Profit Factor: {session['profit_factor']:.2f}
- LONG trades: {session['directions'].get('LONG', 0)}
- SHORT trades: {session['directions'].get('SHORT', 0)}

Top Symbols:
"""
                for symbol, symbol_data in session['top_symbols']:
                    context_text += f"  • {symbol}: {symbol_data['win_rate']:.1f}% WR ({symbol_data['trades']} trades)\n"
                
                context_text += "Top Indicators:\n"
                for ind_name, win_rate, total_passed in session['top_indicators']:
                    context_text += f"  • {ind_name}: {win_rate:.1f}% WR ({total_passed} passed)\n"
                
                context_text += "Exit Reasons:\n"
                for reason, count in session['exit_reasons'].items():
                    context_text += f"  • {reason}: {count} trades\n"
                context_text += "\n"
            
            # Add best/worst session info
            if best_worst.get('success'):
                context_text += "RANKING SESI:\n"
                if best_worst.get('best_win_rate'):
                    session_key, session_data = best_worst['best_win_rate']
                    context_text += f"🏆 Best Win Rate: {session_data['name']} ({session_data['win_rate']:.1f}%)\n"
                
                if best_worst.get('most_profitable'):
                    session_key, session_data = best_worst['most_profitable']
                    context_text += f"💰 Most Profitable: {session_data['name']} (${session_data['total_pnl']:.2f})\n"
                
                if best_worst.get('most_active'):
                    session_key, session_data = best_worst['most_active']
                    context_text += f"🔥 Most Active: {session_data['name']} ({session_data['total_trades']} trades)\n"
            
            # Generate AI analysis with complete context
            question = f"""Berdasarkan data performa sesi trading saya yang lengkap di atas, berikan analisis mendalam tentang:

1. Sesi mana yang paling menguntungkan dan mengapa
2. Pattern trading yang terlihat di setiap sesi
3. Indikator mana yang paling efektif di setiap sesi
4. Rekomendasi strategi untuk mengoptimalkan performa
5. Waktu terbaik untuk trading berdasarkan data historis
6. Risk management yang tepat untuk setiap sesi

Berikan analisis dalam bahasa Indonesia yang actionable dan spesifik berdasarkan data actual saya."""
            
            # Prepare context for Gemini
            context = {
                'session_data': session_summary,
                'session_performance': session_performance,
                'best_worst_sessions': best_worst,
                'trading_mode': trading_mode,
                'analysis_period': days,
                'detailed_context': context_text
            }
            
            analysis = await self.gemini_analyst.chat_with_market_data(
                question,
                context,
                trading_mode
            )
            
            return analysis
            
        except Exception as e:
            return f"Session analysis error: {str(e)}"
    
    async def analyze_indicator_performance_by_session(self, trading_mode: str = 'dry_run', days: int = 7):
        """Get AI analysis for indicator performance by session"""
        try:
            if not self.gemini_analyst:
                return "Gemini AI not available"
            
            # Get session performance with indicator data
            session_performance = self.session_analyzer.get_session_performance(trading_mode, days)
            
            if not session_performance.get('success'):
                return f"Session analysis error: {session_performance.get('error')}"
            
            # Prepare detailed indicator performance summary
            indicator_summary = {}
            all_indicators = set()
            
            for session_key, session_data in session_performance['sessions'].items():
                if session_data['total_trades'] > 0:
                    indicator_summary[session_key] = {
                        'session_name': session_data['name'],
                        'session_color': session_data['color'],
                        'total_trades': session_data['total_trades'],
                        'win_rate': session_data['win_rate'],
                        'total_pnl': session_data['total_pnl'],
                        'indicators': {}
                    }
                    
                    # Process each indicator for this session
                    for ind_name, ind_data in session_data.get('indicator_performance', {}).items():
                        all_indicators.add(ind_name)
                        
                        if ind_data['total_passed'] > 0:
                            win_rate_when_passed = (ind_data['wins_when_passed'] / ind_data['total_passed']) * 100
                        else:
                            win_rate_when_passed = 0
                        
                        indicator_summary[session_key]['indicators'][ind_name] = {
                            'total_passed': ind_data['total_passed'],
                            'total_failed': ind_data['total_failed'],
                            'wins_when_passed': ind_data['wins_when_passed'],
                            'losses_when_passed': ind_data['losses_when_passed'],
                            'win_rate_when_passed': win_rate_when_passed,
                            'pass_rate': (ind_data['total_passed'] / (ind_data['total_passed'] + ind_data['total_failed'])) * 100 if (ind_data['total_passed'] + ind_data['total_failed']) > 0 else 0
                        }
            
            # Create comprehensive context for AI
            context_text = f"""
ANALISIS PERFORMA INDIKATOR PER SESI TRADING - {trading_mode.upper()} MODE
Periode: {days} hari terakhir

DETAIL PERFORMA INDIKATOR PER SESI:
"""
            
            for session_key, session_info in indicator_summary.items():
                context_text += f"""
{session_info['session_color']} {session_info['session_name']}:
- Total Trades: {session_info['total_trades']}
- Session Win Rate: {session_info['win_rate']:.1f}%
- Session PnL: ${session_info['total_pnl']:.2f}

Performa Indikator:
"""
                
                # Sort indicators by win rate when passed
                sorted_indicators = sorted(
                    session_info['indicators'].items(),
                    key=lambda x: x[1]['win_rate_when_passed'],
                    reverse=True
                )
                
                for ind_name, ind_stats in sorted_indicators:
                    if ind_stats['total_passed'] > 0:
                        context_text += f"""  • {ind_name}:
    - Win Rate when Passed: {ind_stats['win_rate_when_passed']:.1f}%
    - Times Passed: {ind_stats['total_passed']}
    - Times Failed: {ind_stats['total_failed']}
    - Pass Rate: {ind_stats['pass_rate']:.1f}%
    - Wins/Losses when Passed: {ind_stats['wins_when_passed']}/{ind_stats['losses_when_passed']}
"""
                context_text += "\n"
            
            # Cross-session indicator analysis
            context_text += "PERBANDINGAN INDIKATOR ANTAR SESI:\n"
            
            for indicator in all_indicators:
                context_text += f"\n{indicator.replace('_', ' ').title()}:\n"
                
                for session_key, session_info in indicator_summary.items():
                    if indicator in session_info['indicators']:
                        ind_data = session_info['indicators'][indicator]
                        if ind_data['total_passed'] > 0:
                            context_text += f"  {session_info['session_color']} {session_info['session_name']}: {ind_data['win_rate_when_passed']:.1f}% WR ({ind_data['total_passed']} passed)\n"
            
            # Generate AI analysis
            question = f"""Berdasarkan data performa indikator per sesi trading yang lengkap di atas, berikan analisis mendalam tentang:

1. Indikator mana yang paling efektif di setiap sesi dan mengapa
2. Pattern performa indikator yang berbeda antar sesi
3. Indikator mana yang konsisten perform baik di semua sesi
4. Indikator mana yang hanya bagus di sesi tertentu
5. Rekomendasi kombinasi indikator optimal untuk setiap sesi
6. Strategi adaptasi indikator berdasarkan sesi trading
7. Risk management berdasarkan performa indikator per sesi

Berikan analisis dalam bahasa Indonesia yang actionable dan spesifik berdasarkan data actual performa indikator saya."""
            
            context = {
                'indicator_by_session': indicator_summary,
                'trading_mode': trading_mode,
                'analysis_period': days,
                'detailed_context': context_text,
                'all_indicators': list(all_indicators)
            }
            
            analysis = await self.gemini_analyst.chat_with_market_data(
                question,
                context,
                trading_mode
            )
            
            return analysis
            
        except Exception as e:
            return f"Indicator session analysis error: {str(e)}"
    
    async def analyze_overall_indicator_performance(self, trading_mode: str = 'dry_run', days: int = 30):
        """Get AI analysis for overall indicator performance"""
        try:
            if not self.gemini_analyst:
                return "Gemini AI not available"
            
            from overall_indicator_performance_system import get_overall_indicator_analyzer
            
            analyzer = get_overall_indicator_analyzer()
            performance = analyzer.get_overall_indicator_performance(trading_mode, days)
            
            if not performance.get('success'):
                return f"Indicator analysis error: {performance.get('error')}"
            
            # Get category summary and recommendations
            categories = analyzer.get_indicator_categories_summary(performance)
            recommendations = analyzer.get_indicator_recommendations(performance)
            
            # Create detailed context for AI
            context_text = f"""
ANALISIS PERFORMA KESELURUHAN INDIKATOR - {trading_mode.upper()} MODE
Periode: {days} hari terakhir
Total Trades: {performance['total_trades_analyzed']}
Total Indikator: {performance['total_indicators']}

TOP PERFORMING INDICATORS:
"""
            
            # Top 10 indicators by accuracy
            top_indicators = list(performance['indicators'].items())[:10]
            for i, (ind_name, stats) in enumerate(top_indicators, 1):
                context_text += f"""
{i}. {stats['description']} ({stats['category']})
   - Overall Accuracy: {stats['overall_accuracy']:.1f}%
   - Pass Rate: {stats['pass_rate']:.1f}% ({stats['total_passed']}/{stats['total_trades']})
   - Win Rate When Passed: {stats['win_rate_when_passed']:.1f}%
   - Win Rate When Failed: {stats['win_rate_when_failed']:.1f}%
   - Avg PnL When Passed: ${stats['avg_pnl_when_passed']:.2f}
   - Avg PnL When Failed: ${stats['avg_pnl_when_failed']:.2f}
   - Symbols Traded: {len(stats['symbols_traded'])}
   - LONG/SHORT: {stats['directions_traded']['LONG']}/{stats['directions_traded']['SHORT']}
"""
            
            # Category summary
            context_text += "\nPERFORMA PER KATEGORI INDIKATOR:\n"
            for category, summary in categories.items():
                if summary.get('indicators'):
                    context_text += f"""
{category}:
- Avg Accuracy: {summary['avg_accuracy']:.1f}%
- Avg Pass Rate: {summary['avg_pass_rate']:.1f}%
- Total Trades: {summary['total_trades']}
- Best Indicators: {', '.join([ind['description'] for ind in summary['indicators'][:3]])}
"""
            
            # Generate AI analysis
            question = f"""Berdasarkan data performa keseluruhan indikator trading saya yang lengkap di atas, berikan analisis mendalam tentang:

1. Indikator mana yang paling akurat dan reliable untuk strategi saya
2. Kategori indikator mana yang paling efektif (TREND, MOMENTUM, OSCILLATOR, dll)
3. Indikator mana yang sebaiknya dihindari atau diperbaiki
4. Kombinasi indikator optimal berdasarkan performa historis
5. Strategi untuk meningkatkan akurasi indikator yang underperform
6. Risk management berdasarkan reliability setiap indikator
7. Rekomendasi filter dan konfirmasi indikator

Berikan analisis dalam bahasa Indonesia yang actionable dan spesifik berdasarkan data actual performa indikator saya."""
            
            context = {
                'indicator_performance': performance,
                'categories': categories,
                'recommendations': recommendations,
                'trading_mode': trading_mode,
                'analysis_period': days,
                'detailed_context': context_text
            }
            
            analysis = await self.gemini_analyst.chat_with_market_data(
                question,
                context,
                trading_mode
            )
            
            return analysis
            
        except Exception as e:
            return f"Overall indicator analysis error: {str(e)}"
    
    async def analyze_pair_performance(self, trading_mode: str = 'dry_run', days: int = 30):
        """Get AI analysis for pair performance"""
        try:
            if not self.gemini_analyst:
                return "Gemini AI not available"
            
            from pair_performance_system import get_pair_analyzer
            
            analyzer = get_pair_analyzer()
            performance = await analyzer.get_pair_performance(trading_mode, days)
            
            if not performance.get('success'):
                return f"Pair analysis error: {performance.get('error')}"
            
            # Get category summary and recommendations
            categories = analyzer.get_pair_categories_summary(performance)
            recommendations = analyzer.get_trading_recommendations(performance)
            
            # Create detailed context for AI
            context_text = f"""
ANALISIS PERFORMA TRADING PAIR - {trading_mode.upper()} MODE
Periode: {days} hari terakhir
Total Pairs: {performance['total_pairs']}

TOP PERFORMING PAIRS:
"""
            
            # Top 15 pairs by PnL
            top_pairs = list(performance['pairs'].items())[:15]
            for i, (symbol, stats) in enumerate(top_pairs, 1):
                vol_cat = stats.get('current_volume_category', {})
                mc_cat = stats.get('current_market_cap_category', {})
                
                context_text += f"""
{i}. {symbol}
   - Total PnL: ${stats['total_pnl']:.2f}
   - Win Rate: {stats['win_rate']:.1f}% ({stats['winning_trades']}/{stats['total_trades']})
   - LONG: {stats['long_percentage']:.1f}% | SHORT: {stats['short_percentage']:.1f}%
   - Avg PnL: ${stats['avg_pnl']:.2f}
   - Max Win: {stats['max_win']:.2f}% | Max Loss: {stats['max_loss']:.2f}%
   - Volume: {vol_cat.get('color', '❓')} {vol_cat.get('category', 'Unknown')} (${stats.get('current_volume_24h', 0):,.0f})
   - Market Cap: {mc_cat.get('color', '❓')} {mc_cat.get('category', 'Unknown')} (${stats.get('current_market_cap', 0):,.0f})
   - Current Price: ${stats.get('current_price', 0):.4f}
   - 24h Change: {stats.get('price_change_24h', 0):.2f}%
"""
            
            # Category analysis
            context_text += "\nANALISIS PER KATEGORI VOLUME:\n"
            for vol_category, pairs in categories['volume_categories'].items():
                if pairs:
                    total_pnl = sum(p['total_pnl'] for p in pairs)
                    avg_win_rate = sum(p['win_rate'] for p in pairs) / len(pairs)
                    context_text += f"""
{vol_category} ({categories['category_definitions']['volume'][vol_category]['description']}):
- Total Pairs: {len(pairs)}
- Combined PnL: ${total_pnl:.2f}
- Avg Win Rate: {avg_win_rate:.1f}%
- Top 3: {', '.join([p['symbol'] for p in pairs[:3]])}
"""
            
            context_text += "\nANALISIS PER KATEGORI MARKET CAP:\n"
            for mc_category, pairs in categories['market_cap_categories'].items():
                if pairs:
                    total_pnl = sum(p['total_pnl'] for p in pairs)
                    avg_win_rate = sum(p['win_rate'] for p in pairs) / len(pairs)
                    context_text += f"""
{mc_category} ({categories['category_definitions']['market_cap'][mc_category]['description']}):
- Total Pairs: {len(pairs)}
- Combined PnL: ${total_pnl:.2f}
- Avg Win Rate: {avg_win_rate:.1f}%
- Top 3: {', '.join([p['symbol'] for p in pairs[:3]])}
"""
            
            # Generate AI analysis
            question = f"""Berdasarkan data performa trading pair yang lengkap di atas, berikan analisis mendalam tentang:

1. Pair mana yang paling menguntungkan dan konsisten
2. Kategori volume dan market cap mana yang paling profitable
3. Pair mana yang sebaiknya dihindari (terutama volume <$100M)
4. Pattern performa berdasarkan ukuran koin (besar, menengah, kecil)
5. Rekomendasi pair selection untuk scalping dan swing trading
6. Risk management berdasarkan kategori pair
7. Strategi diversifikasi portfolio berdasarkan performa historis
8. Pair mana yang cocok untuk LONG vs SHORT strategy

Berikan analisis dalam bahasa Indonesia yang actionable dan spesifik berdasarkan data actual performa pair saya."""
            
            context = {
                'pair_performance': performance,
                'categories': categories,
                'recommendations': recommendations,
                'trading_mode': trading_mode,
                'analysis_period': days,
                'detailed_context': context_text
            }
            
            analysis = await self.gemini_analyst.chat_with_market_data(
                question,
                context,
                trading_mode
            )
            
            return analysis
            
        except Exception as e:
            return f"Pair analysis error: {str(e)}"

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
    # Additional AI endpoints for session analysis
    @app.route('/api/ai/session-analysis/<mode>')
    def ai_session_analysis_endpoint(mode):
        """Session performance analysis endpoint"""
        try:
            # Validate mode
            if mode not in ['dry_run', 'real_trading']:
                return jsonify({
                    'success': False,
                    'error': 'Invalid trading mode'
                }), 400
            
            days = int(request.args.get('days', 30))
            
            # Run async function in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            analysis = loop.run_until_complete(ai_chat.analyze_session_performance(mode, days))
            loop.close()
            
            return jsonify({
                'success': True,
                'analysis': analysis,
                'mode': mode,
                'days': days,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/ai/indicator-session-analysis/<mode>')
    def ai_indicator_session_analysis_endpoint(mode):
        """Indicator performance by session analysis endpoint"""
        try:
            # Validate mode
            if mode not in ['dry_run', 'real_trading']:
                return jsonify({
                    'success': False,
                    'error': 'Invalid trading mode'
                }), 400
            
            days = int(request.args.get('days', 7))
            
            # Run async function in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            analysis = loop.run_until_complete(ai_chat.analyze_indicator_performance_by_session(mode, days))
            loop.close()
            
            return jsonify({
                'success': True,
                'analysis': analysis,
                'mode': mode,
                'days': days,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/ai/overall-indicator-analysis/<mode>')
    def ai_overall_indicator_analysis_endpoint(mode):
        """Overall indicator performance analysis endpoint"""
        try:
            # Validate mode
            if mode not in ['dry_run', 'real_trading']:
                return jsonify({
                    'success': False,
                    'error': 'Invalid trading mode'
                }), 400
            
            days = int(request.args.get('days', 30))
            
            # Run async function in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            analysis = loop.run_until_complete(ai_chat.analyze_overall_indicator_performance(mode, days))
            loop.close()
            
            return jsonify({
                'success': True,
                'analysis': analysis,
                'mode': mode,
                'days': days,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/ai/pair-analysis/<mode>')
    def ai_pair_analysis_endpoint(mode):
        """Pair performance analysis endpoint"""
        try:
            # Validate mode
            if mode not in ['dry_run', 'real_trading']:
                return jsonify({
                    'success': False,
                    'error': 'Invalid trading mode'
                }), 400
            
            days = int(request.args.get('days', 30))
            
            # Run async function in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            analysis = loop.run_until_complete(ai_chat.analyze_pair_performance(mode, days))
            loop.close()
            
            return jsonify({
                'success': True,
                'analysis': analysis,
                'mode': mode,
                'days': days,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500