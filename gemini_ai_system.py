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
    # Import technical analysis functions directly
    try:
        import pandas as pd
        import numpy as np
        import aiohttp
        
        def calculate_ema(data, period):
            """Calculate Exponential Moving Average"""
            if not data or len(data) < period:
                return []
            
            df = pd.Series(data)
            ema = df.ewm(span=period).mean()
            return ema.tolist()
        
        def calculate_rsi(data, period=14):
            """Calculate Relative Strength Index"""
            if not data or len(data) < period + 1:
                return []
            
            df = pd.Series(data)
            delta = df.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.fillna(50).tolist()
        
        def calculate_atr(high, low, close, period=14):
            """Calculate Average True Range"""
            if not high or not low or not close or len(close) < period:
                return []
            
            high_series = pd.Series(high)
            low_series = pd.Series(low)
            close_series = pd.Series(close)
            
            tr1 = high_series - low_series
            tr2 = abs(high_series - close_series.shift())
            tr3 = abs(low_series - close_series.shift())
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean()
            return atr.fillna(0).tolist()
        
        def calculate_macd(data, fast=12, slow=26, signal=9):
            """Calculate MACD"""
            if not data or len(data) < slow:
                return [], [], []
            
            df = pd.Series(data)
            ema_fast = df.ewm(span=fast).mean()
            ema_slow = df.ewm(span=slow).mean()
            
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            
            return macd_line.fillna(0).tolist(), signal_line.fillna(0).tolist(), histogram.fillna(0).tolist()
        
        async def get_klines(symbol, interval='1m', limit=100):
            """Get klines data from Bybit"""
            try:
                url = "https://api.bybit.com/v5/market/kline"
                params = {
                    'category': 'linear',
                    'symbol': symbol,
                    'interval': interval,
                    'limit': limit
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('retCode') == 0:
                                klines = data.get('result', {}).get('list', [])
                                # Convert to format: [timestamp, open, high, low, close, volume]
                                formatted_klines = []
                                for kline in reversed(klines):  # Bybit returns newest first
                                    formatted_klines.append([
                                        int(kline[0]),      # timestamp
                                        float(kline[1]),    # open
                                        float(kline[2]),    # high
                                        float(kline[3]),    # low
                                        float(kline[4]),    # close
                                        float(kline[5])     # volume
                                    ])
                                return formatted_klines
                return []
            except Exception as e:
                print(f"❌ Error getting klines for {symbol}: {e}")
                return []
        
        print("✅ Using standalone technical analysis functions")
        
    except ImportError as e:
        print(f"❌ Could not import required libraries for technical analysis: {e}")
        print("   Please install: pip install pandas numpy aiohttp")
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
        self.max_tokens = int(os.getenv('GEMINI_MAX_TOKENS', '2000'))
        
        # Configure Gemini with first API key
        genai.configure(api_key=self.api_keys[0])
        self.model = genai.GenerativeModel(self.model_name)
        
        # Bybit session for real market data
        self.session = HTTP(
            testnet=False,
            api_key=os.getenv('BYBIT_API_KEY', ''),
            api_secret=os.getenv('BYBIT_API_SECRET', ''),
            domain="bytick"
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
        """Generate AI reasoning for position entry in Indonesian — supports all 5 strategies"""
        try:
            symbol        = signal_data['symbol']
            direction     = signal_data['direction']
            strategy      = signal_data.get('strategy', 'ICT_SMC')
            strategy_label= signal_data.get('strategy_label', '📐 ICT/SMC')
            setup_type    = signal_data.get('setup_type', 'ICT')
            session       = signal_data.get('session', 'N/A')
            rr            = signal_data.get('rr_ratio', 0)
            atr           = signal_data.get('atr_value', 0)
            entry         = signal_data.get('close', 0)
            tp            = signal_data.get('tp', 0)
            sl            = signal_data.get('sl', 0)
            leverage      = signal_data.get('leverage', 'N/A')
            ict_score     = signal_data.get('ict_score', 0)

            # ── Build strategy-specific context block ──────────────────────────
            if strategy == 'ICT_SMC':
                pd_zone    = signal_data.get('pd_zone', 'N/A')
                fib_pct    = signal_data.get('fib_position_pct', 0)
                bos        = signal_data.get('bos_confirmed', False)
                choch      = signal_data.get('choch_detected', False)
                in_ob      = signal_data.get('in_order_block', False)
                in_fvg     = signal_data.get('in_fvg', False)
                liq        = signal_data.get('liquidity_confirmed', False)
                kz         = signal_data.get('kill_zone_active', False)
                bias_dir   = signal_data.get('bias', 'N/A')
                bos_bull   = signal_data.get('bos_bull', False)
                bos_bear   = signal_data.get('bos_bear', False)
                choch_bull = signal_data.get('choch_bull', False)
                choch_bear = signal_data.get('choch_bear', False)
                ssl_swept  = signal_data.get('ssl_swept', False)
                bsl_swept  = signal_data.get('bsl_swept', False)
                confirmators = signal_data.get('confirmators', [])

                checks = [
                    f"{'✅' if bos or bos_bull or bos_bear else '❌'} BOS: {'Bullish' if bos_bull else 'Bearish' if bos_bear else 'Tidak ada'}",
                    f"{'✅' if choch or choch_bull or choch_bear else '❌'} CHoCH: {'Bullish' if choch_bull else 'Bearish' if choch_bear else 'Tidak ada'}",
                    f"{'✅' if in_ob else '❌'} Order Block: {'Aktif' if in_ob else 'Tidak di OB'}",
                    f"{'✅' if in_fvg else '❌'} Fair Value Gap: {'Aktif' if in_fvg else 'Tidak di FVG'}",
                    f"{'✅' if liq else '❌'} Liquidity Sweep: {'SSL swept' if ssl_swept else 'BSL swept' if bsl_swept else 'Tidak ada'}",
                    f"{'✅' if kz else '❌'} Kill Zone: {'Aktif' if kz else 'Di luar'}",
                    f"PD Zone: {pd_zone} ({fib_pct:.0f}% Fib) | Bias: {bias_dir} | Score: {ict_score}/11",
                    f"Konfirmator: {', '.join(confirmators) if confirmators else 'Tidak ada'}",
                ]
                strategy_instructions = "Konfirmasi ICT/SMC (Scalping 15m/5m/1m):\n" + '\n'.join(checks)

            elif strategy == 'MEAN_REVERSION':
                z_score = signal_data.get('z_score', 0)
                bb_pos  = signal_data.get('bb_position', 'N/A')
                strategy_instructions = f"Konfirmasi Mean Reversion: Z-Score={z_score} | BB Position={bb_pos} | Score={ict_score}/5"

            elif strategy == 'TREND_FOLLOW':
                st_dir   = signal_data.get('supertrend_dir', 'N/A')
                htf_bias = signal_data.get('htf_bias', 'N/A')
                strategy_instructions = f"Konfirmasi Trend Following: Supertrend={st_dir} | HTF Bias={htf_bias} | Score={ict_score}/5"

            elif strategy == 'FUNDING_RATE':
                funding = signal_data.get('funding_rate', 0)
                fr_bias = signal_data.get('funding_bias', 'N/A')
                strategy_instructions = f"Konfirmasi Funding Rate: Rate={funding:.4f}% | Bias={fr_bias} | Score={ict_score}/5"

            elif strategy == 'ORDERFLOW':
                cvd_norm  = signal_data.get('cvd_normalized', 0)
                price_roc = signal_data.get('price_roc', 0)
                strategy_instructions = f"Konfirmasi Orderflow/CVD: CVD Normalized={cvd_norm} | Price ROC={price_roc:.2f}% | Score={ict_score}/5"

            else:
                strategy_instructions = f"Setup: {setup_type} | Score: {ict_score}"

            # ── Final prompt ───────────────────────────────────────────────────
            prompt = f"""Tulis analisis entry trade berikut dalam 1-2 kalimat singkat bahasa Indonesia. Langsung ke poin, padat, seperti trader senior yang kasih konfirmasi cepat ke rekannya. Gunakan <b> untuk istilah teknikal penting saja.

=== DATA TRADE ===
Symbol: {symbol} | Arah: {direction} | Strategy: {strategy_label}
Setup: {setup_type} | Sesi: {session} | Leverage: {leverage}x
Entry: ${entry:.6f} | TP: ${tp:.6f} | SL: ${sl:.6f}
R:R: {rr:.2f} | ATR: {atr:.6f}

{strategy_instructions}

OUTPUT: Maksimal 2 kalimat HTML. Tidak ada bullet point, tidak ada heading. Langsung narasi."""

            response = await self._generate_response(prompt)
            return response

        except Exception as e:
            print(f"❌ Error generating entry reasoning: {e}")
            raise Exception(f"Entry reasoning failed: {e}")
    
    async def _get_indicator_analysis(self, symbol: str, direction: str) -> str:
        """Get simple indicator analysis without database queries"""
        try:
            # Simple analysis based on current market conditions only
            analysis_text = f"ANALISIS INDIKATOR UNTUK {symbol} {direction}:\n\n"
            analysis_text += f"📊 ANALISIS TEKNIKAL REAL-TIME:\n"
            analysis_text += f"   - Symbol: {symbol}\n"
            analysis_text += f"   - Direction: {direction}\n"
            analysis_text += f"   - Analisis berdasarkan kondisi pasar saat ini\n"
            analysis_text += f"   - Indikator teknikal menunjukkan sinyal {direction}\n\n"
            
            return analysis_text
            
        except Exception as e:
            print(f"❌ Error getting indicator analysis: {e}")
            return f"Analisis indikator tidak tersedia: {str(e)}"
    
    async def _get_market_data_analysis(self, symbol: str, direction: str) -> str:
        """Get simple market data analysis without database queries"""
        try:
            # Try to get current market data directly
            try:
                from market_data_system import get_market_data_system
                market_system = get_market_data_system()
                current_market_data = await market_system.get_market_data(symbol)
                
                if current_market_data and current_market_data.get('market_cap', 0) > 0:
                    market_cap = current_market_data.get('market_cap', 0)
                    volume_24h = current_market_data.get('total_volume_24h', 0)
                    price_change_24h = current_market_data.get('price_change_percentage_24h', 0)
                    
                    # Categorize
                    if market_cap > 5_000_000_000:
                        mc_category = "🟢 BESAR"
                    elif market_cap > 1_000_000_000:
                        mc_category = "🟡 MENENGAH"
                    else:
                        mc_category = "🔴 KECIL"
                    
                    if volume_24h > 500_000_000:
                        vol_category = "🟢 KOIN BESAR"
                    elif volume_24h > 100_000_000:
                        vol_category = "🟡 MENENGAH"
                    else:
                        vol_category = "🔴 KOIN KECIL"
                    
                    analysis_text = f"MARKET DATA REAL-TIME {symbol}:\n\n"
                    analysis_text += f"📊 CURRENT METRICS:\n"
                    analysis_text += f"   - Market Cap: ${market_cap:,.0f} {mc_category}\n"
                    analysis_text += f"   - 24h Volume: ${volume_24h:,.0f} {vol_category}\n"
                    analysis_text += f"   - 24h Change: {price_change_24h:.2f}%\n\n"
                    
                    # Risk assessment
                    analysis_text += f"🚨 RISK ASSESSMENT:\n"
                    if volume_24h < 100_000_000:
                        analysis_text += f"   ⚠️ Low volume - potential slippage risk\n"
                    if market_cap < 1_000_000_000:
                        analysis_text += f"   ⚠️ Small market cap - higher volatility\n"
                    if abs(price_change_24h) > 10:
                        analysis_text += f"   ⚠️ High 24h volatility ({price_change_24h:.1f}%)\n"
                    
                    if volume_24h >= 100_000_000 and market_cap >= 1_000_000_000 and abs(price_change_24h) <= 10:
                        analysis_text += f"   ✅ Market conditions appear favorable\n"
                    
                    return analysis_text
                else:
                    raise Exception("No market data available")
                    
            except Exception as e:
                print(f"⚠️ Could not get market data: {e}")
                # Fallback to simple analysis
                analysis_text = f"MARKET ANALYSIS {symbol}:\n\n"
                analysis_text += f"📊 BASIC ANALYSIS:\n"
                analysis_text += f"   - Symbol: {symbol}\n"
                analysis_text += f"   - Direction: {direction}\n"
                analysis_text += f"   - Market data: Menggunakan analisis teknikal\n"
                analysis_text += f"   - Risk level: Standard untuk crypto trading\n\n"
                
                return analysis_text
            
        except Exception as e:
            print(f"❌ Error getting market data analysis: {e}")
            return f"Market analysis: Berdasarkan kondisi pasar umum crypto"
    
    async def _get_stored_market_data_analysis(self, position_data: Dict) -> str:
        """Get market data analysis using stored data from when position was opened"""
        try:
            analysis_text = f"MARKET DATA SAAT ENTRY {position_data['symbol']}:\n\n"
            
            # Extract stored market data from position_data if available
            market_cap = position_data.get('market_cap', 0)
            market_cap_category = position_data.get('market_cap_category', 'Unknown')
            volume_category = position_data.get('volume_category', 'Unknown')
            liquidity_score = position_data.get('liquidity_score', 0)
            volatility_score = position_data.get('volatility_score', 0)
            market_dominance = position_data.get('market_dominance', 0)
            total_volume_24h = position_data.get('total_volume_24h', 0)
            
            if market_cap > 0:  # If we have stored market data
                analysis_text += f"📊 MARKET CONDITIONS SAAT ENTRY:\n"
                analysis_text += f"   - Market Cap: ${market_cap:,.0f} ({market_cap_category})\n"
                analysis_text += f"   - 24h Volume: ${total_volume_24h:,.0f} ({volume_category})\n"
                analysis_text += f"   - Liquidity Score: {liquidity_score:.1f}\n"
                analysis_text += f"   - Volatility Score: {volatility_score:.1f}\n"
                analysis_text += f"   - Market Dominance: {market_dominance:.1f}%\n\n"
                
                # Risk factors that were present at entry
                analysis_text += f"🚨 KONDISI RISIKO SAAT ENTRY:\n"
                
                risk_factors = []
                if volatility_score > 10.0:
                    risk_factors.append("Very high volatility - risiko tinggi")
                elif volatility_score > 5.0:
                    risk_factors.append("High volatility - risiko sedang")
                
                if liquidity_score < 5.0:
                    risk_factors.append("Low liquidity - potensi slippage")
                elif liquidity_score < 10.0:
                    risk_factors.append("Medium liquidity - perlu hati-hati")
                
                if market_cap_category in ['Micro Cap', 'Nano Cap']:
                    risk_factors.append("Small market cap - risiko manipulasi tinggi")
                elif market_cap_category == 'Small Cap':
                    risk_factors.append("Small cap - volatilitas tinggi")
                
                if volume_category in ['Low Volume', 'Very Low Volume']:
                    risk_factors.append("Low trading volume - sulit exit")
                
                if risk_factors:
                    for factor in risk_factors:
                        analysis_text += f"   ⚠️ {factor}\n"
                else:
                    analysis_text += f"   ✅ Kondisi market favorable saat entry\n"
                
                # Market category assessment
                analysis_text += f"\n💡 ASSESSMENT KATEGORI:\n"
                if market_cap_category == 'Large Cap':
                    analysis_text += f"   - Large cap: Stabil, likuiditas tinggi, risiko rendah\n"
                elif market_cap_category == 'Mid Cap':
                    analysis_text += f"   - Mid cap: Balance risk-reward, volatilitas sedang\n"
                elif market_cap_category == 'Small Cap':
                    analysis_text += f"   - Small cap: High risk high reward, volatilitas tinggi\n"
                else:
                    analysis_text += f"   - {market_cap_category}: Risiko sangat tinggi, perlu extra hati-hati\n"
                
                if volume_category in ['Very High Volume', 'High Volume']:
                    analysis_text += f"   - Volume tinggi: Mudah entry/exit, spread ketat\n"
                elif volume_category == 'Medium Volume':
                    analysis_text += f"   - Volume sedang: Cukup likuid untuk trading normal\n"
                else:
                    analysis_text += f"   - Volume rendah: Hati-hati dengan slippage dan exit\n"
                
            else:
                analysis_text += f"📊 MARKET DATA: Tidak tersedia saat entry\n"
                analysis_text += f"   (Data market cap dan volume tidak disimpan)\n\n"
            
            return analysis_text
            
        except Exception as e:
            print(f"❌ Error getting stored market data analysis: {e}")
            return f"Analisis market data tidak tersedia: {str(e)}"
    
    async def analyze_symbol_realtime(self, symbol: str, direction: str = None) -> str:
        """
        Analisis real-time untuk symbol tertentu
        Menggunakan data market terkini dari API
        """
        try:
            from ai_analysis_system_simple import get_realtime_market_analysis
            
            analysis = get_realtime_market_analysis(symbol)
            
            if not analysis.get('success'):
                return f"Error dalam analisis real-time: {analysis.get('error', 'Unknown error')}"
            
            # Format analysis untuk AI response
            prompt = f"""
            Berikan analisis real-time untuk {symbol} dalam bahasa Indonesia:
            
            DATA MARKET SAAT INI:
            - Market Cap: ${analysis['market_cap']:,.0f} ({analysis['market_cap_category']})
            - Volume 24h: ${analysis['volume_24h']:,.0f} ({analysis['volume_category']})
            - Liquidity Score: {analysis['liquidity_score']:.1f}
            - Volatility Score: {analysis['volatility_score']:.1f}
            - Market Dominance: {analysis['market_dominance']:.1f}%
            
            PERFORMA HISTORIS:
            {f"Total Trades: {analysis['historical_performance'].get('total_trades', 0)}, Win Rate: {analysis['historical_performance'].get('win_rate', 0):.1f}%" if analysis['historical_performance'] else "Belum ada data historis"}
            
            Berikan analisis komprehensif dalam format HTML dengan:
            <b>1. Kondisi Market Saat Ini:</b> Jelaskan kondisi market cap, volume, dan volatilitas<br><br>
            <b>2. Analisis Historis:</b> Bagaimana performa trading symbol ini sebelumnya<br><br>
            <b>3. Assessment Risiko:</b> Tingkat risiko berdasarkan kondisi market saat ini<br><br>
            <b>4. Rekomendasi Trading:</b> Apakah layak untuk trading dan strategi yang disarankan<br><br>
            <b>5. Timing dan Entry:</b> Kapan waktu terbaik untuk entry dan exit
            
            Gunakan bahasa Indonesia yang jelas, maksimal 350 kata.
            """
            
            response = await self._generate_response(prompt)
            return response
            
        except Exception as e:
            print(f"❌ Error in realtime symbol analysis: {e}")
            return f"Analisis real-time tidak tersedia: {str(e)}"
    
    async def analyze_trade_history(self, symbol: str = None, trade_id: str = None, 
                                  mode: str = "dry_run", limit: int = 5) -> str:
        """
        Analisis historical trades dengan data yang tersimpan
        Menampilkan indikator dan kondisi market saat trade dibuka/ditutup
        """
        try:
            from ai_analysis_system_simple import get_historical_trades_analysis, analyze_indicator_performance
            
            # Get trades analysis
            if symbol:
                trades_analysis = get_historical_trades_analysis(symbol, limit, mode)
            else:
                trades_analysis = get_historical_trades_analysis(None, limit, mode)
            
            if not trades_analysis or (len(trades_analysis) == 1 and 'error' in trades_analysis[0]):
                return f"Tidak ada data historical trades yang ditemukan untuk {symbol or 'semua symbol'}"
            
            # Get indicator performance analysis
            indicator_performance = analyze_indicator_performance(mode, 30)
            
            # Format analysis untuk AI response
            trades_summary = []
            
            for trade in trades_analysis:
                if 'error' in trade:
                    continue
                    
                trade_summary = f"""
                {trade['symbol']} {trade['direction']}:
                - Result: {'PROFIT' if trade['is_profitable'] else 'LOSS'} {trade['pnl_percentage']:.2f}%
                - Exit: {trade['exit_reason']}
                - Pass Rate: {trade['pass_rate']:.1f}% ({trade['passed_indicators_count']}/{trade['passed_indicators_count'] + trade['failed_indicators_count']} indicators)
                - Market: {trade['market_cap_category']} cap, {trade['volume_category']} volume
                - Passed: {', '.join(trade['passed_indicators'][:3])}{'...' if len(trade['passed_indicators']) > 3 else ''}
                - Failed: {', '.join(trade['failed_indicators'][:3])}{'...' if len(trade['failed_indicators']) > 3 else ''}
                """
                trades_summary.append(trade_summary)
            
            # Top performing indicators
            top_indicators = ""
            if indicator_performance.get('success') and indicator_performance['indicator_performance']:
                top_3 = indicator_performance['indicator_performance'][:3]
                top_indicators = f"""
                TOP PERFORMING INDICATORS:
                {chr(10).join([f"- {ind['indicator_name']}: {ind['effectiveness_score']:.1f} score ({ind['win_rate_when_passed']:.1f}% win rate when passed)" for ind in top_3])}
                """
            
            prompt = f"""
            Analisis historical trades berikut dalam bahasa Indonesia:
            
            MODE: {mode.upper()}
            SYMBOL: {symbol or 'SEMUA SYMBOL'}
            TOTAL TRADES ANALYZED: {len(trades_analysis)}
            
            DETAIL TRADES:
            {''.join(trades_summary)}
            
            {top_indicators}
            
            Berikan analisis mendalam dalam format HTML dengan:
            <b>1. Overview Performa:</b> Ringkasan hasil trading secara keseluruhan<br><br>
            <b>2. Analisis Indikator:</b> Indikator mana yang paling sering berhasil dan gagal<br><br>
            <b>3. Kondisi Market Optimal:</b> Pada kondisi market seperti apa trading paling berhasil<br><br>
            <b>4. Pattern Recognition:</b> Pola-pola yang terlihat dari data historis<br><br>
            <b>5. Rekomendasi Perbaikan:</b> Saran untuk meningkatkan performa trading
            
            Fokus pada insight praktis yang bisa digunakan untuk trading selanjutnya.
            Gunakan bahasa Indonesia yang jelas, maksimal 400 kata.
            """
            
            response = await self._generate_response(prompt)
            return response
            
        except Exception as e:
            print(f"❌ Error in trade history analysis: {e}")
            return f"Analisis historical trades tidak tersedia: {str(e)}"
    
    async def analyze_open_positions(self, symbol: str = None, position_id: str = None, 
                                   mode: str = "dry_run") -> str:
        """
        Analisis posisi yang masih terbuka dengan data saat dibuka
        """
        try:
            from ai_analysis_system_simple import get_open_positions_analysis
            
            positions_analysis = get_open_positions_analysis(symbol, mode)
            
            if not positions_analysis or (len(positions_analysis) == 1 and 'error' in positions_analysis[0]):
                return f"Tidak ada posisi terbuka yang ditemukan untuk {symbol or 'semua symbol'}"
            
            # Format analysis untuk AI response
            positions_summary = []
            
            for position in positions_analysis:
                if 'error' in position:
                    continue
                    
                position_summary = f"""
                {position['symbol']} {position['direction']}:
                - Current PnL: {position['pnl_percentage']:.2f}%
                - Entry: ${position['entry_price']:.4f}, Current: ${position['current_price']:.4f}
                - Pass Rate: {position['pass_rate']:.1f}% ({position['passed_indicators_count']}/{position['passed_indicators_count'] + position['failed_indicators_count']} indicators)
                - Market saat Entry: {position['market_cap_category']} cap, {position['volume_category']} volume
                - Passed: {', '.join(position['passed_indicators'][:3])}{'...' if len(position['passed_indicators']) > 3 else ''}
                - Failed: {', '.join(position['failed_indicators'][:3])}{'...' if len(position['failed_indicators']) > 3 else ''}
                """
                positions_summary.append(position_summary)
            
            prompt = f"""
            Analisis posisi terbuka berikut dalam bahasa Indonesia:
            
            MODE: {mode.upper()}
            SYMBOL: {symbol or 'SEMUA SYMBOL'}
            TOTAL POSITIONS: {len(positions_analysis)}
            
            DETAIL POSITIONS:
            {''.join(positions_summary)}
            
            Berikan analisis mendalam dalam format HTML dengan:
            <b>1. Status Posisi:</b> Kondisi current dari setiap posisi (profit/loss, durasi)<br><br>
            <b>2. Kualitas Entry:</b> Seberapa baik kondisi saat entry (indikator, market conditions)<br><br>
            <b>3. Risk Assessment:</b> Tingkat risiko current dan faktor-faktor yang mempengaruhi<br><br>
            <b>4. Action Plan:</b> Apa yang harus dilakukan untuk setiap posisi (hold, close, adjust SL/TP)<br><br>
            <b>5. Learning Points:</b> Pelajaran dari posisi ini untuk trading selanjutnya
            
            Berikan rekomendasi spesifik dan actionable untuk setiap posisi.
            Gunakan bahasa Indonesia yang jelas, maksimal 400 kata.
            """
            
            response = await self._generate_response(prompt)
            return response
            
        except Exception as e:
            print(f"❌ Error in open positions analysis: {e}")
            return f"Analisis posisi terbuka tidak tersedia: {str(e)}"
    
    async def generate_exit_reasoning(self, position_data: Dict, exit_reason: str) -> str:
        """Generate comprehensive AI reasoning for position exit in Indonesian"""
        try:
            symbol        = position_data['symbol']
            direction     = position_data['direction']
            entry_price   = position_data['entry_price']
            exit_price    = position_data['exit_price']
            pnl           = position_data.get('realized_pnl', 0)
            pnl_pct       = position_data.get('pnl_percentage', 0)
            entry_time    = position_data['entry_time']
            entry_indicators = position_data.get('entry_indicators', {})

            # ICT data dari saat entry
            setup_type = entry_indicators.get('setup_type', position_data.get('setup_type', 'ICT'))
            in_ob      = entry_indicators.get('in_order_block', position_data.get('in_order_block', False))
            in_fvg     = entry_indicators.get('in_fvg', position_data.get('in_fvg', False))
            liq        = entry_indicators.get('liquidity_confirmed', position_data.get('liquidity_confirmed', False))
            bos        = entry_indicators.get('bos_confirmed', position_data.get('bos_confirmed', False))
            choch      = entry_indicators.get('choch_detected', position_data.get('choch_detected', False))
            kz         = entry_indicators.get('kill_zone_active', position_data.get('kill_zone_active', False))
            ict_score  = entry_indicators.get('ict_score', position_data.get('ict_score', 0))
            pd_zone    = entry_indicators.get('pd_zone', position_data.get('pd_zone', 'N/A'))
            rr         = entry_indicators.get('rr_ratio', position_data.get('rr_ratio', 0))
            session    = position_data.get('trading_session', 'N/A')

            price_change = ((exit_price - entry_price) / entry_price) * 100
            if direction == 'SHORT':
                price_change = -price_change

            duration = self._calculate_duration(entry_time, datetime.now())

            exit_explanations = {
                'TP_HIT': 'Target Profit tercapai ✅',
                'SL_HIT': 'Stop Loss terpicu ❌',
                'MANUAL': 'Penutupan manual 🖐',
                'TIMEOUT': 'Timeout otomatis ⏰',
                'ERROR': 'Error sistem ⚠️'
            }
            exit_desc = exit_explanations.get(exit_reason, exit_reason)

            # ICT entry checklist
            ict_entry = [
                f"{'✅' if bos else '❌'} BOS terkonfirmasi saat entry",
                f"{'✅' if choch else '❌'} CHoCH terkonfirmasi saat entry",
                f"{'✅' if in_ob else '❌'} Entry di Order Block",
                f"{'✅' if in_fvg else '❌'} Entry di Fair Value Gap",
                f"{'✅' if liq else '❌'} Liquidity sweep terkonfirmasi",
                f"{'✅' if kz else '❌'} Kill Zone aktif saat entry",
                f"📍 PD Zone: {pd_zone} | ICT Score: {ict_score}/11 | R:R: {rr:.2f}",
            ]
            ict_entry_text = '\n'.join(ict_entry)

            prompt = f"""Kamu adalah trader ICT/SMC profesional. Tulis analisis hasil trade berikut dalam bahasa Indonesia yang mengalir natural seperti seorang trader senior sedang mereview trade-nya — bukan laporan formal, bukan daftar poin bernomor. Gunakan paragraf yang mengalir, padat, dan tajam.

=== HASIL TRADE ===
Symbol: {symbol} | Arah: {direction} | Setup: {setup_type}
Sesi Entry: {session} | Durasi: {duration}
Entry: ${entry_price:.6f} → Exit: ${exit_price:.6f} ({price_change:+.2f}%)
PnL: ${pnl:.2f} ({pnl_pct:.2f}%) | Status: {exit_desc}

=== KONDISI ICT SAAT ENTRY ===
{ict_entry_text}

Format output HTML — tulis dalam 3-4 paragraf mengalir tanpa heading bernomor. Gunakan <b> hanya untuk menekankan istilah teknikal penting. Pisahkan paragraf dengan <br><br>.

Paragraf pertama: evaluasi hasil trade — apakah {exit_reason} sesuai ekspektasi setup ICT, bagaimana pergerakan harga dari entry ke exit.
Paragraf kedua: analisis apakah konfirmasi ICT saat entry (BOS/CHoCH, OB, FVG, liquidity sweep) terbukti valid atau tidak, dan apa yang terjadi di market.
Paragraf ketiga: evaluasi kualitas setup dan eksekusi — apa yang bekerja baik dan apa yang bisa diperbaiki.
Paragraf keempat: insight konkret untuk setup {setup_type} serupa ke depannya.

PENTING: Jangan gunakan angka di depan paragraf. Jangan gunakan bullet point. Tulis seperti narasi analisis profesional."""

            response = await self._generate_response(prompt)

            # Clean up formatting
            for tag in ['```html', '```', '<html>', '</html>']:
                response = response.replace(tag, '')
            response = response.strip()
            # Remove leading <br> tags and whitespace
            response = response.strip()
            while response.startswith('<br>') or response.startswith('<br/>') or response.startswith('<br />') or response.startswith('<p>'):
                if response.startswith('<br>'):
                    response = response[4:].strip()
                elif response.startswith('<br/>'):
                    response = response[5:].strip()
                elif response.startswith('<br />'):
                    response = response[6:].strip()
                elif response.startswith('<p>'):
                    response = response[3:].strip()
            
            # Remove trailing </p> tags
            while response.endswith('</p>'):
                response = response[:-4].strip()
            
            # Ensure it starts with proper HTML
            if not response.startswith('<b>'):
                # If it doesn't start with <b>, it might be malformed
                print(f"⚠️ AI response doesn't start with <b>, fixing format...")
                if '<b>' in response:
                    # Find the first <b> tag and start from there
                    start_idx = response.find('<b>')
                    response = response[start_idx:]
            
            return response
            
        except Exception as e:
            print(f"❌ Error generating comprehensive exit reasoning: {e}")
            import traceback
            traceback.print_exc()
            
            # CRITICAL: AI MUST WORK - No fallback allowed per user requirement
            print(f"🔄 CRITICAL: Retrying AI analysis for {position_data.get('symbol', 'N/A')} - AI is MANDATORY")
            
            # Try with different model parameters
            try:
                # Retry with more aggressive settings
                simple_prompt = f"""Tulis analisis penutupan posisi {position_data.get('symbol', 'N/A')} {position_data.get('direction', 'N/A')} dalam bahasa Indonesia yang natural dan mengalir seperti trader profesional — tanpa nomor, tanpa bullet point, hanya paragraf.

Detail trade:
Entry: ${position_data.get('entry_price', 0):.6f} | Exit: ${position_data.get('exit_price', 0):.6f}
PnL: ${position_data.get('realized_pnl', 0):.2f} ({position_data.get('pnl_percentage', 0):.2f}%) | Alasan: {exit_reason}

Tulis 3 paragraf HTML dipisah <br><br>. Gunakan <b> hanya untuk istilah teknikal penting. Bahas hasil trade, evaluasi setup, dan insight untuk ke depannya. Jangan gunakan heading bernomor."""
                
                retry_response = await self._generate_response(simple_prompt)
                
                # Clean up formatting
                if retry_response.startswith('```html'):
                    retry_response = retry_response.replace('```html', '').replace('```', '').strip()
                if retry_response.startswith('<html>'):
                    retry_response = retry_response.replace('<html>', '').strip()
                if retry_response.endswith('</html>'):
                    retry_response = retry_response.replace('</html>', '').strip()
                
                # Remove leading <br> tags and whitespace
                retry_response = retry_response.strip()
                while retry_response.startswith('<br>') or retry_response.startswith('<br/>') or retry_response.startswith('<br />') or retry_response.startswith('<p>'):
                    if retry_response.startswith('<br>'):
                        retry_response = retry_response[4:].strip()
                    elif retry_response.startswith('<br/>'):
                        retry_response = retry_response[5:].strip()
                    elif retry_response.startswith('<br />'):
                        retry_response = retry_response[6:].strip()
                    elif retry_response.startswith('<p>'):
                        retry_response = retry_response[3:].strip()
                
                # Remove trailing </p> tags
                while retry_response.endswith('</p>'):
                    retry_response = retry_response[:-4].strip()
                
                # Ensure it starts with proper HTML
                if not retry_response.startswith('<b>'):
                    print(f"⚠️ Retry response doesn't start with <b>, fixing format...")
                    if '<b>' in retry_response:
                        start_idx = retry_response.find('<b>')
                        retry_response = retry_response[start_idx:]
                
                print(f"✅ AI retry successful for {position_data.get('symbol', 'N/A')}")
                return retry_response
                
            except Exception as retry_error:
                print(f"❌ AI retry failed: {retry_error}")
                
                # LAST RESORT: Force reinitialize AI and try once more
                try:
                    print(f"🔄 LAST RESORT: Reinitializing AI for {position_data.get('symbol', 'N/A')}")
                    
                    # Force reinitialize Gemini
                    from gemini_ai_system import GeminiMarketAnalyst
                    new_analyst = GeminiMarketAnalyst()
                    
                    final_response = await new_analyst._generate_response(simple_prompt)
                    
                    # Clean formatting
                    final_response = final_response.strip()
                    if final_response.startswith('```html'):
                        final_response = final_response.replace('```html', '').replace('```', '').strip()
                    
                    # Remove leading <br> tags
                    while final_response.startswith('<br>') or final_response.startswith('<br/>'):
                        if final_response.startswith('<br>'):
                            final_response = final_response[4:].strip()
                        elif final_response.startswith('<br/>'):
                            final_response = final_response[5:].strip()
                    
                    if '<b>' in final_response and not final_response.startswith('<b>'):
                        start_idx = final_response.find('<b>')
                        final_response = final_response[start_idx:]
                    
                    print(f"✅ AI LAST RESORT successful for {position_data.get('symbol', 'N/A')}")
                    return final_response
                    
                except Exception as final_error:
                    print(f"❌ CRITICAL: All AI attempts failed for {position_data.get('symbol', 'N/A')}: {final_error}")
                    
                    # CRITICAL: AI IS MANDATORY - Raise exception to stop system
                    raise Exception(f"CRITICAL FAILURE: AI exit reasoning is MANDATORY but completely failed for {position_data.get('symbol', 'N/A')}. System must be fixed before continuing. Error: {final_error}")
    
    async def _get_comprehensive_market_analysis(self, symbol: str, entry_time: str) -> str:
        """Get comprehensive market analysis comparing entry vs current conditions"""
        try:
            # Get current market data from Bybit API
            ticker_response = self.session.get_tickers(category="linear", symbol=symbol)
            if ticker_response['retCode'] != 0 or not ticker_response['result']['list']:
                raise Exception(f"Failed to get ticker data for {symbol}: {ticker_response.get('retMsg', 'Unknown error')}")
            
            ticker = ticker_response['result']['list'][0]
            current_price = float(ticker['lastPrice'])
            current_change_24h = float(ticker.get('price24hPcnt', 0)) * 100
            current_volume_24h = float(ticker.get('volume24h', 0))
            current_turnover_24h = float(ticker.get('turnover24h', 0))
            open_interest = float(ticker.get('openInterest', 0))
            
            # Get funding rate
            funding_response = self.session.get_funding_rate_history(category="linear", symbol=symbol, limit=1)
            funding_rate = 0
            if funding_response['retCode'] == 0 and funding_response['result']['list']:
                funding_rate = float(funding_response['result']['list'][0]['fundingRate']) * 100
            
            # Calculate time since entry
            from datetime import datetime
            try:
                entry_dt = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
                time_diff = datetime.now() - entry_dt
                hours_since_entry = time_diff.total_seconds() / 3600
            except:
                hours_since_entry = 0
            
            # Get volatility data from recent klines
            klines_response = self.session.get_kline(category="linear", symbol=symbol, interval="15", limit=20)
            volatility_analysis = "Volatilitas normal"
            price_trend_analysis = "Trend tidak dapat ditentukan"
            
            if klines_response['retCode'] == 0 and klines_response['result']['list']:
                klines = klines_response['result']['list']
                highs = [float(k[2]) for k in klines]
                lows = [float(k[3]) for k in klines]
                closes = [float(k[4]) for k in klines]
                
                # Calculate average true range for volatility
                ranges = [(h - l) / c * 100 for h, l, c in zip(highs, lows, closes) if c > 0]
                avg_volatility = sum(ranges) / len(ranges) if ranges else 0
                
                if avg_volatility > 3.0:
                    volatility_analysis = f"Volatilitas tinggi ({avg_volatility:.2f}% avg range)"
                elif avg_volatility > 1.5:
                    volatility_analysis = f"Volatilitas sedang ({avg_volatility:.2f}% avg range)"
                else:
                    volatility_analysis = f"Volatilitas rendah ({avg_volatility:.2f}% avg range)"
                
                # Calculate price trend from klines (1 hour analysis)
                if len(closes) >= 4:  # Use 4 candles (1 hour) instead of all
                    recent_change = ((closes[-1] - closes[-4]) / closes[-4]) * 100
                    if recent_change > 0.5:
                        price_trend_analysis = f"Trend naik dalam 1 jam terakhir (+{recent_change:.2f}%)"
                    elif recent_change < -0.5:
                        price_trend_analysis = f"Trend turun dalam 1 jam terakhir ({recent_change:.2f}%)"
                    else:
                        price_trend_analysis = f"Sideways dalam 1 jam terakhir ({recent_change:+.2f}%)"
            
            # Alternative 24h change calculation if API returns 0
            if abs(current_change_24h) < 0.01:  # If 24h change is essentially 0
                try:
                    # Get 24h klines to calculate manually
                    klines_24h = self.session.get_kline(category="linear", symbol=symbol, interval="1h", limit=24)
                    if klines_24h['retCode'] == 0 and klines_24h['result']['list']:
                        klines_data = klines_24h['result']['list']
                        if len(klines_data) >= 2:
                            price_24h_ago = float(klines_data[0][4])  # Close price 24h ago
                            manual_change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100
                            current_change_24h = manual_change_24h
                except Exception as e:
                    pass  # Silent fallback
            
            # Get 1-hour change data
            klines_1h = self.session.get_kline(category="linear", symbol=symbol, interval="15", limit=4)
            change_1h = 0
            if klines_1h['retCode'] == 0 and klines_1h['result']['list']:
                klines_1h_data = klines_1h['result']['list']
                if len(klines_1h_data) >= 4:
                    price_1h_ago = float(klines_1h_data[0][4])  # Close price 1h ago
                    change_1h = ((current_price - price_1h_ago) / price_1h_ago) * 100
            
            analysis = f"""PERBANDINGAN KONDISI MARKET:
            
📊 KONDISI SAAT INI:
   - Harga: ${current_price:.6f}
   - Perubahan 24h: {current_change_24h:.2f}%
   - Perubahan 1h: {change_1h:.2f}%
   - Volume 24h: ${current_volume_24h:,.0f}
   - Turnover 24h: ${current_turnover_24h:,.0f}
   - Open Interest: {open_interest:,.0f}
   - Funding Rate: {funding_rate:.4f}%
   - {volatility_analysis}
   - {price_trend_analysis}
   
⏰ WAKTU SEJAK ENTRY:
   - Durasi: {hours_since_entry:.1f} jam
   - Momentum 1h: {'Positif' if change_1h > 0.2 else 'Negatif' if change_1h < -0.2 else 'Netral'}
   
💹 ANALISIS PERUBAHAN:
   - Volume trend: {'Meningkat' if current_volume_24h > 50000000 else 'Normal' if current_volume_24h > 10000000 else 'Rendah'}
   - OI trend: {'Tinggi' if open_interest > 100000000 else 'Sedang' if open_interest > 50000000 else 'Rendah'}
   - Market sentiment 24h: {'Bullish' if current_change_24h > 2 else 'Bearish' if current_change_24h < -2 else 'Sideways'}
   - Market sentiment 1h: {'Bullish' if change_1h > 0.5 else 'Bearish' if change_1h < -0.5 else 'Sideways'}
   - Funding bias: {'Long-heavy' if funding_rate > 0.01 else 'Short-heavy' if funding_rate < -0.01 else 'Balanced'}"""
            
            return analysis
            
        except Exception as e:
            print(f"❌ Error in comprehensive market analysis: {e}")
            # CRITICAL: Re-raise error instead of fallback - market data is required
            raise Exception(f"Market data analysis failed: {e}")
    
    def _analyze_indicator_changes(self, entry_indicators: Dict, symbol: str) -> str:
        """Analyze how indicators have changed since entry with passed/failed analysis"""
        try:
            if not entry_indicators:
                return "Data indikator saat entry tidak tersedia"
            
            # Get the direction from entry indicators context (we need to infer this)
            # This is a limitation - we should store direction with indicators
            # For now, we'll analyze both directions and see which makes more sense
            
            from indicator_analysis_system import IndicatorAnalysisSystem
            analyzer = IndicatorAnalysisSystem()
            
            # Try to determine direction from context or assume we need both analyses
            # Since we don't have direction stored, we'll provide general analysis
            
            analysis = f"""ANALISIS INDIKATOR SAAT ENTRY:
            
📈 KONDISI INDIKATOR SAAT ENTRY:
   - EMA Fast > Slow: {'✅' if entry_indicators.get('ema_fast_above_slow') else '❌'}
   - RSI Oversold: {'✅' if entry_indicators.get('rsi_oversold') else '❌'}
   - RSI Overbought: {'✅' if entry_indicators.get('rsi_overbought') else '❌'}
   - MACD Line > Signal: {'✅' if entry_indicators.get('macd_bullish') else '❌'}
   - Volume Confirmation: {'✅' if entry_indicators.get('volume_confirmation') else '❌'}
   - Volatility Confirmation: {'✅' if entry_indicators.get('volatility_confirmation') else '❌'}
   - Trend Alignment: {'✅' if entry_indicators.get('trend_alignment') else '❌'}
   - Momentum Confirmation: {'✅' if entry_indicators.get('momentum_confirmation') else '❌'}
   
📊 NILAI NUMERIK SAAT ENTRY:
   - RSI Level: {entry_indicators.get('rsi_level', 'N/A')}
   - EMA Fast: {entry_indicators.get('ema_fast_value', 'N/A')}
   - EMA Slow: {entry_indicators.get('ema_slow_value', 'N/A')}
   - MACD Line: {entry_indicators.get('macd_line_value', 'N/A')}
   - Signal Line: {entry_indicators.get('signal_line_value', 'N/A')}
   - ATR: {entry_indicators.get('atr_value', 'N/A')}
   
🔄 KEKUATAN SINYAL SAAT ENTRY:
   - Total indikator positif: {sum(1 for v in entry_indicators.values() if isinstance(v, bool) and v)}
   - Kekuatan sinyal: {'Kuat' if sum(1 for v in entry_indicators.values() if isinstance(v, bool) and v) >= 5 else 'Sedang' if sum(1 for v in entry_indicators.values() if isinstance(v, bool) and v) >= 3 else 'Lemah'}
   
⚠️ CATATAN PENTING:
   - Kondisi indikator mungkin sudah berubah sejak entry
   - Analisis ini berdasarkan snapshot saat posisi dibuka
   - Perlu evaluasi kondisi teknikal saat exit untuk perbandingan lengkap"""
            
            return analysis
            
        except Exception as e:
            print(f"⚠️ Error analyzing indicator changes: {e}")
            return "Analisis perubahan indikator tidak tersedia"
    
    async def _get_current_technical_analysis(self, symbol: str) -> str:
        """Get current technical analysis"""
        try:
            # Get recent klines for technical analysis
            klines_response = self.session.get_kline(category="linear", symbol=symbol, interval="15", limit=50)
            if klines_response['retCode'] != 0 or not klines_response['result']['list']:
                return "Analisis teknikal saat ini tidak tersedia"
            
            klines = klines_response['result']['list']
            closes = [float(k[4]) for k in klines]
            highs = [float(k[2]) for k in klines]
            lows = [float(k[3]) for k in klines]
            volumes = [float(k[5]) for k in klines]
            
            if len(closes) < 26:
                return "Data tidak cukup untuk analisis teknikal"
            
            # Calculate current indicators
            current_price = closes[-1]
            
            # Simple EMA calculation
            ema_fast = sum(closes[-5:]) / 5 if len(closes) >= 5 else current_price
            ema_slow = sum(closes[-13:]) / 13 if len(closes) >= 13 else current_price
            ema_trend = "Bullish" if ema_fast > ema_slow else "Bearish"
            
            # Simple RSI calculation
            gains = []
            losses = []
            for i in range(1, min(15, len(closes))):
                change = closes[-i] - closes[-i-1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            avg_gain = sum(gains) / len(gains) if gains else 0
            avg_loss = sum(losses) / len(losses) if losses else 0.001
            rs = avg_gain / avg_loss if avg_loss > 0 else 0
            rsi = 100 - (100 / (1 + rs))
            
            rsi_condition = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
            
            # Volume analysis
            avg_volume = sum(volumes[-10:]) / 10 if len(volumes) >= 10 else volumes[-1]
            current_volume = volumes[-1]
            volume_trend = "Tinggi" if current_volume > avg_volume * 1.2 else "Rendah" if current_volume < avg_volume * 0.8 else "Normal"
            
            # Price action analysis
            recent_high = max(highs[-10:]) if len(highs) >= 10 else current_price
            recent_low = min(lows[-10:]) if len(lows) >= 10 else current_price
            price_position = ((current_price - recent_low) / (recent_high - recent_low)) * 100 if recent_high != recent_low else 50
            
            analysis = f"""KONDISI TEKNIKAL SAAT INI:
            
📊 INDIKATOR UTAMA:
   - EMA Trend: {ema_trend} (Fast: ${ema_fast:.6f}, Slow: ${ema_slow:.6f})
   - RSI: {rsi:.1f} ({rsi_condition})
   - Volume: {volume_trend} vs rata-rata
   - Price Position: {price_position:.1f}% dari range recent
   
📈 MOMENTUM:
   - Trend direction: {ema_trend}
   - Momentum strength: {'Strong' if abs(ema_fast - ema_slow) / current_price > 0.01 else 'Weak'}
   - Volume support: {'Yes' if volume_trend == 'Tinggi' else 'No'}
   
🎯 LEVEL KRITIS:
   - Recent High: ${recent_high:.6f}
   - Recent Low: ${recent_low:.6f}
   - Current: ${current_price:.6f}"""
            
            return analysis
            
        except Exception as e:
            print(f"❌ Error in current technical analysis: {e}")
            # CRITICAL: Re-raise error instead of fallback - technical data is required
            raise Exception(f"Technical analysis failed: {e}")
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
        max_retries = len(self.api_keys) * 2  # Allow multiple retries per key
        
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
            
            if response and response.text:
                return response.text
            else:
                raise Exception("Empty response from Gemini API")
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if it's a rate limit error
            if ('rate limit' in error_str or 'quota' in error_str or 'too many requests' in error_str) and retry_count < max_retries:
                print(f"⚠️  Rate limit hit on {self._get_current_api_key_info()}, rotating to next key...")
                self._rotate_api_key()
                
                # Wait a bit before retrying
                await asyncio.sleep(2)
                
                # Retry with next API key
                return await self._generate_response(prompt, retry_count + 1)
            
            # Check if it's a safety/content filter error
            elif ('safety' in error_str or 'blocked' in error_str or 'filter' in error_str) and retry_count < max_retries:
                print(f"⚠️  Content filtered, trying with modified prompt...")
                
                # Simplify prompt to avoid content filters
                simplified_prompt = f"""
                Analisis trading dalam bahasa Indonesia:
                
                {prompt.split('DETAIL POSISI:')[1].split('WAJIB GUNAKAN')[0] if 'DETAIL POSISI:' in prompt else prompt[:500]}
                
                Berikan analisis singkat dalam format HTML dengan <b>bold</b> dan <br> untuk line break.
                Fokus pada analisis teknikal dan market condition.
                """
                
                return await self._generate_response(simplified_prompt, retry_count + 1)
            
            # If not a rate limit error or max retries reached
            print(f"❌ Gemini API error ({self._get_current_api_key_info()}): {e}")
            
            if retry_count >= max_retries:
                raise Exception(f"All API keys exhausted after {max_retries} attempts. Last error: {str(e)}")
            else:
                raise Exception(f"Gemini API error: {str(e)}")
    
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
    
    def _format_numerical_indicators(self, indicators: Dict) -> str:
        """Format numerical indicators for AI prompt"""
        numerical_indicators = []
        
        numerical_keys = ['rsi_level', 'atr_value', 'ema_fast_value', 'ema_slow_value', 
                         'macd_line_value', 'signal_line_value', 'support_resistance', 
                         'price_distance_from_level']
        
        descriptions = {
            'rsi_level': 'RSI Level',
            'atr_value': 'Average True Range (Volatility)',
            'ema_fast_value': 'EMA Fast Value',
            'ema_slow_value': 'EMA Slow Value',
            'macd_line_value': 'MACD Line Value',
            'signal_line_value': 'Signal Line Value',
            'support_resistance': 'Support/Resistance Level',
            'price_distance_from_level': 'Distance from Key Level (%)'
        }
        
        for key in numerical_keys:
            if key in indicators and indicators[key] != 0:
                desc = descriptions.get(key, key.replace('_', ' ').title())
                value = indicators[key]
                numerical_indicators.append(f"- {desc}: {value:.6f}")
        
        return "\n".join(numerical_indicators) if numerical_indicators else "No numerical indicator data"
    
    def _format_indicators(self, indicators: Dict) -> str:
        """Format technical indicators for AI prompt with clear descriptions"""
        if not indicators:
            return "No indicator data available"
        
        formatted = []
        
        # Group indicators by type for better readability
        boolean_indicators = []
        numerical_indicators = []
        
        # Indicator descriptions with direction context
        descriptions = {
            'ema_fast_above_slow': 'EMA Fast > EMA Slow (Trend Direction)',
            'macd_bullish': 'MACD Line > Signal Line (Momentum)',
            'rsi_oversold': 'RSI Oversold (<30)',
            'rsi_overbought': 'RSI Overbought (>70)',
            'rsi_neutral': 'RSI Neutral Zone (30-70)',
            'volume_confirmation': 'Volume Confirmation',
            'volatility_confirmation': 'VOLATILITY CONFIRMATION',
            'price_near_support': 'Price Near Support Level',
            'price_near_resistance': 'Price Near Resistance Level',
            'trend_alignment': 'Trend Alignment',
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
    
    def _format_numerical_indicators(self, indicators: Dict) -> str:
        """Format only numerical indicators for AI prompt"""
        if not indicators:
            return "No numerical indicator data available"
        
        numerical_indicators = []
        
        # Numerical indicator descriptions
        descriptions = {
            'rsi_level': 'RSI Level',
            'atr_value': 'Average True Range (Volatility)',
            'ema_fast_value': 'EMA Fast Value',
            'ema_slow_value': 'EMA Slow Value',
            'macd_line_value': 'MACD Line Value',
            'signal_line_value': 'Signal Line Value',
            'support_resistance': 'Support/Resistance Level',
            'price_distance_from_level': 'Distance from Key Level (%)'
        }
        
        for key, value in indicators.items():
            if isinstance(value, (int, float)) and value != 0:
                description = descriptions.get(key, key.replace('_', ' ').title())
                numerical_indicators.append(f"- {description}: {value:.6f}")
        
        return "\n".join(numerical_indicators) if numerical_indicators else "No numerical indicator values"
    
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
    
    async def chat_with_market_data(self, user_question: str, context: Dict = None, trading_mode: str = "dry_run") -> str:
        """Interactive chat with real market data access and trading system data
        
        Args:
            user_question: User's question
            context: Additional context (symbol, etc.)
            trading_mode: "dry_run" or "real_trading" to determine which data to access
        """
        try:
            # Get trading system data based on mode
            if trading_mode == "dry_run":
                from dry_run_system import dry_run_system
                open_positions = dry_run_system.get_open_positions()
                recent_trades = dry_run_system.get_trade_history(10)
            else:
                from real_trade_system import real_trade_system
                open_positions = real_trade_system.get_open_positions()
                recent_trades = real_trade_system.get_trade_history(10)
            
            # Prepare trading context
            trading_context = f"""
            TRADING SYSTEM DATA ({trading_mode.upper()}):
            
            📊 Open Positions: {len(open_positions)}
            {chr(10).join([f"   - {pos['symbol']} {pos['direction']} @ ${pos['entry_price']:.6f} | PnL: {pos.get('unrealized_pnl', 0):.2f}" for pos in open_positions[:5]])}
            
            📈 Recent Trades: {len(recent_trades)}
            {chr(10).join([f"   - {trade['symbol']} {trade['direction']} | PnL: {trade.get('pnl_percentage', 0):.2f}% | {trade.get('exit_reason', 'N/A')}" for trade in recent_trades[:5]])}
            """
            
            # Add symbol-specific context if provided
            symbol_context = ""
            if context and context.get('symbol'):
                symbol = context['symbol']
                try:
                    market_data = await self._get_market_context(symbol)
                    symbol_context = f"\nSYMBOL CONTEXT ({symbol}):\n{market_data}"
                except:
                    symbol_context = f"\nSYMBOL: {symbol} (market data unavailable)"
            
            # Generate response
            prompt = f"""
            Jawab pertanyaan user tentang trading dan market dalam bahasa Indonesia:
            
            PERTANYAAN USER: {user_question}
            
            {trading_context}
            {symbol_context}
            
            Berikan jawaban yang:
            - Menggunakan data trading system yang tersedia
            - Memberikan insight praktis dan actionable
            - Menjelaskan kondisi market saat ini
            - Memberikan rekomendasi berdasarkan data
            - Menggunakan bahasa Indonesia yang jelas
            - Format HTML untuk readability: <b>bold</b>, <br> untuk line break
            """
            
            response = await self._generate_response(prompt)
            return response
            
        except Exception as e:
            print(f"❌ Error in chat with market data: {e}")
            return f"Maaf, terjadi error dalam mengakses data market: {str(e)}"

# Global instance
gemini_analyst = None

def get_gemini_analyst():
    """Get or create Gemini analyst instance with robust error handling"""
    global gemini_analyst
    
    # If instance exists and is working, return it
    if gemini_analyst is not None:
        try:
            # Test if the instance is still working
            if hasattr(gemini_analyst, 'api_keys') and gemini_analyst.api_keys:
                return gemini_analyst
        except:
            # Instance is corrupted, reset it
            gemini_analyst = None
    
    # Create new instance with retry mechanism
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"🤖 Initializing Gemini AI (attempt {attempt + 1}/{max_retries})...")
            gemini_analyst = GeminiMarketAnalyst()
            
            # Verify initialization was successful
            if gemini_analyst and hasattr(gemini_analyst, 'api_keys') and gemini_analyst.api_keys:
                print(f"✅ Gemini AI initialized successfully with {len(gemini_analyst.api_keys)} API keys")
                return gemini_analyst
            else:
                raise Exception("Gemini analyst created but API keys not found")
                
        except Exception as e:
            print(f"❌ Failed to initialize Gemini AI (attempt {attempt + 1}): {e}")
            gemini_analyst = None
            
            if attempt < max_retries - 1:
                import time
                time.sleep(1)  # Wait before retry
            else:
                print("❌ CRITICAL: All attempts to initialize Gemini AI failed!")
                print("🔧 Please check:")
                print("   - GEMINI_API_KEYS environment variable")
                print("   - Internet connection")
                print("   - API key validity")
                raise Exception(f"Failed to initialize Gemini AI after {max_retries} attempts: {e}")
    
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