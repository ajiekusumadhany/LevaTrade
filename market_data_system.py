#!/usr/bin/env python3
"""
Market Data System
Mengambil dan menyimpan data volume, market cap, dan metrics lainnya untuk analisis
"""
import asyncio
import aiohttp
import sqlite3
import json
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

class MarketDataSystem:
    def __init__(self):
        self.coingecko_api_key = os.getenv('COINGECKO_API_KEY', '')  # Optional API key for higher limits
        self.cache_duration = 300  # 5 minutes cache
        self.market_data_cache = {}
        
        # Symbol mapping untuk CoinGecko (USDT pairs ke coin ID)
        self.symbol_mapping = {
            'BTCUSDT': 'bitcoin',
            'ETHUSDT': 'ethereum',
            'ADAUSDT': 'cardano',
            'DOTUSDT': 'polkadot',
            'LINKUSDT': 'chainlink',
            'LTCUSDT': 'litecoin',
            'BCHUSDT': 'bitcoin-cash',
            'XLMUSDT': 'stellar',
            'EOSUSDT': 'eos',
            'TRXUSDT': 'tron',
            'XRPUSDT': 'ripple',
            'BNBUSDT': 'binancecoin',
            'SOLUSDT': 'solana',
            'AVAXUSDT': 'avalanche-2',
            'MATICUSDT': 'matic-network',
            'ATOMUSDT': 'cosmos',
            'NEARUSDT': 'near',
            'FTMUSDT': 'fantom',
            'SANDUSDT': 'the-sandbox',
            'MANAUSDT': 'decentraland',
            'AXSUSDT': 'axie-infinity',
            'CHZUSDT': 'chiliz',
            'ENJUSDT': 'enjincoin',
            'GALAUSDT': 'gala',
            'FLOWUSDT': 'flow',
            'ICPUSDT': 'internet-computer',
            'FILUSDT': 'filecoin',
            'XTZUSDT': 'tezos',
            'ALGOUSDT': 'algorand',
            'VETUSDT': 'vechain',
            'HBARUSDT': 'hedera-hashgraph',
            'EGLDUSDT': 'elrond-erd-2',
            'THETAUSDT': 'theta-token',
            'KLAYUSDT': 'klay-token',
            'XEMUSDT': 'nem',
            'WAVESUSDT': 'waves',
            'ZILUSDT': 'zilliqa',
            'ONTUSDT': 'ontology',
            'ZECUSDT': 'zcash',
            'DASHUSDT': 'dash',
            'DCRUSDT': 'decred',
            'BATUSDT': 'basic-attention-token',
            'ZRXUSDT': '0x',
            'IOTAUSDT': 'iota',
            'OMGUSDT': 'omisego',
            'LRCUSDT': 'loopring',
            'KNCUSDT': 'kyber-network-crystal',
            'COMPUSDT': 'compound-governance-token',
            'MKRUSDT': 'maker',
            'SNXUSDT': 'havven',
            'AAVEUSDT': 'aave',
            'UNIUSDT': 'uniswap',
            'SUSHIUSDT': 'sushi',
            'CRVUSDT': 'curve-dao-token',
            'YFIUSDT': 'yearn-finance',
            'UMAUSDT': 'uma',
            'BALUSDT': 'balancer',
            'RENUSDT': 'republic-protocol',
            'STORJUSDT': 'storj',
            'KMDUSDT': 'komodo',
            'SCUSDT': 'siacoin',
            'DGBUSDT': 'digibyte',
            'BTTUSDT': 'bittorrent-2',
            'WINUSDT': 'wink',
            'HOTUSDT': 'holotoken',
            'FETUSDT': 'fetch-ai',
            'CELRUSDT': 'celer-network',
            'TFUELUSDT': 'tfuel',
            'ONEUSDT': 'harmony',
            'FTMUSDT': 'fantom',
            'DOGEUSDT': 'dogecoin',
            'SHIBUSDT': 'shiba-inu'
        }
    
    async def get_market_data(self, symbol: str) -> Dict:
        """
        Mengambil data market untuk symbol tertentu - PRIORITAS BYBIT untuk TOP 100 VOLUME
        """
        # Check cache first
        cache_key = f"{symbol}_{int(datetime.now().timestamp() // self.cache_duration)}"
        if cache_key in self.market_data_cache:
            return self.market_data_cache[cache_key]
        
        try:
            # PRIORITAS UTAMA: Bybit API (semua TOP 100 volume ada di Bybit)
            bybit_data = await self._fetch_bybit_data(symbol)
            
            if not bybit_data or bybit_data.get('lastPrice', 0) == 0:
                print(f"⚠️ No Bybit data for {symbol}")
                return self._get_default_market_data(symbol)
            
            # Estimate market cap from volume (untuk TOP 100 volume coins)
            volume_24h = bybit_data.get('turnover24h', 0)
            price = bybit_data.get('lastPrice', 0)
            
            # Estimate market cap based on volume (rough estimation)
            estimated_market_cap = volume_24h * 50  # Rough multiplier for active trading coins
            
            # Categorize based on volume (yang penting untuk trading)
            if volume_24h > 500_000_000:
                volume_category = "KOIN_BESAR"
                market_cap_category = "BESAR"
            elif volume_24h > 100_000_000:
                volume_category = "MENENGAH" 
                market_cap_category = "MENENGAH"
            else:
                volume_category = "KOIN_KECIL"
                market_cap_category = "KECIL"
            
            # Create market data from Bybit
            combined_data = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'current_price': price,
                
                # Market data - estimated from Bybit volume
                'market_cap': estimated_market_cap,
                'market_cap_rank': 999,  # Unknown rank
                'total_volume_24h': volume_24h,
                'circulating_supply': 0,  # Unknown
                'total_supply': 0,  # Unknown
                'max_supply': 0,  # Unknown
                
                # Price changes - calculate from Bybit if possible
                'price_change_24h': 0,  # Would need historical data
                'price_change_percentage_24h': 0,  # Would need historical data
                'price_change_percentage_7d': 0,
                'price_change_percentage_30d': 0,
                
                # ATH/ATL - unknown
                'ath': 0,
                'ath_change_percentage': 0,
                'atl': 0,
                'atl_change_percentage': 0,
                
                # Bybit data (yang paling penting)
                'bybit_volume_24h': bybit_data.get('volume24h', 0),
                'bybit_turnover_24h': volume_24h,
                'bybit_open_interest': bybit_data.get('openInterest', 0),
                
                # Categories for trading decisions
                'volume_category': volume_category,
                'market_cap_category': market_cap_category,
                
                # Calculated scores based on Bybit data
                'liquidity_score': self._calculate_liquidity_from_bybit(bybit_data),
                'volatility_score': 5.0,  # Default moderate volatility
                'market_dominance': self._calculate_dominance_from_volume(volume_24h)
            }
            
            # Cache the result
            self.market_data_cache[cache_key] = combined_data
            
            return combined_data
            
        except Exception as e:
            print(f"❌ Error getting market data for {symbol}: {e}")
            return self._get_default_market_data(symbol)
        """
        Mengambil data market untuk symbol tertentu
        """
        # Check cache first
        cache_key = f"{symbol}_{int(datetime.now().timestamp() // self.cache_duration)}"
        if cache_key in self.market_data_cache:
            return self.market_data_cache[cache_key]
        
        try:
            # Get coin ID from symbol mapping
            coin_id = self.symbol_mapping.get(symbol)
            if not coin_id:
                # Try to extract base symbol (remove USDT)
                base_symbol = symbol.replace('USDT', '').lower()
                coin_id = base_symbol
            
            # Get data from CoinGecko
            market_data = await self._fetch_coingecko_data(coin_id)
            
            # Get additional data from Bybit (24h volume, etc.)
            bybit_data = await self._fetch_bybit_data(symbol)
            
            # Combine data
            combined_data = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'market_cap': market_data.get('market_cap', 0),
                'market_cap_rank': market_data.get('market_cap_rank', 0),
                'total_volume_24h': market_data.get('total_volume', 0),
                'circulating_supply': market_data.get('circulating_supply', 0),
                'total_supply': market_data.get('total_supply', 0),
                'max_supply': market_data.get('max_supply', 0),
                'price_change_24h': market_data.get('price_change_24h', 0),
                'price_change_percentage_24h': market_data.get('price_change_percentage_24h', 0),
                'price_change_percentage_7d': market_data.get('price_change_percentage_7d', 0),
                'price_change_percentage_30d': market_data.get('price_change_percentage_30d', 0),
                'ath': market_data.get('ath', 0),
                'ath_change_percentage': market_data.get('ath_change_percentage', 0),
                'atl': market_data.get('atl', 0),
                'atl_change_percentage': market_data.get('atl_change_percentage', 0),
                'bybit_volume_24h': bybit_data.get('volume24h', 0),
                'bybit_turnover_24h': bybit_data.get('turnover24h', 0),
                'bybit_price': bybit_data.get('lastPrice', 0),
                'liquidity_score': self._calculate_liquidity_score(market_data, bybit_data),
                'volatility_score': self._calculate_volatility_score(market_data),
                'market_dominance': self._calculate_market_dominance(market_data)
            }
            
            # Cache the result
            self.market_data_cache[cache_key] = combined_data
            
            return combined_data
            
        except Exception as e:
            print(f"❌ Error getting market data for {symbol}: {e}")
            return self._get_default_market_data(symbol)
    
    async def _fetch_coingecko_data(self, coin_id: str) -> Dict:
        """Fetch data from CoinGecko API"""
        try:
            headers = {}
            if self.coingecko_api_key:
                headers['X-CG-Demo-API-Key'] = self.coingecko_api_key
            
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'false',
                'developer_data': 'false',
                'sparkline': 'false'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        market_data = data.get('market_data', {})
                        
                        return {
                            'market_cap': market_data.get('market_cap', {}).get('usd', 0),
                            'market_cap_rank': data.get('market_cap_rank', 0),
                            'total_volume': market_data.get('total_volume', {}).get('usd', 0),
                            'circulating_supply': market_data.get('circulating_supply', 0),
                            'total_supply': market_data.get('total_supply', 0),
                            'max_supply': market_data.get('max_supply', 0),
                            'price_change_24h': market_data.get('price_change_24h', 0),
                            'price_change_percentage_24h': market_data.get('price_change_percentage_24h', 0),
                            'price_change_percentage_7d': market_data.get('price_change_percentage_7d', 0),
                            'price_change_percentage_30d': market_data.get('price_change_percentage_30d', 0),
                            'ath': market_data.get('ath', {}).get('usd', 0),
                            'ath_change_percentage': market_data.get('ath_change_percentage', {}).get('usd', 0),
                            'atl': market_data.get('atl', {}).get('usd', 0),
                            'atl_change_percentage': market_data.get('atl_change_percentage', {}).get('usd', 0)
                        }
                    else:
                        print(f"⚠️ CoinGecko API error: {response.status}")
                        return {}
                        
        except Exception as e:
            print(f"❌ Error fetching CoinGecko data: {e}")
            return {}
    
    async def _fetch_bybit_data(self, symbol: str) -> Dict:
        """Fetch data from Bybit API"""
        try:
            url = "https://api.bybit.com/v5/market/tickers"
            params = {
                'category': 'linear',
                'symbol': symbol
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('retCode') == 0 and data.get('result', {}).get('list'):
                            ticker = data['result']['list'][0]
                            return {
                                'volume24h': float(ticker.get('volume24h', 0)),
                                'turnover24h': float(ticker.get('turnover24h', 0)),
                                'lastPrice': float(ticker.get('lastPrice', 0)),
                                'bid1Price': float(ticker.get('bid1Price', 0)),
                                'ask1Price': float(ticker.get('ask1Price', 0)),
                                'openInterest': float(ticker.get('openInterest', 0))
                            }
                    return {}
                    
        except Exception as e:
            print(f"❌ Error fetching Bybit data: {e}")
            return {}
    
    def _calculate_liquidity_from_bybit(self, bybit_data: Dict) -> float:
        """Calculate liquidity score from Bybit data only"""
        try:
            volume_24h = bybit_data.get('volume24h', 0)
            turnover_24h = bybit_data.get('turnover24h', 0)
            open_interest = bybit_data.get('openInterest', 0)
            
            # High volume = high liquidity
            if turnover_24h > 1_000_000_000:  # > $1B
                return 95.0
            elif turnover_24h > 500_000_000:  # > $500M
                return 85.0
            elif turnover_24h > 100_000_000:  # > $100M
                return 70.0
            elif turnover_24h > 50_000_000:   # > $50M
                return 50.0
            elif turnover_24h > 10_000_000:   # > $10M
                return 30.0
            else:
                return 10.0
                
        except Exception:
            return 10.0
    
    def _calculate_dominance_from_volume(self, volume_24h: float) -> float:
        """Calculate market dominance from volume"""
        try:
            # Higher volume = higher dominance in trading
            if volume_24h > 1_000_000_000:  # > $1B
                return 90.0
            elif volume_24h > 500_000_000:  # > $500M
                return 75.0
            elif volume_24h > 100_000_000:  # > $100M
                return 60.0
            elif volume_24h > 50_000_000:   # > $50M
                return 40.0
            elif volume_24h > 10_000_000:   # > $10M
                return 25.0
            else:
                return 10.0
                
        except Exception:
            return 10.0
        """Calculate liquidity score based on volume and market cap"""
        try:
            market_cap = coingecko_data.get('market_cap', 0)
            volume_24h = coingecko_data.get('total_volume', 0)
            bybit_volume = bybit_data.get('turnover24h', 0)
            
            if market_cap > 0:
                # Volume to market cap ratio
                volume_ratio = (volume_24h + bybit_volume) / market_cap
                
                # Normalize to 0-100 scale
                liquidity_score = min(volume_ratio * 100, 100)
                return round(liquidity_score, 2)
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_volatility_score(self, market_data: Dict) -> float:
        """Calculate volatility score based on price changes"""
        try:
            change_24h = abs(market_data.get('price_change_percentage_24h', 0))
            change_7d = abs(market_data.get('price_change_percentage_7d', 0))
            
            # Weighted average of short and medium term volatility
            volatility_score = (change_24h * 0.7) + (change_7d * 0.3 / 7)
            
            return round(volatility_score, 2)
            
        except Exception:
            return 0.0
    
    def _calculate_market_dominance(self, market_data: Dict) -> float:
        """Calculate market dominance based on market cap rank"""
        try:
            rank = market_data.get('market_cap_rank', 1000)
            
            if rank <= 10:
                return 95.0 - (rank - 1) * 5  # Top 10: 95-50%
            elif rank <= 50:
                return 50.0 - (rank - 10) * 1  # Top 50: 50-10%
            elif rank <= 100:
                return 10.0 - (rank - 50) * 0.1  # Top 100: 10-5%
            else:
                return max(5.0 - (rank - 100) * 0.01, 0)  # Others: <5%
                
        except Exception:
            return 0.0
    
    def _get_default_market_data(self, symbol: str) -> Dict:
        """Return default market data when API fails"""
        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'current_price': 0,
            'market_cap': 0,
            'market_cap_rank': 999,
            'total_volume_24h': 0,
            'circulating_supply': 0,
            'total_supply': 0,
            'max_supply': 0,
            'price_change_24h': 0,
            'price_change_percentage_24h': 0,
            'price_change_percentage_7d': 0,
            'price_change_percentage_30d': 0,
            'ath': 0,
            'ath_change_percentage': 0,
            'atl': 0,
            'atl_change_percentage': 0,
            'bybit_volume_24h': 0,
            'bybit_turnover_24h': 0,
            'bybit_open_interest': 0,
            'volume_category': 'KOIN_KECIL',
            'market_cap_category': 'KECIL',
            'liquidity_score': 0.0,
            'volatility_score': 0.0,
            'market_dominance': 0.0
        }
    
    def categorize_market_cap(self, market_cap: float) -> str:
        """Categorize market cap into size categories"""
        if market_cap >= 10_000_000_000:  # $10B+
            return "Large Cap"
        elif market_cap >= 2_000_000_000:  # $2B-$10B
            return "Mid Cap"
        elif market_cap >= 300_000_000:   # $300M-$2B
            return "Small Cap"
        elif market_cap >= 50_000_000:    # $50M-$300M
            return "Micro Cap"
        else:                              # <$50M
            return "Nano Cap"
    
    def categorize_volume(self, volume_24h: float) -> str:
        """Categorize 24h volume"""
        if volume_24h >= 1_000_000_000:   # $1B+
            return "Very High Volume"
        elif volume_24h >= 100_000_000:   # $100M-$1B
            return "High Volume"
        elif volume_24h >= 10_000_000:    # $10M-$100M
            return "Medium Volume"
        elif volume_24h >= 1_000_000:     # $1M-$10M
            return "Low Volume"
        else:                             # <$1M
            return "Very Low Volume"

# Global instance
market_data_system = MarketDataSystem()

def get_market_data_system():
    """Get global market data system instance"""
    return market_data_system

async def test_market_data_system():
    """Test the market data system"""
    system = MarketDataSystem()
    
    test_symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
    
    print("🧪 Testing Market Data System...")
    
    for symbol in test_symbols:
        print(f"\n📊 Testing {symbol}:")
        data = await system.get_market_data(symbol)
        
        print(f"   Market Cap: ${data['market_cap']:,.0f} ({system.categorize_market_cap(data['market_cap'])})")
        print(f"   24h Volume: ${data['total_volume_24h']:,.0f} ({system.categorize_volume(data['total_volume_24h'])})")
        print(f"   Market Cap Rank: #{data['market_cap_rank']}")
        print(f"   Liquidity Score: {data['liquidity_score']}")
        print(f"   Volatility Score: {data['volatility_score']}")
        print(f"   Market Dominance: {data['market_dominance']}%")

if __name__ == "__main__":
    asyncio.run(test_market_data_system())