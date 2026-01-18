"""
Real Trading System - Untuk trading nyata dengan tracking terpisah
"""
import json
import sqlite3
from datetime import datetime, timedelta
import uuid
from typing import Dict, List, Optional
import os
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bybit API configuration
BYBIT_API_KEY = os.getenv('BYBIT_API_KEY', '')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET', '')

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Initialize Telegram bot if credentials are available
telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None

class RealTradeSystem:
    def __init__(self, db_path="real_trades.db"):
        self.db_path = db_path
        self.init_database()
        self._bybit_session = None
        
    def _get_bybit_session(self):
        """Get Bybit session for API calls"""
        if not self._bybit_session and BYBIT_API_KEY and BYBIT_API_SECRET:
            from pybit.unified_trading import HTTP
            self._bybit_session = HTTP(
                testnet=False,  # MAINNET untuk real trading
                api_key=BYBIT_API_KEY,
                api_secret=BYBIT_API_SECRET
            )
        return self._bybit_session
    
    def get_real_balance(self):
        """Get real balance from Bybit API"""
        try:
            session = self._get_bybit_session()
            if not session:
                print("⚠️  No Bybit API credentials, using fallback balance")
                return 1000.0  # Fallback jika tidak ada API key
            
            response = session.get_wallet_balance(accountType="UNIFIED")
            
            if response['retCode'] == 0:
                coins = response['result']['list'][0]['coin']
                usdt_balance = 0
                for coin in coins:
                    if coin['coin'] == 'USDT':
                        usdt_balance = float(coin['walletBalance'])
                        break
                print(f"💰 Real Bybit Balance: ${usdt_balance:.2f} USDT")
                return usdt_balance
            else:
                print(f"❌ Error getting Bybit balance: {response.get('retMsg', 'Unknown error')}")
                return 1000.0  # Fallback
        except Exception as e:
            print(f"❌ Exception getting Bybit balance: {e}")
            return 1000.0  # Fallback
        
    def init_database(self):
        """Initialize SQLite database for real trading"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)  # Add timeout
        cursor = conn.cursor()
        
        # Enable WAL mode for better concurrent access
        cursor.execute('PRAGMA journal_mode=WAL;')
        cursor.execute('PRAGMA synchronous=NORMAL;')
        cursor.execute('PRAGMA cache_size=10000;')
        cursor.execute('PRAGMA temp_store=memory;')
        
        # Table untuk open positions (sama struktur dengan dry run)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS open_positions (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                quantity REAL NOT NULL,
                leverage INTEGER NOT NULL,
                tp_price REAL NOT NULL,
                sl_price REAL NOT NULL,
                entry_time TEXT NOT NULL,
                current_price REAL,
                unrealized_pnl REAL DEFAULT 0,
                indicators TEXT,
                position_value_usd REAL NOT NULL,
                bybit_order_id TEXT,
                bybit_position_id TEXT,
                ai_entry_reasoning TEXT
            )
        ''')
        
        # Table untuk trade history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_history (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL NOT NULL,
                quantity REAL NOT NULL,
                leverage INTEGER NOT NULL,
                entry_time TEXT NOT NULL,
                exit_time TEXT NOT NULL,
                exit_reason TEXT NOT NULL,
                pnl REAL NOT NULL,
                pnl_percentage REAL NOT NULL,
                indicators TEXT,
                position_value_usd REAL NOT NULL,
                duration_minutes INTEGER,
                bybit_entry_order_id TEXT,
                bybit_exit_order_id TEXT,
                fees_paid REAL DEFAULT 0,
                ai_entry_reasoning TEXT,
                ai_exit_reasoning TEXT
            )
        ''')
        
        # Table untuk performance metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                date TEXT PRIMARY KEY,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                total_pnl REAL DEFAULT 0,
                max_drawdown REAL DEFAULT 0,
                balance REAL,
                win_rate REAL DEFAULT 0,
                avg_win REAL DEFAULT 0,
                avg_loss REAL DEFAULT 0,
                profit_factor REAL DEFAULT 0,
                total_fees REAL DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def open_position(self, signal: Dict, bybit_order_id: str = None) -> str:
        """Open new real trading position"""
        position_id = str(uuid.uuid4())
        
        # Retry mechanism for database operations
        max_retries = 3
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=30.0)
                cursor = conn.cursor()
        
                # Store ALL indicators that triggered the signal (KONDISI MARKET SAAT SINYAL)
                indicators = {
                    # Boolean indicators (kondisi saat sinyal terjadi)
                    'ema_fast_above_slow': bool(signal.get('ema_fast_above_slow', False)),
                    'macd_bullish': bool(signal.get('macd_bullish', False)),
                    'rsi_oversold': bool(signal.get('rsi_oversold', False)),
                    'rsi_overbought': bool(signal.get('rsi_overbought', False)),
                    'rsi_neutral': bool(signal.get('rsi_neutral', False)),
                    'volume_confirmation': bool(signal.get('volume_confirmation', False)),
                    'volatility_confirmation': bool(signal.get('volatility_confirmation', False)),
                    'price_near_support': bool(signal.get('price_near_support', False)),
                    'price_near_resistance': bool(signal.get('price_near_resistance', False)),
                    'trend_alignment': bool(signal.get('trend_alignment', False)),
                    'momentum_confirmation': bool(signal.get('momentum_confirmation', False)),
                    
                    # Numerical values (nilai indikator saat sinyal)
                    'rsi_level': float(signal.get('rsi_level', 50)),
                    'atr_value': float(signal.get('atr_value', 0)),
                    'ema_fast_value': float(signal.get('ema_fast_value', 0)),
                    'ema_slow_value': float(signal.get('ema_slow_value', 0)),
                    'macd_line_value': float(signal.get('macd_line_value', 0)),
                    'signal_line_value': float(signal.get('signal_line_value', 0)),
                    'support_resistance': float(signal.get('support_resistance', 0)),
                    'price_distance_from_level': float(signal.get('price_distance_from_level', 0))
                }
                
                cursor.execute('''
                    INSERT INTO open_positions 
                    (id, symbol, direction, entry_price, quantity, leverage, tp_price, sl_price, 
                     entry_time, current_price, indicators, position_value_usd, bybit_order_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    position_id, signal['symbol'], signal['direction'], signal['close'],
                    signal['pos_size'], signal['leverage'], signal['tp'], signal['sl'],
                    datetime.now().isoformat(), signal['close'], json.dumps(indicators),
                    signal['position_value_usd'], bybit_order_id
                ))
        
                conn.commit()
                conn.close()
                
                print(f"🚀 [REAL TRADE] Opened {signal['direction']} position for {signal['symbol']}")
                return position_id
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    print(f"⚠️  Real trade database locked, retrying... ({attempt + 1}/{max_retries})")
                    time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    print(f"❌ Real trade database error after {attempt + 1} attempts: {e}")
                    raise
            except Exception as e:
                print(f"❌ Unexpected error opening real position: {e}")
                raise
    
    async def update_positions(self, current_prices: Dict[str, float]):
        """Update current prices and check for TP/SL hits"""
        # Retry mechanism for database operations
        max_retries = 3
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=30.0)
                cursor = conn.cursor()
        
                # Get all open positions
                cursor.execute('SELECT * FROM open_positions')
                positions = cursor.fetchall()
                
                for pos in positions:
                    # Handle both old and new schema with ai_entry_reasoning
                    if len(pos) >= 16:  # New schema with AI reasoning
                        (pos_id, symbol, direction, entry_price, quantity, leverage, 
                         tp_price, sl_price, entry_time, _, unrealized_pnl, indicators, 
                         position_value_usd, bybit_order_id, bybit_position_id, ai_entry_reasoning) = pos
                    else:  # Old schema without AI reasoning
                        (pos_id, symbol, direction, entry_price, quantity, leverage, 
                         tp_price, sl_price, entry_time, _, unrealized_pnl, indicators, 
                         position_value_usd, bybit_order_id, bybit_position_id) = pos
                        ai_entry_reasoning = ""
                    
                    if symbol in current_prices:
                        current_price = current_prices[symbol]
                        
                        # Calculate unrealized PnL
                        if direction == "LONG":
                            pnl = (current_price - entry_price) * quantity
                            # Check TP/SL
                            if current_price >= tp_price:
                                # Generate AI exit reasoning for TP hit
                                ai_exit_reasoning = await self._generate_exit_reasoning(pos, current_price, "TP_HIT")
                                self._close_position(pos_id, current_price, "TP_HIT", conn, ai_exit_reasoning)
                                continue
                            elif current_price <= sl_price:
                                # Generate AI exit reasoning for SL hit
                                ai_exit_reasoning = await self._generate_exit_reasoning(pos, current_price, "SL_HIT")
                                self._close_position(pos_id, current_price, "SL_HIT", conn, ai_exit_reasoning)
                                continue
                        else:  # SHORT
                            pnl = (entry_price - current_price) * quantity
                            # Check TP/SL
                            if current_price <= tp_price:
                                # Generate AI exit reasoning for TP hit
                                ai_exit_reasoning = await self._generate_exit_reasoning(pos, current_price, "TP_HIT")
                                self._close_position(pos_id, current_price, "TP_HIT", conn, ai_exit_reasoning)
                                continue
                            elif current_price >= sl_price:
                                # Generate AI exit reasoning for SL hit
                                ai_exit_reasoning = await self._generate_exit_reasoning(pos, current_price, "SL_HIT")
                                self._close_position(pos_id, current_price, "SL_HIT", conn, ai_exit_reasoning)
                                continue
                        
                        # Update current price and unrealized PnL
                        cursor.execute('''
                            UPDATE open_positions 
                            SET current_price = ?, unrealized_pnl = ?
                            WHERE id = ?
                        ''', (current_price, pnl, pos_id))
                
                conn.commit()
                conn.close()
                break  # Success, exit retry loop
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    print(f"⚠️  Real trade database locked during position update, retrying... ({attempt + 1}/{max_retries})")
                    await asyncio.sleep(0.1 * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    print(f"❌ Real trade database error during position update after {attempt + 1} attempts: {e}")
                    raise
            except Exception as e:
                print(f"❌ Unexpected error updating real positions: {e}")
                raise
    
    async def _generate_exit_reasoning(self, pos, exit_price: float, exit_reason: str) -> str:
        """Generate AI exit reasoning for position closure"""
        try:
            from gemini_ai_system import get_gemini_analyst
            
            gemini_analyst = get_gemini_analyst()
            if not gemini_analyst:
                return f"AI exit reasoning unavailable - {exit_reason}"
            
            # Prepare position data for AI analysis
            position_data = {
                'symbol': pos[1],  # symbol
                'direction': pos[2],  # direction
                'entry_price': pos[3],  # entry_price
                'exit_price': exit_price,
                'quantity': pos[4],  # quantity
                'leverage': pos[5],  # leverage
                'entry_time': pos[8],  # entry_time
                'exit_time': datetime.now().isoformat(),
                'exit_reason': exit_reason,
                'entry_indicators': json.loads(pos[11]) if pos[11] else {},  # indicators
                'realized_pnl': 0,  # Will be calculated
                'pnl_percentage': 0  # Will be calculated
            }
            
            # Generate AI exit reasoning
            exit_reasoning = await gemini_analyst.generate_exit_reasoning(position_data, exit_reason)
            return exit_reasoning
            
        except Exception as e:
            print(f"⚠️  Failed to generate exit reasoning: {e}")
            return f"Exit reasoning unavailable - {exit_reason}"
    
    def _close_position(self, position_id: str, exit_price: float, exit_reason: str, conn, ai_exit_reasoning: str = ""):
        """Close position and move to history"""
        cursor = conn.cursor()
        
        # Get position data
        cursor.execute('SELECT * FROM open_positions WHERE id = ?', (position_id,))
        pos = cursor.fetchone()
        
        if pos:
            # Handle both old and new database schemas
            if len(pos) >= 16:  # New schema with AI reasoning
                (pos_id, symbol, direction, entry_price, quantity, leverage, 
                 tp_price, sl_price, entry_time, _, _, indicators, position_value_usd,
                 bybit_order_id, bybit_position_id, ai_entry_reasoning) = pos
            else:  # Old schema without AI reasoning
                (pos_id, symbol, direction, entry_price, quantity, leverage, 
                 tp_price, sl_price, entry_time, _, _, indicators, position_value_usd,
                 bybit_order_id, bybit_position_id) = pos
                ai_entry_reasoning = ""
            
            # Calculate final PnL
            if direction == "LONG":
                pnl = (exit_price - entry_price) * quantity
            else:  # SHORT
                pnl = (entry_price - exit_price) * quantity
            
            # Calculate PnL percentage relative to margin used (position_value / leverage)
            # This ensures consistency across all systems
            margin_used = position_value_usd / leverage if leverage > 0 else position_value_usd
            pnl_percentage = (pnl / margin_used) * 100 if margin_used > 0 else 0
            
            # Calculate duration
            entry_dt = datetime.fromisoformat(entry_time)
            exit_dt = datetime.now()
            duration_minutes = int((exit_dt - entry_dt).total_seconds() / 60)
            
            # Estimate fees (0.1% for maker/taker)
            fees_paid = position_value_usd * 0.001 * 2  # Entry + Exit fees
            
            # Move to history
            cursor.execute('''
                INSERT INTO trade_history 
                (id, symbol, direction, entry_price, exit_price, quantity, leverage,
                 entry_time, exit_time, exit_reason, pnl, pnl_percentage, indicators,
                 position_value_usd, duration_minutes, bybit_entry_order_id, fees_paid,
                 ai_entry_reasoning, ai_exit_reasoning)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pos_id, symbol, direction, entry_price, exit_price, quantity, leverage,
                entry_time, exit_dt.isoformat(), exit_reason, pnl, pnl_percentage,
                indicators, position_value_usd, duration_minutes, bybit_order_id, fees_paid,
                ai_entry_reasoning, ai_exit_reasoning
            ))
            
            # Remove from open positions
            cursor.execute('DELETE FROM open_positions WHERE id = ?', (position_id,))
            
            # Update performance metrics
            self._update_performance_metrics(conn)
            
            print(f"✅ [REAL TRADE] Closed {direction} {symbol} - {exit_reason} - PnL: ${pnl:.2f} ({pnl_percentage:.2f}%)")
            
            # Send AI Exit Reasoning to Telegram (async call)
            if ai_exit_reasoning and ai_exit_reasoning.strip():
                try:
                    # Import here to avoid circular imports
                    import crypto_bot_parallel
                    
                    # Schedule the async call with complete trading information
                    asyncio.create_task(
                        crypto_bot_parallel.send_ai_exit_reasoning_telegram(
                            symbol, direction, exit_reason, pnl, ai_exit_reasoning,
                            entry_price, exit_price, duration_minutes
                        )
                    )
                except Exception as e:
                    print(f"⚠️ Could not send AI exit reasoning to Telegram: {e}")
    
    
    def _update_performance_metrics(self, conn):
        """Update daily performance metrics"""
        cursor = conn.cursor()
        today = datetime.now().date().isoformat()
        
        # Calculate metrics from trade history
        cursor.execute('''
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                SUM(pnl) as total_pnl,
                AVG(CASE WHEN pnl > 0 THEN pnl ELSE NULL END) as avg_win,
                AVG(CASE WHEN pnl < 0 THEN pnl ELSE NULL END) as avg_loss,
                SUM(fees_paid) as total_fees
            FROM trade_history
        ''')
        
        metrics = cursor.fetchone()
        if metrics and metrics[0] > 0:  # If there are trades
            total_trades, winning_trades, losing_trades, total_pnl, avg_win, avg_loss, total_fees = metrics
            
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if avg_loss and losing_trades > 0 else 0
            
            # Calculate max drawdown berdasarkan real balance
            cursor.execute('SELECT pnl FROM trade_history ORDER BY exit_time')
            pnls = [row[0] for row in cursor.fetchall()]
            
            # Get real balance from Bybit
            real_balance = self.get_real_balance()
            
            max_drawdown = 0
            peak = real_balance  # Starting balance dari Bybit
            current_balance = real_balance
            
            for pnl in pnls:
                current_balance += pnl
                if current_balance > peak:
                    peak = current_balance
                drawdown = (peak - current_balance) / peak * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            # Insert or update metrics
            cursor.execute('''
                INSERT OR REPLACE INTO performance_metrics
                (date, total_trades, winning_trades, losing_trades, total_pnl,
                 max_drawdown, balance, win_rate, avg_win, avg_loss, profit_factor, total_fees)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                today, total_trades, winning_trades, losing_trades, total_pnl,
                max_drawdown, current_balance, win_rate, avg_win or 0, avg_loss or 0, 
                profit_factor, total_fees or 0
            ))
    
    def get_open_positions(self) -> List[Dict]:
        """Get all open positions ordered by newest first"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM open_positions ORDER BY entry_time DESC')
        positions = cursor.fetchall()
        
        result = []
        for pos in positions:
            # Handle both old and new schema with ai_entry_reasoning
            if len(pos) >= 16:  # New schema with AI reasoning
                (pos_id, symbol, direction, entry_price, quantity, leverage, 
                 tp_price, sl_price, entry_time, current_price, unrealized_pnl, 
                 indicators, position_value_usd, bybit_order_id, bybit_position_id, ai_entry_reasoning) = pos
            else:  # Old schema without AI reasoning
                (pos_id, symbol, direction, entry_price, quantity, leverage, 
                 tp_price, sl_price, entry_time, current_price, unrealized_pnl, 
                 indicators, position_value_usd, bybit_order_id, bybit_position_id) = pos
                ai_entry_reasoning = ""
            
            result.append({
                'id': pos_id,
                'symbol': symbol,
                'direction': direction,
                'entry_price': entry_price,
                'current_price': current_price or entry_price,
                'quantity': quantity,
                'leverage': leverage,
                'tp_price': tp_price,
                'sl_price': sl_price,
                'entry_time': entry_time,
                'unrealized_pnl': unrealized_pnl or 0,
                'indicators': json.loads(indicators) if indicators else {},
                'position_value_usd': position_value_usd,
                'bybit_order_id': bybit_order_id,
                'ai_entry_reasoning': ai_entry_reasoning
            })
        
        conn.close()
        return result
    
    def get_trade_history(self, limit: int = 50) -> List[Dict]:
        """Get trade history with AI reasoning"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM trade_history 
            ORDER BY exit_time DESC 
            LIMIT ?
        ''', (limit,))
        
        trades = cursor.fetchall()
        
        result = []
        for trade in trades:
            # Handle both old and new schema
            if len(trade) >= 19:  # New schema with AI reasoning
                (trade_id, symbol, direction, entry_price, exit_price, quantity, leverage,
                 entry_time, exit_time, exit_reason, pnl, pnl_percentage, indicators,
                 position_value_usd, duration_minutes, bybit_entry_order_id, 
                 bybit_exit_order_id, fees_paid, ai_entry_reasoning, ai_exit_reasoning) = trade
            else:  # Old schema without AI reasoning
                (trade_id, symbol, direction, entry_price, exit_price, quantity, leverage,
                 entry_time, exit_time, exit_reason, pnl, pnl_percentage, indicators,
                 position_value_usd, duration_minutes, bybit_entry_order_id, 
                 bybit_exit_order_id, fees_paid) = trade
                ai_entry_reasoning = ""
                ai_exit_reasoning = ""
            
            result.append({
                'id': trade_id,
                'symbol': symbol,
                'direction': direction,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'quantity': quantity,
                'leverage': leverage,
                'entry_time': entry_time,
                'exit_time': exit_time,
                'exit_reason': exit_reason,
                'pnl': pnl,
                'pnl_percentage': pnl_percentage,
                'indicators': json.loads(indicators) if indicators else {},
                'position_value_usd': position_value_usd,
                'duration_minutes': duration_minutes,
                'fees_paid': fees_paid or 0,
                'ai_entry_reasoning': ai_entry_reasoning,
                'ai_exit_reasoning': ai_exit_reasoning
            })
        
        conn.close()
        return result
    
    def get_closed_positions(self) -> List[Dict]:
        """Get closed positions (alias for get_trade_history for compatibility)"""
        return self.get_trade_history(1000)  # Get all closed positions
    
    def get_performance_metrics(self) -> Dict:
        """Get performance metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM performance_metrics ORDER BY date DESC LIMIT 1')
        metrics = cursor.fetchone()
        
        if metrics:
            (date, total_trades, winning_trades, losing_trades, total_pnl,
             max_drawdown, balance, win_rate, avg_win, avg_loss, profit_factor, total_fees) = metrics
            
            # Get starting balance for ROI calculation
            starting_balance = self.get_real_balance()  # Real balance dari Bybit
            
            # Calculate ROI Account = Total PnL / Starting Balance
            roi_account = (total_pnl / starting_balance) * 100 if starting_balance > 0 else 0
            
            result = {
                'date': date,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'total_pnl': total_pnl,
                'roi_account': roi_account,  # ROI Account untuk evaluasi performa
                'max_drawdown': max_drawdown,
                'balance': balance,
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor,
                'total_fees': total_fees or 0,
                'starting_balance': starting_balance
            }
        else:
            # No trades yet, get real balance from Bybit
            real_balance = self.get_real_balance()
            
            result = {
                'date': datetime.now().date().isoformat(),
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': 0,
                'roi_account': 0,  # ROI Account untuk evaluasi performa
                'max_drawdown': 0,
                'balance': real_balance,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'total_fees': 0,
                'starting_balance': real_balance
            }
        
        conn.close()
        return result

# Global instance
real_trade_system = RealTradeSystem()