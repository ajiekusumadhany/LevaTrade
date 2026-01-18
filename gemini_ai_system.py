#!/usr/bin/env python3
"""
Gemini AI Integration System for Market Analysis and Reasoning
- Entry reasoning for new positions
- Exit reasoning for closed positions
- Interactive chat with real market data
- Market condition analysis
"""
import os
import json
import asyncio
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from pybit.unified_trading import HTTP
from dry_run_system import dry_run_system
from real_trade_system import real_trade_system

# Import technical analysis functions from main bot
import sys
sys.path.append('.')
try:
    from crypto_bot_parallel import calculate_ema, calculate_rsi, calculate_atr, calculate_macd, get_klines
except ImportError:
    print("⚠️  Could not import technical analysis functions from main bot")
    calculate_ema = calculate_rsi = calculate_atr = calculate_macd = get_klines = None

# Load environment variables
load_dotenv()

class GeminiMarketAnalyst:
    def __init__(self):
        """Initialize Gemini AI Market Analyst with API key rotation"""
        # Load multiple API keys from environment
        api_keys_str = os.getenv('GEMINI_API_KEYS', '')
        if not api_keys_str:
            raise ValueError("GEMINI_API_KEYS not found in environment variables")
        
        # Parse multiple API keys
        self.api_keys = [key.strip() for key in api_keys_str.split(',') if key.strip()]
        if not self.api_keys:
            raise ValueError("No valid Gemini API keys found")
        
        self.current_key_index = 0
        self.model_name = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')
        self.temperature = float(os.getenv('GEMINI_TEMPERATURE', '0.7'))
        self.max_tokens = int(os.getenv('GEMINI_MAX_TOKENS', '500'))
        
        # Configure Gemini with first API key
        genai.configure(api_key=self.api_keys[0])
        self.model = genai.GenerativeModel(self.model_name)
        
        # Bybit session for real market data
        self.session = HTTP(
            testnet=False,
            api_key=os.getenv('BYBIT_API_KEY', ''),
            api_secret=os.getenv('BYBIT_API_SECRET', '')
        )
        
        print(f"🤖 Gemini AI Market Analyst initialized with {len(self.api_keys)} API keys")
        print(f"📊 Model: {self.model_name}")
        print(f"⚙️  Temperature: {self.temperature}, Max Tokens: {self.max_tokens}")
    
    def _rotate_api_key(self):
        """Rotate to next API key"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        current_key = self.api_keys[self.current_key_index]
        
        # Reconfigure Gemini with new API key
        genai.configure(api_key=current_key)
        self.model = genai.GenerativeModel(self.model_name)
        
        print(f"🔄 Rotated to API key #{self.current_key_index + 1}/{len(self.api_keys)}")
    
    def _get_current_api_key_info(self) -> str:
        """Get current API key info for logging"""
        return f"Key {self.current_key_index + 1}/{len(self.api_keys)}"
    
    async def generate_entry_reasoning(self, signal_data: Dict) -> str:
        """Generate AI reasoning for position entry in Indonesian"""
        try:
            # Get current market data
            market_data = await self._get_market_context(signal_data['symbol'])
            
            # Collect all indicators from signal data
            indicators = {
                # Boolean indicators
                'ema_fast_above_slow': signal_data.get('ema_fast_above_slow', False),
                'macd_bullish': signal_data.get('macd_bullish', False),
                'rsi_oversold': signal_data.get('rsi_oversold', False),
                'rsi_overbought': signal_data.get('rsi_overbought', False),
                'rsi_neutral': signal_data.get('rsi_neutral', False),
                'volume_confirmation': signal_data.get('volume_confirmation', False),
                'volatility_confirmation': signal_data.get('volatility_confirmation', False),
                'price_near_support': signal_data.get('price_near_support', False),
                'price_near_resistance': signal_data.get('price_near_resistance', False),
                'trend_alignment': signal_data.get('trend_alignment', False),
                'momentum_confirmation': signal_data.get('momentum_confirmation', False),
                
                # Numerical values
                'rsi_level': signal_data.get('rsi_level', 50),
                'atr_value': signal_data.get('atr_value', 0),
                'ema_fast_value': signal_data.get('ema_fast_value', 0),
                'ema_slow_value': signal_data.get('ema_slow_value', 0),
                'macd_line_value': signal_data.get('macd_line_value', 0),
                'signal_line_value': signal_data.get('signal_line_value', 0),
                'support_resistance': signal_data.get('support_resistance', 0),
                'price_distance_from_level': signal_data.get('price_distance_from_level', 0)
            }
            
            # Prepare prompt for entry reasoning
            prompt = f"""
            Analisis entry trading crypto ini dan berikan penjelasan detail:
            
            DETAIL POSISI:
            - Symbol: {signal_data['symbol']}
            - Arah: {signal_data['direction']}
            - Harga Entry: ${signal_data['close']:.6f}
            - Take Profit: ${signal_data.get('tp', 'N/A')}
            - Stop Loss: ${signal_data.get('sl', 'N/A')}
            - Ukuran Posisi: {signal_data.get('pos_size', 'N/A')}
            - Leverage: {signal_data.get('leverage', 'N/A')}x
            
            INDIKATOR TEKNIKAL:
            {self._format_indicators(indicators)}
            
            DATA PASAR SAAT INI:
            {market_data}
            
            Berikan analisis dalam bahasa Indonesia yang mencakup:<br><br>
            <b>1. Alasan Entry:</b> Mengapa ini titik entry yang bagus<br><br>
            <b>2. Analisis Teknikal:</b> Indikator kunci yang mendukung trade ini<br><br>
            <b>3. Konteks Pasar:</b> Kondisi pasar saat ini dan sentimen<br><br>
            <b>4. Penilaian Risiko:</b> Potensi risiko dan mitigasinya<br><br>
            <b>5. Ekspektasi Hasil:</b> Target harga dan timeline
            
            PENTING:
            - Gunakan bahasa Indonesia yang jelas dan ringkas (maksimal 300 kata)
            - JANGAN gunakan format markdown (**, *, #, dll)
            - Gunakan HTML formatting untuk keterbacaan: <b>bold</b>, <i>italic</i>, <br> untuk line break
            - Format output dengan HTML tags yang akan ditampilkan dengan baik di dashboard
            - Contoh: <b>Alasan Entry:</b> Kondisi bullish terlihat dari...<br><br><b>Analisis Teknikal:</b> EMA menunjukkan...
            """
            
            response = await self._generate_response(prompt)
            return response
            
        except Exception as e:
            print(f"❌ Error generating entry reasoning: {e}")
            return f"Analisis entry tidak tersedia karena error: {str(e)}"
    
    async def generate_exit_reasoning(self, position_data: Dict, exit_reason: str) -> str:
        """Generate AI reasoning for position exit in Indonesian"""
        try:
            # Get market data from entry to exit
            market_journey = await self._get_market_journey(
                position_data['symbol'],
                position_data['entry_time'],
                datetime.now()
            )
            
            # Prepare prompt for exit reasoning in Indonesian
            prompt = f"""
            Analisis penutupan posisi trading crypto ini dan jelaskan apa yang terjadi:
            
            DETAIL POSISI:
            - Symbol: {position_data['symbol']}
            - Arah: {position_data['direction']}
            - Harga Entry: ${position_data['entry_price']:.6f}
            - Harga Exit: ${position_data['exit_price']:.6f}
            - Alasan Exit: {exit_reason}
            - Durasi: {self._calculate_duration(position_data['entry_time'], datetime.now())}
            - PnL: ${position_data.get('realized_pnl', 0):.2f} ({position_data.get('pnl_percentage', 0):.2f}%)
            
            PERJALANAN PASAR:
            {market_journey}
            
            INDIKATOR ENTRY AWAL:
            {self._format_indicators(position_data.get('entry_indicators', {}))}
            
            Berikan penjelasan dalam bahasa Indonesia yang mencakup:
            
            <b>Apa yang Terjadi:</b><br>
            Jelaskan pergerakan pasar dari entry hingga exit dengan detail.<br><br>
            
            <b>Analisis Exit:</b><br>
            Jelaskan mengapa posisi ditutup (TP/SL/manual) dan kondisi saat itu.<br><br>
            
            <b>Faktor Pasar:</b><br>
            Sebutkan kondisi atau peristiwa kunci yang mempengaruhi hasil trade.<br><br>
            
            <b>Review Performa:</b><br>
            Evaluasi apakah ini trade yang bagus dan apa yang bisa diperbaiki.<br><br>
            
            <b>Pelajaran Penting:</b><br>
            Berikan insight penting untuk trade selanjutnya.
            
            PENTING: 
            - Gunakan bahasa Indonesia yang natural dan mudah dipahami
            - JANGAN gunakan format markdown (**, *, #, dll)
            - WAJIB gunakan HTML formatting untuk keterbacaan: <b>bold</b>, <i>italic</i>, <br> untuk line break
            - Format output dengan HTML tags yang akan ditampilkan dengan baik di dashboard
            - Maksimal 250 kata
            - Fokus pada analisis praktis dan edukatif
            - CONTOH FORMAT YANG BENAR:
            
            <b>Apa yang Terjadi:</b><br>
            Harga bergerak dari $3250.75 ke $3180.25 dalam waktu 18 menit...<br><br>
            
            <b>Analisis Exit:</b><br>
            Posisi ditutup karena TP_HIT yang menunjukkan target profit tercapai...<br><br>
            
            <b>Faktor Pasar:</b><br>
            RSI overbought memberikan sinyal yang tepat untuk entry SHORT...<br><br>
            
            GUNAKAN FORMAT HTML SEPERTI CONTOH DI ATAS!
            
            PENTING: 
            - Gunakan bahasa Indonesia yang natural dan mudah dipahami
            - JANGAN gunakan format markdown (**, *, #, dll)
            - JANGAN gunakan bold, italic, atau formatting apapun
            - Tulis dalam format paragraf biasa yang siap ditampilkan
            - Maksimal 250 kata
            - Fokus pada analisis praktis dan edukatif
            - Output harus berupa teks plain tanpa formatting
            """
            
            response = await self._generate_response(prompt)
            return response
            
        except Exception as e:
            print(f"❌ Error generating exit reasoning: {e}")
            return f"Analisis exit tidak tersedia karena error: {str(e)}"
    
    async def chat_with_market_data(self, user_question: str, context: Dict = None, trading_mode: str = "dry_run") -> str:
        """Interactive chat with real market data access and trading system data
        
        Args:
            user_question: User's question
            context: Additional context (symbol, etc.)
            trading_mode: "dry_run" or "real_trading" to determine which data to access
        """
        try:
            # Analyze user question to determine what data to fetch
            question_lower = user_question.lower()
            
            # Get current market overview
            market_overview = await self._get_market_overview()
            
            # Get trading system data based on question context and mode
            system_data = ""
            
            # Add mode indicator
            mode_name = "SIMULASI (DRY RUN)" if trading_mode == "dry_run" else "TRADING NYATA"
            system_data += f"MODE SAAT INI: {mode_name}\n\n"
            
            # Trading performance and history
            if any(word in question_lower for word in ['performance', 'performa', 'kinerja', 'history', 'riwayat', 'trades', 'trading', 'pnl', 'profit', 'loss', 'rugi', 'untung', 'win rate']):
                system_data += await self._get_trading_performance_data(trading_mode)
                system_data += await self._get_detailed_trading_history(trading_mode)
            
            # Open positions
            if any(word in question_lower for word in ['position', 'posisi', 'open', 'buka', 'current', 'saat ini', 'holding', 'pegang']):
                system_data += await self._get_current_positions_data(trading_mode)
            
            # Specific symbol analysis
            symbol_to_analyze = None
            if context and 'symbol' in context:
                symbol_to_analyze = context['symbol']
            else:
                # Extract symbol from question
                words = user_question.upper().split()
                for word in words:
                    if word.endswith('USDT'):
                        symbol_to_analyze = word
                        break
                    elif word in ['BTC', 'ETH', 'XRP', 'SOL', 'DOGE', 'ADA', 'DOT', 'LINK', 'UNI', 'AVAX']:
                        symbol_to_analyze = f"{word}USDT"
                        break
            
            if symbol_to_analyze:
                system_data += await self._get_comprehensive_symbol_analysis(symbol_to_analyze, trading_mode)
            
            # Technical analysis request
            if any(word in question_lower for word in ['analisis', 'analysis', 'teknikal', 'technical', 'indikator', 'indicator', 'chart', 'grafik']):
                if symbol_to_analyze:
                    system_data += await self._get_technical_analysis(symbol_to_analyze)
                else:
                    system_data += await self._get_market_technical_overview()
            
            # System statistics and analytics
            if any(word in question_lower for word in ['system', 'sistem', 'bot', 'statistics', 'statistik', 'analytics', 'analitik', 'overview', 'ringkasan']):
                system_data += await self._get_system_analytics(trading_mode)
            
            # Recent activity
            if any(word in question_lower for word in ['recent', 'terbaru', 'latest', 'terakhir', 'today', 'hari ini', 'yesterday', 'kemarin']):
                system_data += await self._get_recent_activity(trading_mode)
            
            prompt = f"""
            Anda adalah asisten AI trading crypto yang canggih dengan akses penuh ke data sistem trading pengguna dan informasi pasar real-time.
            
            WAKTU SAAT INI: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} WIB
            
            PERTANYAAN PENGGUNA: {user_question}
            
            RINGKASAN PASAR SAAT INI (Real-time):
            {market_overview}
            
            DATA SISTEM TRADING (Fresh from Database):
            {system_data}
            
            PENTING: Semua data yang Anda terima adalah REAL-TIME dan UP-TO-DATE dari database dan API pasar. 
            Tidak ada data cache yang digunakan. Setiap query mengambil data terbaru langsung dari sumber.
            
            Berikan respons yang komprehensif dan membantu berdasarkan data pasar real-time dan informasi sistem trading.
            
            Panduan:
            - Gunakan angka dan data spesifik dari sistem trading yang FRESH
            - Berikan wawasan yang dapat ditindaklanjuti jika memungkinkan
            - Jika ditanya tentang performa, sertakan win rate, PnL, dan statistik trading terbaru
            - Jika ditanya tentang posisi, sertakan status saat ini dan unrealized PnL real-time
            - Jika ditanya tentang kondisi pasar, kaitkan dengan strategi trading pengguna
            - Jika ditanya tentang analisis teknikal, berikan penjelasan detail indikator real-time
            - Gunakan bahasa yang percakapan namun tetap presisi dengan data
            - SELALU GUNAKAN BAHASA INDONESIA dalam respons Anda
            - Gunakan HTML formatting untuk keterbacaan: <b>bold</b>, <i>italic</i>, <br> untuk line break
            - JANGAN gunakan markdown syntax (**, *, #, dll)
            - Jangan menyebutkan mode trading (simulasi/nyata) kecuali ditanya langsung
            - Fokus pada analisis dan insight, bukan pada disclaimer mode
            - Sebutkan bahwa data yang Anda berikan adalah real-time jika relevan
            
            Batasi respons hingga maksimal 500 kata dan gunakan bahasa Indonesia yang natural.
            """
            
            response = await self._generate_response(prompt)
            return response
            
        except Exception as e:
            print(f"❌ Error in chat response: {e}")
            return f"Maaf, saya mengalami kesulitan mengakses data sistem trading saat ini: {str(e)}"
    
    async def analyze_market_conditions(self, symbols: List[str] = None) -> str:
        """Analyze current market conditions"""
        try:
            # Get market data for analysis
            if symbols:
                market_data = await self._get_multi_symbol_data(symbols[:10])  # Limit to 10 symbols
            else:
                market_data = await self._get_market_overview()
            
            prompt = f"""
            Analyze the current crypto market conditions:
            
            MARKET DATA:
            {market_data}
            
            Please provide:
            1. **Market Sentiment**: Overall bullish/bearish/neutral
            2. **Key Trends**: Major price movements and patterns
            3. **Volatility Assessment**: Current market volatility levels
            4. **Trading Opportunities**: Potential setups or risks
            5. **Outlook**: Short-term market expectations
            
            Keep it concise and actionable (max 200 words).
            """
            
            response = await self._generate_response(prompt)
            return response
            
        except Exception as e:
            print(f"❌ Error analyzing market conditions: {e}")
            return f"Market analysis unavailable: {str(e)}"
    
    async def _generate_response(self, prompt: str, retry_count: int = 0) -> str:
        """Generate response using Gemini AI with automatic API key rotation on rate limits"""
        max_retries = len(self.api_keys)
        
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                    top_p=0.8,
                    top_k=40
                )
            )
            return response.text
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if it's a rate limit error
            if ('rate limit' in error_str or 'quota' in error_str or 'too many requests' in error_str) and retry_count < max_retries:
                print(f"⚠️  Rate limit hit on {self._get_current_api_key_info()}, rotating to next key...")
                self._rotate_api_key()
                
                # Wait a bit before retrying
                await asyncio.sleep(1)
                
                # Retry with next API key
                return await self._generate_response(prompt, retry_count + 1)
            
            # If not a rate limit error or max retries reached
            print(f"❌ Gemini API error ({self._get_current_api_key_info()}): {e}")
            
            if retry_count >= max_retries:
                return f"AI response unavailable: All API keys exhausted. Error: {str(e)}"
            else:
                return f"AI response unavailable: {str(e)}"
    
    async def _get_market_context(self, symbol: str) -> str:
        """Get current market context for a symbol"""
        try:
            # Get current price and 24h stats
            ticker_response = self.session.get_tickers(category="linear", symbol=symbol)
            if ticker_response['retCode'] != 0:
                return "Market data unavailable"
            
            ticker = ticker_response['result']['list'][0]
            
            # Get recent klines for trend analysis
            klines_response = self.session.get_kline(
                category="linear",
                symbol=symbol,
                interval="15",
                limit=20
            )
            
            if klines_response['retCode'] != 0:
                return "Price history unavailable"
            
            klines = klines_response['result']['list']
            prices = [float(k[4]) for k in klines]  # Close prices
            
            # Calculate basic metrics
            current_price = float(ticker['lastPrice'])
            price_change_24h = float(ticker['price24hPcnt']) * 100
            volume_24h = float(ticker['volume24h'])
            
            # Simple trend analysis
            if len(prices) >= 5:
                recent_trend = "Uptrend" if prices[-1] > prices[-5] else "Downtrend"
                volatility = np.std(prices[-10:]) / np.mean(prices[-10:]) * 100
            else:
                recent_trend = "Neutral"
                volatility = 0
            
            return f"""
            Current Price: ${current_price:.6f}
            24h Change: {price_change_24h:+.2f}%
            24h Volume: ${volume_24h:,.0f}
            Recent Trend: {recent_trend}
            Volatility: {volatility:.2f}%
            """
            
        except Exception as e:
            return f"Market context error: {str(e)}"
    
    async def _get_market_journey(self, symbol: str, start_time, end_time) -> str:
        """Get market data journey from entry to exit"""
        try:
            # Convert string to datetime if needed
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00')).replace(tzinfo=None)
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00')).replace(tzinfo=None)
            
            # Calculate time difference in hours
            time_diff = (end_time - start_time).total_seconds() / 3600
            
            # Determine appropriate interval based on duration
            if time_diff <= 4:
                interval = "15"  # 15 minutes
                limit = min(int(time_diff * 4), 200)
            elif time_diff <= 24:
                interval = "60"  # 1 hour
                limit = min(int(time_diff), 200)
            else:
                interval = "240"  # 4 hours
                limit = min(int(time_diff / 4), 200)
            
            # Get klines data
            klines_response = self.session.get_kline(
                category="linear",
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            if klines_response['retCode'] != 0:
                return "Market journey data unavailable"
            
            klines = klines_response['result']['list']
            if not klines:
                return "No market data available for this period"
            
            # Analyze the journey
            prices = [float(k[4]) for k in klines]  # Close prices
            volumes = [float(k[5]) for k in klines]  # Volumes
            
            start_price = prices[0] if prices else 0
            end_price = prices[-1] if prices else 0
            max_price = max(prices) if prices else 0
            min_price = min(prices) if prices else 0
            avg_volume = np.mean(volumes) if volumes else 0
            
            price_change = ((end_price - start_price) / start_price * 100) if start_price > 0 else 0
            
            return f"""
            Journey Duration: {time_diff:.1f} hours
            Start Price: ${start_price:.6f}
            End Price: ${end_price:.6f}
            Price Change: {price_change:+.2f}%
            High: ${max_price:.6f}
            Low: ${min_price:.6f}
            Avg Volume: ${avg_volume:,.0f}
            """
            
        except Exception as e:
            return f"Market journey error: {str(e)}"
    
    async def _get_market_overview(self) -> str:
        """Get general market overview"""
        try:
            # Get top symbols data
            tickers_response = self.session.get_tickers(category="linear")
            if tickers_response['retCode'] != 0:
                return "Market overview unavailable"
            
            tickers = tickers_response['result']['list']
            
            # Filter for major USDT pairs
            major_pairs = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'SOLUSDT', 'DOGEUSDT']
            major_data = []
            
            for ticker in tickers:
                if ticker['symbol'] in major_pairs:
                    major_data.append({
                        'symbol': ticker['symbol'],
                        'price': float(ticker['lastPrice']),
                        'change': float(ticker['price24hPcnt']) * 100,
                        'volume': float(ticker['volume24h'])
                    })
            
            # Sort by volume
            major_data.sort(key=lambda x: x['volume'], reverse=True)
            
            overview = "MAJOR PAIRS:\n"
            for data in major_data[:5]:
                emoji = "🟢" if data['change'] >= 0 else "🔴"
                overview += f"{emoji} {data['symbol']}: ${data['price']:.6f} ({data['change']:+.2f}%)\n"
            
            return overview
            
        except Exception as e:
            return f"Market overview error: {str(e)}"
    
    async def _get_detailed_symbol_data(self, symbol: str) -> str:
        """Get detailed data for specific symbol"""
        try:
            # Get ticker data
            ticker_response = self.session.get_tickers(category="linear", symbol=symbol)
            if ticker_response['retCode'] != 0:
                return f"Data unavailable for {symbol}"
            
            ticker = ticker_response['result']['list'][0]
            
            return f"""
            {symbol} Details:
            Price: ${float(ticker['lastPrice']):.6f}
            24h Change: {float(ticker['price24hPcnt']) * 100:+.2f}%
            24h High: ${float(ticker['highPrice24h']):.6f}
            24h Low: ${float(ticker['lowPrice24h']):.6f}
            24h Volume: ${float(ticker['volume24h']):,.0f}
            Open Interest: ${float(ticker.get('openInterest', 0)):,.0f}
            """
            
        except Exception as e:
            return f"Symbol data error: {str(e)}"
    
    async def _get_multi_symbol_data(self, symbols: List[str]) -> str:
        """Get data for multiple symbols"""
        try:
            tickers_response = self.session.get_tickers(category="linear")
            if tickers_response['retCode'] != 0:
                return "Multi-symbol data unavailable"
            
            all_tickers = {t['symbol']: t for t in tickers_response['result']['list']}
            
            result = "SELECTED SYMBOLS:\n"
            for symbol in symbols:
                if symbol in all_tickers:
                    ticker = all_tickers[symbol]
                    change = float(ticker['price24hPcnt']) * 100
                    emoji = "🟢" if change >= 0 else "🔴"
                    result += f"{emoji} {symbol}: ${float(ticker['lastPrice']):.6f} ({change:+.2f}%)\n"
            
            return result
            
        except Exception as e:
            return f"Multi-symbol data error: {str(e)}"
    
    def _format_indicators(self, indicators: Dict) -> str:
        """Format technical indicators for AI prompt with clear descriptions"""
        if not indicators:
            return "No indicator data available"
        
        formatted = []
        
        # Group indicators by type for better readability
        boolean_indicators = []
        numerical_indicators = []
        
        # Indicator descriptions
        descriptions = {
            'ema_fast_above_slow': 'EMA Fast > EMA Slow (Trend Direction)',
            'macd_bullish': 'MACD Bullish (Momentum)',
            'rsi_oversold': 'RSI Oversold (<35)',
            'rsi_overbought': 'RSI Overbought (>65)',
            'rsi_neutral': 'RSI Neutral Zone (35-65)',
            'volume_confirmation': 'Volume Above Average',
            'volatility_confirmation': 'Sufficient Volatility',
            'price_near_support': 'Price Near Support Level',
            'price_near_resistance': 'Price Near Resistance Level',
            'trend_alignment': 'Trend Alignment with Direction',
            'momentum_confirmation': 'Momentum Confirmation',
            'rsi_level': 'RSI Level',
            'atr_value': 'Average True Range (ATR)',
            'ema_fast_value': 'EMA Fast Value',
            'ema_slow_value': 'EMA Slow Value',
            'macd_line_value': 'MACD Line Value',
            'signal_line_value': 'MACD Signal Line Value',
            'support_resistance': 'Support/Resistance Level',
            'price_distance_from_level': 'Distance from Key Level (%)'
        }
        
        for key, value in indicators.items():
            description = descriptions.get(key, key.replace('_', ' ').title())
            
            if isinstance(value, bool):
                status = "✅ TRUE" if value else "❌ FALSE"
                boolean_indicators.append(f"- {description}: {status}")
            elif isinstance(value, (int, float)):
                if value != 0:  # Only show non-zero values
                    numerical_indicators.append(f"- {description}: {value:.6f}")
        
        # Combine formatted indicators
        if boolean_indicators:
            formatted.append("KONDISI SINYAL:")
            formatted.extend(boolean_indicators)
        
        if numerical_indicators:
            if boolean_indicators:
                formatted.append("")  # Add spacing
            formatted.append("NILAI INDIKATOR:")
            formatted.extend(numerical_indicators)
        
        return "\n".join(formatted) if formatted else "No valid indicator data"
    
    def _calculate_duration(self, start_time, end_time) -> str:
        """Calculate and format duration - handles both string and datetime inputs"""
        try:
            # Convert string to datetime if needed
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00')).replace(tzinfo=None)
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00')).replace(tzinfo=None)
            
            duration = end_time - start_time
            hours = duration.total_seconds() / 3600
            
            if hours < 1:
                minutes = duration.total_seconds() / 60
                return f"{minutes:.0f}m"
            elif hours < 24:
                return f"{hours:.1f}h"
            else:
                days = hours / 24
                return f"{days:.1f}d"
        except Exception as e:
            print(f"⚠️  Duration calculation error: {e}")
            return "Unknown duration"
    
    async def _get_trading_performance_data(self, trading_mode: str = "dry_run") -> str:
        """Get comprehensive trading performance data for specific mode - ALWAYS FRESH DATA"""
        try:
            if trading_mode == "dry_run":
                # Force fresh data fetch from database
                performance_data = self._get_system_performance(dry_run_system, "DRY RUN SIMULATION")
            else:
                # Force fresh data fetch from database
                performance_data = self._get_system_performance(real_trade_system, "REAL TRADING")
            
            return f"""
            TRADING PERFORMANCE ({trading_mode.upper().replace('_', ' ')}) - DATA REAL-TIME:
            
            {performance_data}
            """
            
        except Exception as e:
            return f"Performance data error: {str(e)}"
    
    def _get_system_performance(self, trading_system, system_name: str) -> str:
        """Get performance data from a trading system - ALWAYS FRESH FROM DATABASE"""
        try:
            # Force fresh data fetch - no caching
            closed_positions = trading_system.get_closed_positions()  # Fresh from DB
            open_positions = trading_system.get_open_positions()      # Fresh from DB
            
            if not closed_positions and not open_positions:
                return f"{system_name}: No trading activity"
            
            # Calculate performance metrics from fresh data
            total_trades = len(closed_positions)
            winning_trades = len([p for p in closed_positions if p.get('realized_pnl', 0) > 0])
            losing_trades = len([p for p in closed_positions if p.get('realized_pnl', 0) < 0])
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            total_pnl = sum(p.get('realized_pnl', 0) for p in closed_positions)
            unrealized_pnl = sum(p.get('unrealized_pnl', 0) for p in open_positions)
            
            # Best and worst trades from fresh data
            best_trade = max(closed_positions, key=lambda x: x.get('realized_pnl', 0)) if closed_positions else None
            worst_trade = min(closed_positions, key=lambda x: x.get('realized_pnl', 0)) if closed_positions else None
            
            # Recent activity (last 24h) - calculated from fresh data
            now = datetime.now()
            recent_trades = []
            for p in closed_positions:
                if p.get('exit_time'):
                    try:
                        exit_time = datetime.fromisoformat(p['exit_time'].replace('Z', '+00:00')).replace(tzinfo=None)
                        if exit_time > now - timedelta(days=1):
                            recent_trades.append(p)
                    except:
                        continue
            
            # Add timestamp to show data freshness
            current_time = datetime.now().strftime('%H:%M:%S')
            
            performance_text = f"""
            {system_name} PERFORMANCE (Updated: {current_time}):
            - Total Trades: {total_trades}
            - Win Rate: {win_rate:.1f}% ({winning_trades}W / {losing_trades}L)
            - Realized PnL: ${total_pnl:.2f}
            - Unrealized PnL: ${unrealized_pnl:.2f}
            - Open Positions: {len(open_positions)}
            - Recent 24h Trades: {len(recent_trades)}
            """
            
            if best_trade:
                performance_text += f"- Best Trade: {best_trade['symbol']} ${best_trade.get('realized_pnl', 0):.2f}\n"
            
            if worst_trade:
                performance_text += f"- Worst Trade: {worst_trade['symbol']} ${worst_trade.get('realized_pnl', 0):.2f}\n"
            
            return performance_text
            
        except Exception as e:
            return f"{system_name} performance error: {str(e)}"
    
    async def _get_current_positions_data(self, trading_mode: str = "dry_run") -> str:
        """Get current open positions data for specific mode - ALWAYS FRESH DATA"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S')
            positions_text = f"CURRENT POSITIONS ({trading_mode.upper().replace('_', ' ')}) - REAL-TIME UPDATE {current_time}:\n\n"
            
            if trading_mode == "dry_run":
                # Force fresh fetch from database
                positions = dry_run_system.get_open_positions()
                if positions:
                    for pos in positions:
                        pnl_pct = (pos.get('unrealized_pnl', 0) / (pos['entry_price'] * pos['quantity']) * 100) if pos.get('quantity', 0) > 0 else 0
                        emoji = "🟢" if pos.get('unrealized_pnl', 0) >= 0 else "🔴"
                        duration = self._calculate_position_duration(pos.get('entry_time'))
                        current_price = pos.get('current_price', pos.get('entry_price', 0))
                        positions_text += f"{emoji} {pos['symbol']}: {pos['direction']} Entry: ${pos['entry_price']:.6f} Current: ${current_price:.6f} PnL: ${pos.get('unrealized_pnl', 0):.2f} ({pnl_pct:+.2f}%) - {duration}\n"
                else:
                    positions_text += "No open positions in simulation.\n"
            else:
                # Force fresh fetch from database
                positions = real_trade_system.get_open_positions()
                if positions:
                    for pos in positions:
                        pnl_pct = (pos.get('unrealized_pnl', 0) / (pos['entry_price'] * pos['quantity']) * 100) if pos.get('quantity', 0) > 0 else 0
                        emoji = "🟢" if pos.get('unrealized_pnl', 0) >= 0 else "🔴"
                        duration = self._calculate_position_duration(pos.get('entry_time'))
                        current_price = pos.get('current_price', pos.get('entry_price', 0))
                        positions_text += f"{emoji} {pos['symbol']}: {pos['direction']} Entry: ${pos['entry_price']:.6f} Current: ${current_price:.6f} PnL: ${pos.get('unrealized_pnl', 0):.2f} ({pnl_pct:+.2f}%) - {duration}\n"
                else:
                    positions_text += "No open positions in real trading.\n"
            
            return positions_text
            
        except Exception as e:
            return f"Positions data error: {str(e)}"
    
    async def _get_system_analytics(self, trading_mode: str = "dry_run") -> str:
        """Get system analytics and statistics for specific mode"""
        try:
            mode_name = "SIMULATION" if trading_mode == "dry_run" else "REAL TRADING"
            analytics_text = f"SYSTEM ANALYTICS ({mode_name}):\n\n"
            
            # Trading system configuration
            analytics_text += "CONFIGURATION:\n"
            analytics_text += f"- Mode: {mode_name}\n"
            analytics_text += f"- Timeframe: 15 minutes (scalping)\n"
            analytics_text += f"- Max Positions: 20 (optimized for auto trading)\n"
            analytics_text += f"- Scan Interval: 3 minutes\n"
            analytics_text += f"- Position Updates: 30 seconds\n"
            analytics_text += f"- Top Symbols: 100 USDT pairs\n"
            
            # Strategy parameters
            analytics_text += "\nSTRATEGY PARAMETERS:\n"
            analytics_text += f"- EMA Fast/Slow: 5/13\n"
            analytics_text += f"- RSI Length: 9\n"
            analytics_text += f"- TP/SL Multiplier: 0.8x/0.6x ATR\n"
            analytics_text += f"- Max Risk: 1.0% per trade\n"
            analytics_text += f"- Max Leverage: 10x\n"
            
            # Mode-specific information
            if trading_mode == "dry_run":
                analytics_text += "\nSIMULATION FEATURES:\n"
                analytics_text += f"- Virtual balance tracking\n"
                analytics_text += f"- Risk-free testing\n"
                analytics_text += f"- Strategy validation\n"
                analytics_text += f"- Performance analysis\n"
            else:
                analytics_text += "\nREAL TRADING FEATURES:\n"
                analytics_text += f"- Live market execution\n"
                analytics_text += f"- Real money at risk\n"
                analytics_text += f"- Actual P&L impact\n"
                analytics_text += f"- Live position management\n"
            
            # System status
            analytics_text += "\nSYSTEM STATUS:\n"
            analytics_text += f"- Auto Trading: Enabled\n"
            analytics_text += f"- Early Exit System: Active\n"
            analytics_text += f"- Error Notifications: Active\n"
            analytics_text += f"- Dual Interval Monitoring: Active\n"
            analytics_text += f"- AI Reasoning: Active\n"
            
            return analytics_text
            
        except Exception as e:
            return f"System analytics error: {str(e)}"
    
    async def _get_recent_activity(self, trading_mode: str = "dry_run") -> str:
        """Get recent trading activity for specific mode - ALWAYS FRESH DATA"""
        try:
            now = datetime.now()
            cutoff_time = now - timedelta(hours=24)
            current_time = now.strftime('%H:%M:%S')
            
            mode_name = "SIMULATION" if trading_mode == "dry_run" else "REAL TRADING"
            activity_text = f"RECENT ACTIVITY - {mode_name} (24H) - Real-time Update {current_time}:\n\n"
            
            # Get recent closed positions based on mode - FORCE FRESH FETCH
            if trading_mode == "dry_run":
                closed_positions = dry_run_system.get_closed_positions()  # Fresh from DB
            else:
                closed_positions = real_trade_system.get_closed_positions()  # Fresh from DB
            
            recent_trades = []
            
            # Filter recent trades from fresh data
            for pos in closed_positions:
                if pos.get('exit_time'):
                    try:
                        exit_time = datetime.fromisoformat(pos['exit_time'].replace('Z', '+00:00')).replace(tzinfo=None)
                        if exit_time > cutoff_time:
                            recent_trades.append(pos)
                    except:
                        continue
            
            if recent_trades:
                activity_text += f"RECENT TRADES ({len(recent_trades)} total):\n"
                for pos in recent_trades[-10:]:  # Last 10 trades
                    emoji = "🟢" if pos.get('realized_pnl', 0) >= 0 else "🔴"
                    pnl_pct = pos.get('pnl_percentage', 0)
                    duration = self._calculate_position_duration(pos.get('entry_time'), pos.get('exit_time'))
                    entry_price = pos.get('entry_price', 0)
                    exit_price = pos.get('exit_price', 0)
                    activity_text += f"{emoji} {pos['symbol']}: {pos['direction']} Entry: ${entry_price:.6f} Exit: ${exit_price:.6f} PnL: ${pos.get('realized_pnl', 0):.2f} ({pnl_pct:+.2f}%) - {pos.get('exit_reason', 'N/A')} - {duration}\n"
                
                # Summary statistics from fresh data
                total_pnl = sum(pos.get('realized_pnl', 0) for pos in recent_trades)
                winning_trades = len([p for p in recent_trades if p.get('realized_pnl', 0) > 0])
                win_rate = (winning_trades / len(recent_trades) * 100) if recent_trades else 0
                
                activity_text += f"\n24H SUMMARY (Real-time):\n"
                activity_text += f"- Total PnL: ${total_pnl:.2f}\n"
                activity_text += f"- Win Rate: {win_rate:.1f}% ({winning_trades}/{len(recent_trades)})\n"
            else:
                activity_text += f"No recent trading activity in {mode_name.lower()} in the last 24 hours.\n"
            
            return activity_text
            
        except Exception as e:
            return f"Recent activity error: {str(e)}"
    
    def _calculate_position_duration(self, entry_time: str, exit_time: str = None) -> str:
        """Calculate position duration"""
        try:
            if not entry_time:
                return "Unknown duration"
            
            start = datetime.fromisoformat(entry_time.replace('Z', '+00:00')).replace(tzinfo=None)
            end = datetime.fromisoformat(exit_time.replace('Z', '+00:00')).replace(tzinfo=None) if exit_time else datetime.now()
            
            return self._calculate_duration(start, end)
        except:
            return "Unknown duration"
    
    async def _get_detailed_trading_history(self, trading_mode: str = "dry_run", limit: int = 10) -> str:
        """Get detailed trading history with pagination support - ALWAYS FRESH DATA"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S')
            mode_name = "SIMULASI" if trading_mode == "dry_run" else "TRADING NYATA"
            history_text = f"RIWAYAT TRADING DETAIL - {mode_name} (Updated: {current_time}):\n\n"
            
            # Get trading history with limit - FORCE FRESH FETCH
            if trading_mode == "dry_run":
                trades = dry_run_system.get_trade_history(limit)  # Fresh from DB
                total_trades = len(dry_run_system.get_trade_history(1000))  # Fresh count
            else:
                trades = real_trade_system.get_trade_history(limit)  # Fresh from DB
                total_trades = len(real_trade_system.get_trade_history(1000))  # Fresh count
            
            if trades:
                history_text += f"{min(limit, len(trades))} TRADE TERAKHIR (dari total {total_trades} trades):\n"
                
                for i, trade in enumerate(trades):
                    emoji = "🟢" if trade.get('pnl', 0) >= 0 else "🔴"
                    pnl = trade.get('pnl', 0)
                    pnl_pct = trade.get('pnl_percentage', 0)
                    exit_reason = trade.get('exit_reason', 'Unknown')
                    duration = self._calculate_position_duration(
                        trade.get('entry_time'), 
                        trade.get('exit_time')
                    )
                    entry_price = trade.get('entry_price', 0)
                    exit_price = trade.get('exit_price', 0)
                    
                    history_text += f"{i+1}. {emoji} {trade['symbol']} {trade['direction']} - Entry: ${entry_price:.6f} Exit: ${exit_price:.6f} - PnL: ${pnl:.2f} ({pnl_pct:+.2f}%) - {exit_reason} - {duration}\n"
                
                # Calculate statistics for displayed trades - from fresh data
                displayed_pnl = sum(t.get('pnl', 0) for t in trades)
                displayed_wins = len([t for t in trades if t.get('pnl', 0) > 0])
                displayed_win_rate = (displayed_wins / len(trades) * 100) if trades else 0
                
                # Get overall statistics - FRESH DATA
                if trading_mode == "dry_run":
                    all_trades = dry_run_system.get_trade_history(1000)  # Fresh fetch
                else:
                    all_trades = real_trade_system.get_trade_history(1000)  # Fresh fetch
                
                total_pnl = sum(t.get('pnl', 0) for t in all_trades)
                total_wins = len([t for t in all_trades if t.get('pnl', 0) > 0])
                overall_win_rate = (total_wins / len(all_trades) * 100) if all_trades else 0
                
                # Analyze exit reasons from recent trades
                exit_reasons = {}
                for trade in trades:
                    reason = trade.get('exit_reason', 'Unknown')
                    exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
                
                history_text += f"\nSTATISTIK {limit} TRADE TERAKHIR:\n"
                history_text += f"- PnL: ${displayed_pnl:.2f}\n"
                history_text += f"- Win Rate: {displayed_win_rate:.1f}% ({displayed_wins}W/{len(trades)-displayed_wins}L)\n"
                history_text += f"- Exit Reasons: {dict(exit_reasons)}\n"
                
                history_text += f"\nSTATISTIK KESELURUHAN (Real-time):\n"
                history_text += f"- Total Trades: {total_trades}\n"
                history_text += f"- Total PnL: ${total_pnl:.2f}\n"
                history_text += f"- Overall Win Rate: {overall_win_rate:.1f}%\n"
                
                # Best and worst trades from recent - fresh data
                if trades:
                    best_trade = max(trades, key=lambda x: x.get('pnl', 0))
                    worst_trade = min(trades, key=lambda x: x.get('pnl', 0))
                    
                    history_text += f"- Best Recent: {best_trade['symbol']} ${best_trade.get('pnl', 0):.2f}\n"
                    history_text += f"- Worst Recent: {worst_trade['symbol']} ${worst_trade.get('pnl', 0):.2f}\n"
                
                # Pagination info
                if total_trades > limit:
                    remaining = total_trades - limit
                    history_text += f"\n📄 Menampilkan {limit} dari {total_trades} trades (tersisa {remaining} trades lainnya)\n"
                    
            else:
                history_text += "Belum ada riwayat trading.\n"
            
            return history_text
            
        except Exception as e:
            return f"Error mengakses riwayat trading: {str(e)}"
    
    async def _get_comprehensive_symbol_analysis(self, symbol: str, trading_mode: str = "dry_run") -> str:
        """Get comprehensive analysis for a specific symbol - ALWAYS FRESH DATA"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S')
            analysis_text = f"ANALISIS KOMPREHENSIF {symbol} (Real-time Update: {current_time}):\n\n"
            
            # Current market data - FRESH from API
            market_data = await self._get_market_context(symbol)
            analysis_text += f"DATA PASAR SAAT INI:\n{market_data}\n"
            
            # Technical analysis - FRESH from API
            technical_data = await self._get_technical_analysis(symbol)
            analysis_text += f"ANALISIS TEKNIKAL:\n{technical_data}\n"
            
            # Trading history for this symbol - FRESH from DB
            if trading_mode == "dry_run":
                trades = dry_run_system.get_trade_history(50)  # Fresh fetch
            else:
                trades = real_trade_system.get_trade_history(50)  # Fresh fetch
            
            symbol_trades = [t for t in trades if t['symbol'] == symbol]
            
            if symbol_trades:
                analysis_text += f"RIWAYAT TRADING {symbol} (Fresh Data):\n"
                analysis_text += f"- Total Trades: {len(symbol_trades)}\n"
                
                symbol_pnl = sum(t.get('pnl', 0) for t in symbol_trades)
                symbol_wins = len([t for t in symbol_trades if t.get('pnl', 0) > 0])
                symbol_win_rate = (symbol_wins / len(symbol_trades) * 100) if symbol_trades else 0
                
                analysis_text += f"- PnL: ${symbol_pnl:.2f}\n"
                analysis_text += f"- Win Rate: {symbol_win_rate:.1f}%\n"
                
                # Recent trades for this symbol
                recent_symbol_trades = symbol_trades[:5]
                analysis_text += f"- 5 Trade Terakhir:\n"
                for trade in recent_symbol_trades:
                    emoji = "🟢" if trade.get('pnl', 0) >= 0 else "🔴"
                    entry_price = trade.get('entry_price', 0)
                    exit_price = trade.get('exit_price', 0)
                    analysis_text += f"  {emoji} {trade['direction']} Entry: ${entry_price:.6f} Exit: ${exit_price:.6f} PnL: ${trade.get('pnl', 0):.2f} ({trade.get('exit_reason', 'N/A')})\n"
            else:
                analysis_text += f"RIWAYAT TRADING {symbol}: Belum ada trading untuk symbol ini.\n"
            
            # Current position for this symbol - FRESH from DB
            if trading_mode == "dry_run":
                positions = dry_run_system.get_open_positions()  # Fresh fetch
            else:
                positions = real_trade_system.get_open_positions()  # Fresh fetch
            
            symbol_position = next((p for p in positions if p['symbol'] == symbol), None)
            
            if symbol_position:
                pnl_pct = (symbol_position.get('unrealized_pnl', 0) / (symbol_position['entry_price'] * symbol_position['quantity']) * 100) if symbol_position.get('quantity', 0) > 0 else 0
                emoji = "🟢" if symbol_position.get('unrealized_pnl', 0) >= 0 else "🔴"
                current_price = symbol_position.get('current_price', symbol_position.get('entry_price', 0))
                
                analysis_text += f"POSISI TERBUKA {symbol} (Real-time):\n"
                analysis_text += f"{emoji} {symbol_position['direction']} @ ${symbol_position['entry_price']:.6f}\n"
                analysis_text += f"- Current Price: ${current_price:.6f}\n"
                analysis_text += f"- Unrealized PnL: ${symbol_position.get('unrealized_pnl', 0):.2f} ({pnl_pct:+.2f}%)\n"
                analysis_text += f"- Duration: {self._calculate_position_duration(symbol_position.get('entry_time'))}\n"
                analysis_text += f"- TP: ${symbol_position.get('tp_price', 0):.6f}\n"
                analysis_text += f"- SL: ${symbol_position.get('sl_price', 0):.6f}\n"
            else:
                analysis_text += f"POSISI TERBUKA {symbol}: Tidak ada posisi terbuka.\n"
            
            return analysis_text
            
        except Exception as e:
            return f"Error analisis {symbol}: {str(e)}"
    
    async def _get_technical_analysis(self, symbol: str) -> str:
        """Get real-time technical analysis for a symbol using bot's own indicators"""
        try:
            # Get real-time klines data
            klines_response = self.session.get_kline(
                category="linear",
                symbol=symbol,
                interval="15",  # 15-minute timeframe same as bot
                limit=100
            )
            
            if klines_response['retCode'] != 0:
                return f"Tidak dapat mengakses data real-time untuk {symbol}"
            
            klines = klines_response['result']['list']
            if not klines:
                return f"Tidak ada data real-time untuk {symbol}"
            
            # Convert to DataFrame for analysis (same format as bot)
            df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df = df.astype({
                'open': float, 'high': float, 'low': float, 'close': float, 'volume': float
            })
            
            # Reverse order to match bot's data format (oldest first)
            df = df.iloc[::-1].reset_index(drop=True)
            
            technical_text = f"ANALISIS TEKNIKAL REAL-TIME {symbol}:\n"
            
            try:
                # Calculate same indicators as trading bot
                current_price = df['close'].iloc[-1]
                
                # EMA 5 and 13 (same as bot configuration)
                ema_fast = df['close'].ewm(span=5, adjust=False).mean()
                ema_slow = df['close'].ewm(span=13, adjust=False).mean()
                ema_fast_val = ema_fast.iloc[-1]
                ema_slow_val = ema_slow.iloc[-1]
                
                technical_text += f"- Harga Saat Ini: ${current_price:.6f}\n"
                technical_text += f"- EMA Fast (5): ${ema_fast_val:.6f}\n"
                technical_text += f"- EMA Slow (13): ${ema_slow_val:.6f}\n"
                technical_text += f"- EMA Trend: {'🟢 Bullish' if ema_fast_val > ema_slow_val else '🔴 Bearish'}\n"
                
                # RSI 9 (same as bot)
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=9).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=9).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                rsi_val = rsi.iloc[-1]
                
                technical_text += f"- RSI (9): {rsi_val:.2f}\n"
                if rsi_val > 65:
                    rsi_status = "🔴 Overbought"
                elif rsi_val < 35:
                    rsi_status = "🟢 Oversold"
                else:
                    rsi_status = "🟡 Neutral"
                technical_text += f"- RSI Status: {rsi_status}\n"
                
                # MACD (5, 13, 4 - same as bot)
                ema_fast_macd = df['close'].ewm(span=5, adjust=False).mean()
                ema_slow_macd = df['close'].ewm(span=13, adjust=False).mean()
                macd_line = ema_fast_macd - ema_slow_macd
                signal_line = macd_line.ewm(span=4, adjust=False).mean()
                macd_val = macd_line.iloc[-1]
                signal_val = signal_line.iloc[-1]
                
                technical_text += f"- MACD Line: {macd_val:.8f}\n"
                technical_text += f"- Signal Line: {signal_val:.8f}\n"
                technical_text += f"- MACD Signal: {'🟢 Bullish' if macd_val > signal_val else '🔴 Bearish'}\n"
                
                # ATR (14 - same as bot)
                high = df['high']
                low = df['low']
                close = df['close']
                
                tr1 = high - low
                tr2 = abs(high - close.shift(1))
                tr3 = abs(low - close.shift(1))
                true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                atr = true_range.rolling(window=14).mean()
                atr_val = atr.iloc[-1]
                
                technical_text += f"- ATR (14): {atr_val:.8f}\n"
                
                # Calculate TP/SL levels (same as bot)
                tp_distance = atr_val * 0.8  # TP_ATR_MULT
                sl_distance = atr_val * 0.6  # SL_ATR_MULT
                
                # For LONG positions
                long_tp = current_price + tp_distance
                long_sl = current_price - sl_distance
                
                # For SHORT positions  
                short_tp = current_price - tp_distance
                short_sl = current_price + sl_distance
                
                technical_text += f"\nLEVEL TRADING:\n"
                technical_text += f"- LONG TP: ${long_tp:.6f} (+{tp_distance:.6f})\n"
                technical_text += f"- LONG SL: ${long_sl:.6f} (-{sl_distance:.6f})\n"
                technical_text += f"- SHORT TP: ${short_tp:.6f} (-{tp_distance:.6f})\n"
                technical_text += f"- SHORT SL: ${short_sl:.6f} (+{sl_distance:.6f})\n"
                
                # Volume analysis
                volume_avg = df['volume'].tail(20).mean()
                volume_current = df['volume'].iloc[-1]
                volume_ratio = volume_current / volume_avg if volume_avg > 0 else 1
                
                technical_text += f"\nVOLUME & MOMENTUM:\n"
                technical_text += f"- Volume Ratio: {volume_ratio:.2f}x\n"
                technical_text += f"- Volume Status: {'🟢 Tinggi' if volume_ratio > 1.5 else '🟡 Normal' if volume_ratio > 0.5 else '🔴 Rendah'}\n"
                
                # Price levels (24h)
                high_24h = df['high'].tail(96).max() if len(df) >= 96 else df['high'].max()
                low_24h = df['low'].tail(96).min() if len(df) >= 96 else df['low'].min()
                price_change_24h = ((current_price - df['close'].iloc[-96]) / df['close'].iloc[-96] * 100) if len(df) >= 96 else 0
                
                technical_text += f"- 24h High: ${high_24h:.6f}\n"
                technical_text += f"- 24h Low: ${low_24h:.6f}\n"
                technical_text += f"- 24h Change: {price_change_24h:+.2f}%\n"
                
                # Trading signals summary (same logic as bot)
                signals = []
                signal_strength = 0
                
                # EMA signal
                if ema_fast_val > ema_slow_val:
                    signals.append("✅ EMA: Trend bullish")
                    signal_strength += 1
                else:
                    signals.append("❌ EMA: Trend bearish")
                
                # RSI signal
                if 35 <= rsi_val <= 65:
                    signals.append("✅ RSI: Zona trading")
                    signal_strength += 1
                elif rsi_val < 35:
                    signals.append("🟢 RSI: Oversold (buy signal)")
                    signal_strength += 1
                elif rsi_val > 65:
                    signals.append("🔴 RSI: Overbought (sell signal)")
                    signal_strength += 1
                
                # MACD signal
                if macd_val > signal_val:
                    signals.append("✅ MACD: Momentum bullish")
                    signal_strength += 1
                else:
                    signals.append("❌ MACD: Momentum bearish")
                
                # Volume confirmation
                if volume_ratio > 1.2:
                    signals.append("✅ Volume: Konfirmasi kuat")
                    signal_strength += 1
                
                technical_text += f"\nRINGKASAN SINYAL:\n"
                for signal in signals:
                    technical_text += f"- {signal}\n"
                
                # Overall assessment
                if signal_strength >= 3:
                    overall = "🟢 KUAT"
                elif signal_strength >= 2:
                    overall = "🟡 SEDANG"
                else:
                    overall = "🔴 LEMAH"
                
                technical_text += f"\nKESIMPULAN: Sinyal {overall} ({signal_strength}/4 indikator positif)\n"
                
            except Exception as e:
                technical_text += f"Error menghitung indikator: {str(e)}\n"
            
            return technical_text
            
        except Exception as e:
            return f"Error analisis teknikal real-time {symbol}: {str(e)}"
    
    async def _get_basic_technical_analysis(self, symbol: str) -> str:
        """Fallback basic technical analysis if bot functions not available"""
        try:
            # Get klines data for technical analysis
            klines_response = self.session.get_kline(
                category="linear",
                symbol=symbol,
                interval="15",  # 15 minutes
                limit=100
            )
            
            if klines_response['retCode'] != 0:
                return f"Tidak dapat mengakses data teknikal untuk {symbol}"
            
            klines = klines_response['result']['list']
            if not klines:
                return f"Tidak ada data teknikal untuk {symbol}"
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df = df.astype({
                'open': float, 'high': float, 'low': float, 'close': float, 'volume': float
            })
            
            # Calculate technical indicators
            closes = df['close'].values
            highs = df['high'].values
            lows = df['low'].values
            volumes = df['volume'].values
            
            # Simple Moving Averages
            sma_20 = np.mean(closes[-20:]) if len(closes) >= 20 else closes[-1]
            sma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else closes[-1]
            
            # EMA (approximation)
            ema_12 = closes[-1]  # Simplified
            ema_26 = np.mean(closes[-26:]) if len(closes) >= 26 else closes[-1]
            
            # RSI (simplified)
            if len(closes) >= 14:
                price_changes = np.diff(closes[-15:])
                gains = np.where(price_changes > 0, price_changes, 0)
                losses = np.where(price_changes < 0, -price_changes, 0)
                avg_gain = np.mean(gains) if len(gains) > 0 else 0
                avg_loss = np.mean(losses) if len(losses) > 0 else 0.001
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            else:
                rsi = 50
            
            # Volatility
            volatility = np.std(closes[-20:]) / np.mean(closes[-20:]) * 100 if len(closes) >= 20 else 0
            
            # Volume analysis
            avg_volume = np.mean(volumes[-20:]) if len(volumes) >= 20 else volumes[-1]
            current_volume = volumes[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Price levels
            current_price = closes[-1]
            high_24h = np.max(highs[-96:]) if len(highs) >= 96 else current_price  # 24h = 96 * 15min
            low_24h = np.min(lows[-96:]) if len(lows) >= 96 else current_price
            
            technical_text = f"""
INDIKATOR TEKNIKAL (Basic):
- Harga Saat Ini: ${current_price:.6f}
- SMA 20: ${sma_20:.6f}
- SMA 50: ${sma_50:.6f}
- EMA 12: ${ema_12:.6f}
- RSI (14): {rsi:.1f}
- Volatilitas: {volatility:.2f}%
- Volume Ratio: {volume_ratio:.2f}x
- 24h High: ${high_24h:.6f}
- 24h Low: ${low_24h:.6f}

ANALISIS:
- Trend: {'Bullish' if current_price > sma_20 else 'Bearish'}
- RSI Status: {'Overbought' if rsi > 70 else 'Oversold' if rsi < 30 else 'Neutral'}
- Volume: {'High' if volume_ratio > 1.5 else 'Normal' if volume_ratio > 0.5 else 'Low'}
- Volatilitas: {'Tinggi' if volatility > 5 else 'Sedang' if volatility > 2 else 'Rendah'}
"""
            
            return technical_text
            
        except Exception as e:
            return f"Error analisis teknikal {symbol}: {str(e)}"
    
    async def _get_market_technical_overview(self) -> str:
        """Get technical overview of major market pairs"""
        try:
            major_pairs = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'SOLUSDT', 'DOGEUSDT']
            overview_text = "RINGKASAN TEKNIKAL PASAR UTAMA:\n\n"
            
            for symbol in major_pairs:
                try:
                    # Get basic technical data
                    ticker_response = self.session.get_tickers(category="linear", symbol=symbol)
                    if ticker_response['retCode'] == 0:
                        ticker = ticker_response['result']['list'][0]
                        price = float(ticker['lastPrice'])
                        change_24h = float(ticker['price24hPcnt']) * 100
                        volume = float(ticker['volume24h'])
                        
                        emoji = "🟢" if change_24h >= 0 else "🔴"
                        overview_text += f"{emoji} {symbol}: ${price:.6f} ({change_24h:+.2f}%) Vol: ${volume:,.0f}\n"
                except:
                    overview_text += f"⚠️ {symbol}: Data tidak tersedia\n"
            
            return overview_text
            
        except Exception as e:
            return f"Error ringkasan teknikal: {str(e)}"

# Global instance
gemini_analyst = None

def get_gemini_analyst():
    """Get or create Gemini analyst instance"""
    global gemini_analyst
    if gemini_analyst is None:
        try:
            gemini_analyst = GeminiMarketAnalyst()
        except Exception as e:
            print(f"❌ Failed to initialize Gemini AI: {e}")
            return None
    return gemini_analyst

# Test function
async def test_gemini_integration():
    """Test Gemini AI integration"""
    print("🧪 Testing Gemini AI Integration...")
    
    try:
        analyst = get_gemini_analyst()
        if not analyst:
            print("❌ Failed to initialize Gemini analyst")
            return
        
        # Test market overview
        print("\n📊 Testing market analysis...")
        market_analysis = await analyst.analyze_market_conditions()
        print(f"Market Analysis: {market_analysis[:100]}...")
        
        # Test chat
        print("\n💬 Testing chat functionality...")
        chat_response = await analyst.chat_with_market_data("What's the current Bitcoin price?")
        print(f"Chat Response: {chat_response[:100]}...")
        
        print("✅ Gemini AI integration test completed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini_integration())