"""
Dry Run Trading System - Simulasi trading dengan tracking lengkap
"""
import json
import sqlite3
from datetime import datetime, timedelta, timezone

# WIB = UTC+7
WIB = timezone(timedelta(hours=7))

def now_wib() -> datetime:
    return datetime.now(WIB)
import uuid
from typing import Dict, List, Optional
import asyncio
import os
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get balance from environment
BALANCE_USD = float(os.getenv('BALANCE_USD', '1000'))

# Global socketio instance (will be set by dashboard_app.py)
_socketio_instance = None

def set_socketio_instance(socketio):
    """Set the socketio instance for real-time notifications"""
    global _socketio_instance
    _socketio_instance = socketio

def get_socketio_instance():
    """Get the socketio instance"""
    return _socketio_instance

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Initialize Telegram bot if credentials are available
telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None

class DryRunSystem:
    def __init__(self, db_path="dry_run_trades.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)  # Add timeout
        cursor = conn.cursor()
        
        # Enable WAL mode for better concurrent access
        cursor.execute('PRAGMA journal_mode=WAL;')
        cursor.execute('PRAGMA synchronous=NORMAL;')
        cursor.execute('PRAGMA cache_size=10000;')
        cursor.execute('PRAGMA temp_store=memory;')
        
        # Table untuk open positions
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
                ai_entry_reasoning TEXT,
                market_cap REAL DEFAULT 0,
                market_cap_rank INTEGER DEFAULT 0,
                total_volume_24h REAL DEFAULT 0,
                circulating_supply REAL DEFAULT 0,
                total_supply REAL DEFAULT 0,
                max_supply REAL DEFAULT 0,
                price_change_24h REAL DEFAULT 0,
                price_change_percentage_24h REAL DEFAULT 0,
                price_change_percentage_7d REAL DEFAULT 0,
                price_change_percentage_30d REAL DEFAULT 0,
                ath REAL DEFAULT 0,
                ath_change_percentage REAL DEFAULT 0,
                atl REAL DEFAULT 0,
                atl_change_percentage REAL DEFAULT 0,
                bybit_volume_24h REAL DEFAULT 0,
                bybit_turnover_24h REAL DEFAULT 0,
                liquidity_score REAL DEFAULT 0,
                volatility_score REAL DEFAULT 0,
                market_dominance REAL DEFAULT 0,
                market_cap_category TEXT DEFAULT '',
                volume_category TEXT DEFAULT '',
                market_data_timestamp TEXT DEFAULT '',
                trading_session TEXT DEFAULT 'UNKNOWN',
                strategy_name TEXT DEFAULT 'ICT_SMC'
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
                ai_entry_reasoning TEXT,
                ai_exit_reasoning TEXT,
                market_cap REAL DEFAULT 0,
                market_cap_rank INTEGER DEFAULT 0,
                total_volume_24h REAL DEFAULT 0,
                circulating_supply REAL DEFAULT 0,
                total_supply REAL DEFAULT 0,
                max_supply REAL DEFAULT 0,
                price_change_24h REAL DEFAULT 0,
                price_change_percentage_24h REAL DEFAULT 0,
                price_change_percentage_7d REAL DEFAULT 0,
                price_change_percentage_30d REAL DEFAULT 0,
                ath REAL DEFAULT 0,
                ath_change_percentage REAL DEFAULT 0,
                atl REAL DEFAULT 0,
                atl_change_percentage REAL DEFAULT 0,
                bybit_volume_24h REAL DEFAULT 0,
                bybit_turnover_24h REAL DEFAULT 0,
                liquidity_score REAL DEFAULT 0,
                volatility_score REAL DEFAULT 0,
                market_dominance REAL DEFAULT 0,
                market_cap_category TEXT DEFAULT '',
                volume_category TEXT DEFAULT '',
                market_data_timestamp TEXT DEFAULT '',
                trading_session TEXT DEFAULT 'UNKNOWN',
                strategy_name TEXT DEFAULT 'ICT_SMC'
            )
        ''')
        
        # Table untuk performance metrics
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                date TEXT PRIMARY KEY,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                total_pnl REAL DEFAULT 0,
                max_drawdown REAL DEFAULT 0,
                balance REAL DEFAULT {BALANCE_USD},
                win_rate REAL DEFAULT 0,
                avg_win REAL DEFAULT 0,
                avg_loss REAL DEFAULT 0,
                profit_factor REAL DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()

        # Migration: tambah kolom strategy_name jika belum ada (untuk DB lama)
        self._migrate_add_strategy_column()

    def _migrate_add_strategy_column(self):
        """Add strategy_name column to existing databases"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        cursor = conn.cursor()
        for table in ('open_positions', 'trade_history'):
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN strategy_name TEXT DEFAULT 'ICT_SMC'")
            except Exception:
                pass  # Column already exists
        conn.commit()
        conn.close()

    async def open_position(self, signal: Dict) -> str:
        """Open new position"""
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
                
                # Get market data for this symbol
                try:
                    from market_data_system import get_market_data_system
                    from trading_session_system import get_session_analyzer
                    market_system = get_market_data_system()
                    session_analyzer = get_session_analyzer()
                    market_data = await market_system.get_market_data(signal['symbol'])
                    
                    # Get trading session for current time
                    current_time = now_wib().isoformat()
                    trading_session = session_analyzer.get_trading_session(current_time)
                    
                except Exception as e:
                    print(f"⚠️ Could not get market data for {signal['symbol']}: {e}")
                    market_data = {}
                    trading_session = 'UNKNOWN'
                
                cursor.execute('''
                    INSERT INTO open_positions 
                    (id, symbol, direction, entry_price, quantity, leverage, tp_price, sl_price, 
                     entry_time, current_price, unrealized_pnl, indicators, position_value_usd, ai_entry_reasoning,
                     market_cap, market_cap_rank, total_volume_24h, circulating_supply, total_supply, max_supply,
                     price_change_24h, price_change_percentage_24h, price_change_percentage_7d, price_change_percentage_30d,
                     ath, ath_change_percentage, atl, atl_change_percentage, bybit_volume_24h, bybit_turnover_24h,
                     liquidity_score, volatility_score, market_dominance, market_cap_category, volume_category, market_data_timestamp, trading_session, strategy_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    position_id, signal['symbol'], signal['direction'], signal['close'],
                    signal['pos_size'], signal['leverage'], signal['tp'], signal['sl'],
                    now_wib().isoformat(), signal['close'], 0.0, json.dumps(indicators),
                    signal['position_value_usd'], signal.get('ai_entry_reasoning', ''),
                    # Market data
                    market_data.get('market_cap', 0),
                    market_data.get('market_cap_rank', 0),
                    market_data.get('total_volume_24h', 0),
                    market_data.get('circulating_supply', 0),
                    market_data.get('total_supply', 0),
                    market_data.get('max_supply', 0),
                    market_data.get('price_change_24h', 0),
                    market_data.get('price_change_percentage_24h', 0),
                    market_data.get('price_change_percentage_7d', 0),
                    market_data.get('price_change_percentage_30d', 0),
                    market_data.get('ath', 0),
                    market_data.get('ath_change_percentage', 0),
                    market_data.get('atl', 0),
                    market_data.get('atl_change_percentage', 0),
                    market_data.get('bybit_volume_24h', 0),
                    market_data.get('bybit_turnover_24h', 0),
                    market_data.get('liquidity_score', 0),
                    market_data.get('volatility_score', 0),
                    market_data.get('market_dominance', 0),
                    market_system.categorize_market_cap(market_data.get('market_cap', 0)) if market_data else "",
                    market_system.categorize_volume(market_data.get('total_volume_24h', 0)) if market_data else "",
                    market_data.get('timestamp', ''),
                    trading_session,
                    signal.get('strategy', 'ICT_SMC')
                ))
        
                conn.commit()
                conn.close()
                
                print(f"🚀 [DRY RUN] Opened {signal['direction']} position for {signal['symbol']}")
                
                # Send notification using file-based system
                try:
                    from notification_system import send_notification
                    send_notification('position_opened', {
                        'symbol': signal['symbol'],
                        'direction': signal['direction'],
                        'entry_price': signal['close'],
                        'tp_price': signal['tp'],
                        'sl_price': signal['sl'],
                        'leverage': signal['leverage'],
                        'position_value_usd': signal['position_value_usd'],
                        'strategy_name': signal.get('strategy', 'ICT_SMC'),
                        'strategy_label': signal.get('strategy_label', '📐 ICT/SMC'),
                        'mode': 'dry-run'
                    })
                except Exception as e:
                    print(f"⚠️ Failed to send notification: {e}")
                
                return position_id
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    print(f"⚠️  Database locked, retrying... ({attempt + 1}/{max_retries})")
                    time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    print(f"❌ Database error after {attempt + 1} attempts: {e}")
                    raise
            except Exception as e:
                print(f"❌ Unexpected error opening position: {e}")
                raise
    
    async def update_positions(self, current_prices: Dict[str, float]):
        """Update current prices and check for TP/SL hits"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=30.0)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
        
                cursor.execute('SELECT * FROM open_positions')
                positions = cursor.fetchall()
                
                for pos in positions:
                    pos_id = pos['id']
                    symbol = pos['symbol']
                    direction = pos['direction']
                    entry_price = pos['entry_price']
                    quantity = pos['quantity']
                    leverage = pos['leverage']
                    tp_price = pos['tp_price']
                    sl_price = pos['sl_price']
                    entry_time = pos['entry_time']
                    ai_entry_reasoning = pos['ai_entry_reasoning'] if 'ai_entry_reasoning' in pos.keys() else ''

                    if symbol in current_prices:
                        current_price = current_prices[symbol]
                        
                        if not all([current_price, entry_price, quantity, tp_price, sl_price]):
                            print(f"⚠️  Skipping {symbol}: Missing data")
                            continue
                        
                        try:
                            current_price = float(current_price)
                            entry_price = float(entry_price)
                            quantity = float(quantity)
                            tp_price = float(tp_price)
                            sl_price = float(sl_price)
                        except (TypeError, ValueError) as e:
                            print(f"⚠️  Skipping {symbol}: Invalid data types - {e}")
                            continue
                        
                        try:
                            if direction == "LONG":
                                pnl = (current_price - entry_price) * quantity
                                if current_price >= tp_price:
                                    ai_exit_reasoning = await self._generate_exit_reasoning(pos, current_price, "TP_HIT")
                                    self._close_position(pos_id, current_price, "TP_HIT", conn, ai_exit_reasoning)
                                    continue
                                elif current_price <= sl_price:
                                    ai_exit_reasoning = await self._generate_exit_reasoning(pos, current_price, "SL_HIT")
                                    self._close_position(pos_id, current_price, "SL_HIT", conn, ai_exit_reasoning)
                                    continue
                            else:  # SHORT
                                pnl = (entry_price - current_price) * quantity
                                if current_price <= tp_price:
                                    ai_exit_reasoning = await self._generate_exit_reasoning(pos, current_price, "TP_HIT")
                                    self._close_position(pos_id, current_price, "TP_HIT", conn, ai_exit_reasoning)
                                    continue
                                elif current_price >= sl_price:
                                    ai_exit_reasoning = await self._generate_exit_reasoning(pos, current_price, "SL_HIT")
                                    self._close_position(pos_id, current_price, "SL_HIT", conn, ai_exit_reasoning)
                                    continue
                        except Exception as calc_error:
                            print(f"❌ Error calculating PnL for {symbol}: {calc_error}")
                            continue
                        
                        cursor.execute('''
                            UPDATE open_positions 
                            SET current_price = ?, unrealized_pnl = ?
                            WHERE id = ?
                        ''', (current_price, pnl, pos_id))
                
                conn.commit()
                conn.close()
                break
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    await asyncio.sleep(0.1 * (attempt + 1))
                    continue
                else:
                    raise
            except Exception as e:
                print(f"❌ Unexpected error updating positions: {e}")
                raise
    
    def _close_position(self, position_id: str, exit_price: float, exit_reason: str, conn, ai_exit_reasoning: str = ""):
        """Close position and move to history"""
        cursor = conn.cursor()
        
        # Get position data
        cursor.execute('SELECT * FROM open_positions WHERE id = ?', (position_id,))
        pos = cursor.fetchone()
        
        if pos:
            # Handle different database schemas (old vs new with market data and trading session)
            if len(pos) >= 37:  # New schema with market data and trading session
                (pos_id, symbol, direction, entry_price, quantity, leverage, 
                 tp_price, sl_price, entry_time, _, _, indicators, position_value_usd, ai_entry_reasoning,
                 market_cap, market_cap_rank, total_volume_24h, circulating_supply, total_supply, max_supply,
                 price_change_24h, price_change_percentage_24h, price_change_percentage_7d, price_change_percentage_30d,
                 ath, ath_change_percentage, atl, atl_change_percentage, bybit_volume_24h, bybit_turnover_24h,
                 liquidity_score, volatility_score, market_dominance, market_cap_category, volume_category, market_data_timestamp, trading_session) = pos
            elif len(pos) >= 36:  # New schema with market data but no trading session
                (pos_id, symbol, direction, entry_price, quantity, leverage, 
                 tp_price, sl_price, entry_time, _, _, indicators, position_value_usd, ai_entry_reasoning,
                 market_cap, market_cap_rank, total_volume_24h, circulating_supply, total_supply, max_supply,
                 price_change_24h, price_change_percentage_24h, price_change_percentage_7d, price_change_percentage_30d,
                 ath, ath_change_percentage, atl, atl_change_percentage, bybit_volume_24h, bybit_turnover_24h,
                 liquidity_score, volatility_score, market_dominance, market_cap_category, volume_category, market_data_timestamp) = pos
                # Get trading session from entry time
                try:
                    from trading_session_system import get_session_analyzer
                    session_analyzer = get_session_analyzer()
                    trading_session = session_analyzer.get_trading_session(entry_time)
                except:
                    trading_session = 'UNKNOWN'
            elif len(pos) >= 14:  # Old schema with AI reasoning but no market data
                (pos_id, symbol, direction, entry_price, quantity, leverage, 
                 tp_price, sl_price, entry_time, _, _, indicators, position_value_usd, ai_entry_reasoning) = pos
                # Set default market data values
                (market_cap, market_cap_rank, total_volume_24h, circulating_supply, total_supply, max_supply,
                 price_change_24h, price_change_percentage_24h, price_change_percentage_7d, price_change_percentage_30d,
                 ath, ath_change_percentage, atl, atl_change_percentage, bybit_volume_24h, bybit_turnover_24h,
                 liquidity_score, volatility_score, market_dominance, market_cap_category, volume_category, market_data_timestamp) = [0] * 20 + ["", ""]
                # Get trading session from entry time
                try:
                    from trading_session_system import get_session_analyzer
                    session_analyzer = get_session_analyzer()
                    trading_session = session_analyzer.get_trading_session(entry_time)
                except:
                    trading_session = 'UNKNOWN'
            else:  # Very old schema without AI reasoning and market data
                (pos_id, symbol, direction, entry_price, quantity, leverage, 
                 tp_price, sl_price, entry_time, _, _, indicators, position_value_usd) = pos
                ai_entry_reasoning = ""
                # Set default market data values
                (market_cap, market_cap_rank, total_volume_24h, circulating_supply, total_supply, max_supply,
                 price_change_24h, price_change_percentage_24h, price_change_percentage_7d, price_change_percentage_30d,
                 ath, ath_change_percentage, atl, atl_change_percentage, bybit_volume_24h, bybit_turnover_24h,
                 liquidity_score, volatility_score, market_dominance, market_cap_category, volume_category, market_data_timestamp) = [0] * 20 + ["", ""]
                # Get trading session from entry time
                try:
                    from trading_session_system import get_session_analyzer
                    session_analyzer = get_session_analyzer()
                    trading_session = session_analyzer.get_trading_session(entry_time)
                except:
                    trading_session = 'UNKNOWN'
            
            # Calculate final PnL
            if direction == "LONG":
                pnl = (exit_price - entry_price) * quantity
            else:  # SHORT
                pnl = (entry_price - exit_price) * quantity
            
            # Calculate PnL percentage relative to MARGIN USED (bukan risk amount)
            # Margin = Position Value / Leverage
            leverage = pos[5]  # leverage
            position_value_usd = pos[12]  # position_value_usd
            margin_used = position_value_usd / leverage if leverage > 0 else position_value_usd
            pnl_percentage = (pnl / margin_used) * 100 if margin_used > 0 else 0
            
            # Calculate duration
            entry_dt = datetime.fromisoformat(entry_time)
            exit_dt = now_wib()
            # Handle naive entry_dt (lama tanpa timezone)
            if entry_dt.tzinfo is None:
                entry_dt = entry_dt.replace(tzinfo=WIB)
            duration_minutes = int((exit_dt - entry_dt).total_seconds() / 60)
            
            # Get strategy_name from open position (column index 37 if exists)
            strategy_name = 'ICT_SMC'
            try:
                if len(pos) >= 39:
                    strategy_name = pos[38] or 'ICT_SMC'
            except Exception:
                pass

            # Move to history
            cursor.execute('''
                INSERT INTO trade_history 
                (id, symbol, direction, entry_price, exit_price, quantity, leverage,
                 entry_time, exit_time, exit_reason, pnl, pnl_percentage, indicators,
                 position_value_usd, duration_minutes, ai_entry_reasoning, ai_exit_reasoning,
                 market_cap, market_cap_rank, total_volume_24h, circulating_supply, total_supply, max_supply,
                 price_change_24h, price_change_percentage_24h, price_change_percentage_7d, price_change_percentage_30d,
                 ath, ath_change_percentage, atl, atl_change_percentage, bybit_volume_24h, bybit_turnover_24h,
                 liquidity_score, volatility_score, market_dominance, market_cap_category, volume_category, market_data_timestamp, trading_session, strategy_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pos_id, symbol, direction, entry_price, exit_price, quantity, leverage,
                entry_time, exit_dt.isoformat(), exit_reason, pnl, pnl_percentage,
                indicators, position_value_usd, duration_minutes, 
                ai_entry_reasoning, ai_exit_reasoning,
                # Copy market data from open position (use existing values from when position was opened)
                market_cap, market_cap_rank, total_volume_24h, circulating_supply, total_supply, max_supply,
                price_change_24h, price_change_percentage_24h, price_change_percentage_7d, price_change_percentage_30d,
                ath, ath_change_percentage, atl, atl_change_percentage, bybit_volume_24h, bybit_turnover_24h,
                liquidity_score, volatility_score, market_dominance, market_cap_category, volume_category, market_data_timestamp,
                trading_session, strategy_name
            ))
            
            # Remove from open positions
            cursor.execute('DELETE FROM open_positions WHERE id = ?', (position_id,))
            
            # Update performance metrics
            self._update_performance_metrics(conn)
            
            print(f"✅ [DRY RUN] Closed {direction} {symbol} - {exit_reason} - PnL: ${pnl:.2f} ({pnl_percentage:.2f}%)")
            
            # Record trade result for conditional risk system
            try:
                from conditional_risk_system import record_trade_result
                from session_management_system import get_current_session_parameters
                
                # Get current session (when trade is closing, not when it was opened)
                current_session_params = get_current_session_parameters()
                session = current_session_params['session']
                
                # Fix session name mapping for conditional risk system
                session_mapping = {
                    'DEAD_ZONE': 'DEAD_ZONE',
                    'ASIA': 'ASIA', 
                    'LONDON': 'LONDON',
                    'NEWYORK': 'NEWYORK',  # Map NEW_YORK to NEWYORK
                    'NEW_YORK': 'NEWYORK'  # Handle both variants
                }
                
                mapped_session = session_mapping.get(session, session)
                
                # Calculate risk percentage used (approximate from position size)
                # This is an approximation since we don't store the exact risk used
                risk_used = (margin_used / self.get_current_balance()) * 100 if self.get_current_balance() > 0 else 0.5
                
                record_trade_result(mapped_session, pnl, risk_used)
                print(f"📊 Trade result recorded: {mapped_session} session, PnL=${pnl:.2f}, Risk≈{risk_used:.1f}%")
            except Exception as e:
                print(f"⚠️ Failed to record trade result for conditional risk: {e}")
            
            # Send notification using file-based system
            try:
                from notification_system import send_notification
                send_notification('position_closed', {
                    'symbol': symbol,
                    'direction': direction,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'exit_reason': exit_reason,
                    'pnl': pnl,
                    'pnl_percentage': pnl_percentage,
                    'duration_minutes': duration_minutes,
                    'strategy_name': strategy_name,
                    'mode': 'dry-run'
                })
            except Exception as e:
                print(f"⚠️ Failed to send notification: {e}")
            
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
            
    async def _generate_exit_reasoning(self, pos, exit_price: float, exit_reason: str) -> str:
        """Generate AI exit reasoning for position closure"""
        try:
            from gemini_ai_system import get_gemini_analyst
            
            gemini_analyst = get_gemini_analyst()
            if not gemini_analyst:
                print(f"❌ CRITICAL: Gemini analyst not available for {pos[1] if len(pos) > 1 else 'N/A'}")
                print("🔄 Attempting to reinitialize Gemini AI...")
                
                # Force reinitialize
                try:
                    from gemini_ai_system import GeminiMarketAnalyst
                    gemini_analyst = GeminiMarketAnalyst()
                    print("✅ Gemini AI reinitialized successfully")
                except Exception as init_error:
                    print(f"❌ Failed to reinitialize Gemini AI: {init_error}")
                    raise Exception(f"Gemini AI is required but unavailable: {init_error}")
            
            if not gemini_analyst:
                raise Exception("Gemini AI is required for exit reasoning but could not be initialized")
            
            # Calculate PnL correctly
            realized_pnl = (exit_price - pos[3]) * pos[4] if pos[2] == "LONG" else (pos[3] - exit_price) * pos[4]
            
            # Calculate PnL percentage relative to margin used (consistent with other systems)
            position_value = pos[3] * pos[4]  # entry_price * quantity
            leverage = pos[5]  # leverage
            margin_used = position_value / leverage if leverage > 0 else position_value
            pnl_percentage = (realized_pnl / margin_used) * 100 if margin_used > 0 else 0
            
            # Prepare position data for AI analysis with ALL stored market data
            position_data = {
                'symbol': pos[1],  # symbol
                'direction': pos[2],  # direction
                'entry_price': pos[3],  # entry_price
                'exit_price': exit_price,
                'entry_time': pos[8],  # entry_time
                'realized_pnl': realized_pnl,
                'pnl_percentage': pnl_percentage,
                'entry_indicators': json.loads(pos[11]) if pos[11] and str(pos[11]).strip() else {},  # indicators
                
                # CRITICAL: Add all market data that was stored at entry
                'market_cap': pos[14] if len(pos) > 14 else 0,
                'market_cap_rank': pos[15] if len(pos) > 15 else 0,
                'total_volume_24h': pos[16] if len(pos) > 16 else 0,
                'circulating_supply': pos[17] if len(pos) > 17 else 0,
                'total_supply': pos[18] if len(pos) > 18 else 0,
                'max_supply': pos[19] if len(pos) > 19 else 0,
                'price_change_24h': pos[20] if len(pos) > 20 else 0,
                'price_change_percentage_24h': pos[21] if len(pos) > 21 else 0,
                'price_change_percentage_7d': pos[22] if len(pos) > 22 else 0,
                'price_change_percentage_30d': pos[23] if len(pos) > 23 else 0,
                'ath': pos[24] if len(pos) > 24 else 0,
                'ath_change_percentage': pos[25] if len(pos) > 25 else 0,
                'atl': pos[26] if len(pos) > 26 else 0,
                'atl_change_percentage': pos[27] if len(pos) > 27 else 0,
                'bybit_volume_24h': pos[28] if len(pos) > 28 else 0,
                'bybit_turnover_24h': pos[29] if len(pos) > 29 else 0,
                'liquidity_score': pos[30] if len(pos) > 30 else 0,
                'volatility_score': pos[31] if len(pos) > 31 else 0,
                'market_dominance': pos[32] if len(pos) > 32 else 0,
                'market_cap_category': pos[33] if len(pos) > 33 else '',
                'volume_category': pos[34] if len(pos) > 34 else '',
                'market_data_timestamp': pos[35] if len(pos) > 35 else '',
                'trading_session': pos[36] if len(pos) > 36 else 'UNKNOWN'
            }
            
            # Generate AI exit reasoning
            exit_reasoning = await gemini_analyst.generate_exit_reasoning(position_data, exit_reason)
            return exit_reasoning
            
        except Exception as e:
            print(f"⚠️  Failed to generate exit reasoning: {e}")
            import traceback
            traceback.print_exc()
            
            # Return proper format even on error
            symbol = pos[1] if len(pos) > 1 else 'N/A'
            direction = pos[2] if len(pos) > 2 else 'N/A'
            
            return f"""<b>📊 Ringkasan Eksekusi:</b><br>
Posisi {direction} pada {symbol} ditutup dengan alasan {exit_reason}. Analisis AI tidak tersedia karena error sistem, namun posisi telah ditutup sesuai dengan strategi risk management.<br><br>

<b>📈 Analisis Market:</b><br>
Kondisi market saat exit memerlukan evaluasi manual karena sistem AI mengalami gangguan sementara.<br><br>

<b>🔍 Evaluasi Teknikal:</b><br>
Indikator teknikal dan sinyal entry perlu dievaluasi secara manual untuk memahami hasil trade ini.<br><br>

<b>💡 Insight dan Rekomendasi:</b><br>
Meskipun analisis AI tidak tersedia, trade ini tetap mengikuti protokol risk management yang telah ditetapkan. Lakukan evaluasi manual untuk pembelajaran selanjutnya."""
    
    
    def _update_performance_metrics(self, conn):
        """Update daily performance metrics with dynamic balance"""
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
                AVG(CASE WHEN pnl < 0 THEN pnl ELSE NULL END) as avg_loss
            FROM trade_history
        ''')
        
        metrics = cursor.fetchone()
        if metrics and metrics[0] > 0:  # If there are trades
            total_trades, winning_trades, losing_trades, total_pnl, avg_win, avg_loss = metrics
            
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if avg_loss and losing_trades > 0 else 0
            
            # Calculate max drawdown with dynamic balance
            cursor.execute('SELECT pnl FROM trade_history ORDER BY exit_time')
            pnls = [row[0] for row in cursor.fetchall()]
            
            max_drawdown = 0
            peak = BALANCE_USD  # Starting balance from env
            current_balance = BALANCE_USD
            
            for pnl in pnls:
                current_balance += pnl
                if current_balance > peak:
                    peak = current_balance
                drawdown = (peak - current_balance) / peak * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            # Insert or update metrics with dynamic balance
            cursor.execute('''
                INSERT OR REPLACE INTO performance_metrics
                (date, total_trades, winning_trades, losing_trades, total_pnl,
                 max_drawdown, balance, win_rate, avg_win, avg_loss, profit_factor)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                today, total_trades, winning_trades, losing_trades, total_pnl,
                max_drawdown, current_balance, win_rate, avg_win or 0, avg_loss or 0, profit_factor
            ))
    
    def get_open_positions(self) -> List[Dict]:
        """Get all open positions ordered by newest first"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM open_positions ORDER BY entry_time DESC')
        positions = cursor.fetchall()
        
        result = []
        for pos in positions:
            indicators_raw = pos['indicators'] if 'indicators' in pos.keys() else ''
            try:
                indicators_parsed = json.loads(indicators_raw) if indicators_raw and str(indicators_raw).strip() else {}
            except (json.JSONDecodeError, TypeError):
                indicators_parsed = {}

            result.append({
                'id': pos['id'],
                'symbol': pos['symbol'],
                'direction': pos['direction'],
                'entry_price': pos['entry_price'],
                'current_price': pos['current_price'] or pos['entry_price'],
                'quantity': pos['quantity'],
                'leverage': pos['leverage'],
                'tp_price': pos['tp_price'],
                'sl_price': pos['sl_price'],
                'entry_time': pos['entry_time'],
                'unrealized_pnl': pos['unrealized_pnl'] or 0,
                'indicators': indicators_parsed,
                'position_value_usd': pos['position_value_usd'],
                'ai_entry_reasoning': pos['ai_entry_reasoning'] if 'ai_entry_reasoning' in pos.keys() else '',
                'trading_session': pos['trading_session'] if 'trading_session' in pos.keys() else 'UNKNOWN',
                'strategy_name': pos['strategy_name'] if 'strategy_name' in pos.keys() else 'ICT_SMC',
            })
        
        conn.close()
        return result
    
    def get_trade_history(self, limit: int = 50) -> List[Dict]:
        """Get trade history with AI reasoning and market data"""
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
            # Handle different schema lengths (old vs new with market data and trading session)
            if len(trade) >= 39:  # New schema with market data and trading session
                (trade_id, symbol, direction, entry_price, exit_price, quantity, leverage,
                 entry_time, exit_time, exit_reason, pnl, pnl_percentage, indicators,
                 position_value_usd, duration_minutes, ai_entry_reasoning, ai_exit_reasoning,
                 market_cap, market_cap_rank, total_volume_24h, circulating_supply, total_supply, max_supply,
                 price_change_24h, price_change_percentage_24h, price_change_percentage_7d, price_change_percentage_30d,
                 ath, ath_change_percentage, atl, atl_change_percentage, bybit_volume_24h, bybit_turnover_24h,
                 liquidity_score, volatility_score, market_dominance, market_cap_category, volume_category, market_data_timestamp, trading_session) = trade
            elif len(trade) >= 38:  # New schema with market data but no trading session
                (trade_id, symbol, direction, entry_price, exit_price, quantity, leverage,
                 entry_time, exit_time, exit_reason, pnl, pnl_percentage, indicators,
                 position_value_usd, duration_minutes, ai_entry_reasoning, ai_exit_reasoning,
                 market_cap, market_cap_rank, total_volume_24h, circulating_supply, total_supply, max_supply,
                 price_change_24h, price_change_percentage_24h, price_change_percentage_7d, price_change_percentage_30d,
                 ath, ath_change_percentage, atl, atl_change_percentage, bybit_volume_24h, bybit_turnover_24h,
                 liquidity_score, volatility_score, market_dominance, market_cap_category, volume_category, market_data_timestamp) = trade
                # Get trading session from entry time
                try:
                    from trading_session_system import get_session_analyzer
                    session_analyzer = get_session_analyzer()
                    trading_session = session_analyzer.get_trading_session(entry_time)
                except:
                    trading_session = 'UNKNOWN'
            elif len(trade) >= 17:  # Old schema with AI reasoning but no market data
                (trade_id, symbol, direction, entry_price, exit_price, quantity, leverage,
                 entry_time, exit_time, exit_reason, pnl, pnl_percentage, indicators,
                 position_value_usd, duration_minutes, ai_entry_reasoning, ai_exit_reasoning) = trade
                # Set default market data values
                (market_cap, market_cap_rank, total_volume_24h, circulating_supply, total_supply, max_supply,
                 price_change_24h, price_change_percentage_24h, price_change_percentage_7d, price_change_percentage_30d,
                 ath, ath_change_percentage, atl, atl_change_percentage, bybit_volume_24h, bybit_turnover_24h,
                 liquidity_score, volatility_score, market_dominance, market_cap_category, volume_category, market_data_timestamp) = [0] * 20 + ["", ""]
                # Get trading session from entry time
                try:
                    from trading_session_system import get_session_analyzer
                    session_analyzer = get_session_analyzer()
                    trading_session = session_analyzer.get_trading_session(entry_time)
                except:
                    trading_session = 'UNKNOWN'
            else:  # Very old schema without AI reasoning and market data
                (trade_id, symbol, direction, entry_price, exit_price, quantity, leverage,
                 entry_time, exit_time, exit_reason, pnl, pnl_percentage, indicators,
                 position_value_usd, duration_minutes) = trade
                ai_entry_reasoning = ""
                ai_exit_reasoning = ""
                # Set default market data values
                (market_cap, market_cap_rank, total_volume_24h, circulating_supply, total_supply, max_supply,
                 price_change_24h, price_change_percentage_24h, price_change_percentage_7d, price_change_percentage_30d,
                 ath, ath_change_percentage, atl, atl_change_percentage, bybit_volume_24h, bybit_turnover_24h,
                 liquidity_score, volatility_score, market_dominance, market_cap_category, volume_category, market_data_timestamp) = [0] * 20 + ["", ""]
                # Get trading session from entry time
                try:
                    from trading_session_system import get_session_analyzer
                    session_analyzer = get_session_analyzer()
                    trading_session = session_analyzer.get_trading_session(entry_time)
                except:
                    trading_session = 'UNKNOWN'
            
            # Extract strategy_name — column index 40 in new schema (after trading_session at 39)
            strategy_name = 'ICT_SMC'
            try:
                if len(trade) >= 41:
                    strategy_name = trade[40] or 'ICT_SMC'
            except Exception:
                pass

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
                'indicators': json.loads(indicators) if indicators and indicators.strip() else {},
                # Market data
                'market_cap': market_cap,
                'market_cap_rank': market_cap_rank,
                'total_volume_24h': total_volume_24h,
                'liquidity_score': liquidity_score,
                'volatility_score': volatility_score,
                'market_dominance': market_dominance,
                'market_cap_category': market_cap_category,
                'volume_category': volume_category,
                'trading_session': trading_session,
                'strategy_name': strategy_name,
                'ai_entry_reasoning': ai_entry_reasoning or '',
                'ai_exit_reasoning': ai_exit_reasoning or '',
                'position_value_usd': position_value_usd,
                'duration_minutes': duration_minutes,
            })
        
        conn.close()
        return result
    
    def get_closed_positions(self) -> List[Dict]:
        """Get closed positions (alias for get_trade_history for compatibility)"""
        return self.get_trade_history(1000)  # Get all closed positions
    
    def get_current_balance(self) -> float:
        """Get current dynamic balance (starting balance + total PnL)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate total PnL from all closed trades
        cursor.execute('SELECT SUM(pnl) FROM trade_history')
        result = cursor.fetchone()
        total_pnl = result[0] if result and result[0] is not None else 0
        
        conn.close()
        
        # Get starting balance from environment
        import os
        from dotenv import load_dotenv
        load_dotenv()
        starting_balance = float(os.getenv('BALANCE_USD', '1167'))
        
        # Current balance = starting balance + total PnL
        current_balance = starting_balance + total_pnl
        
        print(f"💰 Dynamic Balance: Starting ${starting_balance:.2f} + PnL ${total_pnl:.2f} = ${current_balance:.2f}")
        
        return current_balance
    
    def get_performance_metrics(self) -> Dict:
        """Get performance metrics with dynamic balance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT date, total_trades, winning_trades, losing_trades, total_pnl, win_rate, profit_factor, max_drawdown, balance FROM performance_metrics ORDER BY date DESC LIMIT 1')
        metrics = cursor.fetchone()
        
        # Get current dynamic balance
        current_balance = self.get_current_balance()
        
        if metrics:
            (date, total_trades, winning_trades, losing_trades, total_pnl,
             win_rate, profit_factor, max_drawdown, balance) = metrics
            avg_win = 0
            avg_loss = 0
            
            # Calculate ROI Account = Total PnL / Starting Balance
            import os
            from dotenv import load_dotenv
            load_dotenv()
            starting_balance = float(os.getenv('BALANCE_USD', '1000'))
            roi_account = (total_pnl / starting_balance) * 100 if starting_balance > 0 else 0
            
            result = {
                'date': date,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'total_pnl': total_pnl,
                'roi_account': roi_account,
                'max_drawdown': max_drawdown,
                'balance': current_balance,
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor,
                'starting_balance': starting_balance
            }
        else:
            import os
            from dotenv import load_dotenv
            load_dotenv()
            starting_balance = float(os.getenv('BALANCE_USD', '1000'))
            result = {
                'date': datetime.now().date().isoformat(),
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': 0,
                'roi_account': 0,
                'max_drawdown': 0,
                'balance': current_balance,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'starting_balance': starting_balance
            }
        
        conn.close()
        return result

# Global instance
dry_run_system = DryRunSystem()