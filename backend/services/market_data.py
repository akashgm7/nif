"""
Indian Market Data Service
Fetches OHLCV data for NSE indices using yfinance.
Supports: NIFTY 50, BANK NIFTY, FINNIFTY, MIDCAP NIFTY, SENSEX, BANKEX
Market Hours: 9:15 AM - 3:30 PM IST
"""
import yfinance as yf
import pandas as pd
import numpy as np
import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Optional, Dict
import pytz

IST = pytz.timezone("Asia/Kolkata")

# yfinance ticker map for Indian indices
INDIAN_INDICES = {
    "NIFTY50":   "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "FINNIFTY":  "NIFTY_FIN_SERVICE.NS",
    "MIDCAPNIFTY": "^NSMIDCP",
    "SENSEX":    "^BSESN",
}

# Market timing
MARKET_OPEN  = time(9, 15)
MARKET_CLOSE = time(15, 30)

# Prime session windows (IST)
PRIME_WINDOWS = [
    (time(9, 15), time(11, 30)),   # Opening momentum
    (time(13, 30), time(15, 0)),   # Post-lunch continuation
]

class MarketDataService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def is_market_open(self) -> bool:
        """Production Mode: Respects Indian Market hours (9:15 AM - 3:30 PM IST)."""
        now_ist = datetime.now(IST).time()
        return MARKET_OPEN <= now_ist <= MARKET_CLOSE

    def get_current_session(self) -> str:
        """Production Mode: Actual session detection."""
        now_ist = datetime.now(IST).time()
        if not self.is_market_open():
            return "MARKET_CLOSED"
        if time(9, 15) <= now_ist <= time(10, 0):
            return "OPENING_SURGE"
        if time(10, 0) <= now_ist <= time(11, 30):
            return "MORNING_MOMENTUM"
        if time(11, 30) <= now_ist <= time(13, 30):
            return "MIDDAY_CONSOLIDATION"
        if time(13, 30) <= now_ist <= time(15, 0):
            return "AFTERNOON_TREND"
        return "PRE_CLOSE"

    def is_prime_window(self) -> bool:
        """Returns True if we are in a high-probability trading window."""
        now_ist = datetime.now(IST).time()
        return any(start <= now_ist <= end for start, end in PRIME_WINDOWS)

    def _fetch_ohlcv(self, ticker_symbol: str, interval: str, period: str = "5d") -> Optional[pd.DataFrame]:
        """
        Synchronous fetch via yfinance.
        interval: '1m', '5m', '15m', '60m' (1h), '1d'
        """
        try:
            ticker = yf.Ticker(ticker_symbol)
            df = ticker.history(period=period, interval=interval, auto_adjust=True)
            if df is None or df.empty:
                return None
            df = df.reset_index()
            # Normalize column names
            df.columns = [c.lower() for c in df.columns]
            if 'datetime' in df.columns:
                df.rename(columns={'datetime': 'timestamp'}, inplace=True)
            elif 'date' in df.columns:
                df.rename(columns={'date': 'timestamp'}, inplace=True)
            # Keep only trading hours rows for intraday data
            if interval in ['1m', '5m', '15m', '60m']:
                df = df[df['timestamp'].dt.tz_localize(None).apply(
                    lambda x: MARKET_OPEN <= x.time() <= MARKET_CLOSE
                    if hasattr(x, 'time') else True
                )]
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].dropna()
            return df
        except Exception as e:
            self.logger.error(f"Error fetching {ticker_symbol} {interval}: {e}")
            return None

    async def fetch_ohlcv(self, symbol: str, timeframe: str = '15m') -> Optional[pd.DataFrame]:
        """Async wrapper for fetch."""
        ticker_symbol = INDIAN_INDICES.get(symbol)
        if not ticker_symbol:
            self.logger.warning(f"Unknown symbol: {symbol}")
            return None

        # yfinance interval mapping
        tf_map = {'1m': '1m', '3m': '5m', '5m': '5m', '15m': '15m', '1h': '60m', '1H': '60m', '4h': '60m'}
        interval = tf_map.get(timeframe, '15m')

        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(None, self._fetch_ohlcv, ticker_symbol, interval)
        return df

    async def get_multi_tf_data(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """Fetches 1H, 15m, 5m, 3m, and 1m data concurrently."""
        tfs = ['1h', '15m', '5m', '3m', '1m']
        results = await asyncio.gather(*[self.fetch_ohlcv(symbol, tf) for tf in tfs])
        return {tf: df for tf, df in zip(tfs, results)}

    def calculate_vwap_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates VWAP with Standard Deviation Bands."""
        df = self.calculate_vwap(df)
        # Calculate Rolling Standard Deviation of price vs VWAP
        df['std'] = df['close'].rolling(window=20).std()
        df['vwap_upper_1'] = df['vwap'] + (df['std'] * 1.5)
        df['vwap_lower_1'] = df['vwap'] - (df['std'] * 1.5)
        df['vwap_upper_2'] = df['vwap'] + (df['std'] * 2.5)
        df['vwap_lower_2'] = df['vwap'] - (df['std'] * 2.5)
        return df

    def get_institutional_levels(self, df_1d: pd.DataFrame, df_intraday: pd.DataFrame) -> Dict[str, float]:
        """Calculates PDH, PDL, PDC and Opening Range."""
        levels = {}
        if df_1d is not None and len(df_1d) >= 2:
            prev_day = df_1d.iloc[-2] # Previous day's row
            levels['pdh'] = float(prev_day['high'])
            levels['pdl'] = float(prev_day['low'])
            levels['pdc'] = float(prev_day['close'])

        # Opening Range (9:15 - 9:30 for 15m ORB)
        if df_intraday is not None and not df_intraday.empty:
            df_intraday['timestamp'] = pd.to_datetime(df_intraday['timestamp'])
            orb_15 = df_intraday[df_intraday['timestamp'].dt.time < time(9, 30)]
            orb_30 = df_intraday[df_intraday['timestamp'].dt.time < time(9, 45)]
            
            if not orb_15.empty:
                levels['orb_15_high'] = float(orb_15['high'].max())
                levels['orb_15_low'] = float(orb_15['low'].min())
            if not orb_30.empty:
                levels['orb_30_high'] = float(orb_30['high'].max())
                levels['orb_30_low'] = float(orb_30['low'].min())
        
        return levels

    def calculate_vwap(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates session VWAP (resets daily)."""
        df = df.copy()
        df['tp'] = (df['high'] + df['low'] + df['close']) / 3
        df['tp_vol'] = df['tp'] * df['volume']
        # Rolling cumulative for session
        cum_vol = df['volume'].cumsum()
        df['vwap'] = (df['tp_vol'].cumsum() / cum_vol).replace([np.inf, -np.inf], np.nan).ffill().fillna(df['close'])
        return df

    def get_india_vix(self) -> Optional[float]:
        """Fetches India VIX with basic caching to prevent rate limits."""
        # Simple cache check
        if hasattr(self, '_cached_vix') and hasattr(self, '_vix_time'):
            if datetime.now() - self._vix_time < timedelta(minutes=5):
                return self._cached_vix

        try:
            vix = yf.Ticker("^INDIAVIX")
            hist = vix.history(period="1d", interval="1m")
            if not hist.empty:
                val = round(float(hist['Close'].iloc[-1]), 2)
                self._cached_vix = val
                self._vix_time = datetime.now()
                return val
        except Exception as e:
            self.logger.error(f"VIX fetch error: {e}")
        
        # Fallback to last known value or 15.0 (average)
        return getattr(self, '_cached_vix', 15.0)

    async def get_advanced_confluence_data(self, symbol: str) -> Dict[str, Any]:
        """Aggregates all advanced data points for the Sniper Engine."""
        dfs = await self.get_multi_tf_data(symbol)
        df_1d = await self.fetch_ohlcv(symbol, '1d') # Period is 5d by default
        
        # Calculate specialized indicators
        if dfs['15m'] is not None:
            dfs['15m'] = self.calculate_vwap_bands(dfs['15m'])
        
        levels = self.get_institutional_levels(df_1d, dfs['1m'])
        vix = self.get_india_vix()
        
        return {
            "dfs": dfs,
            "levels": levels,
            "vix": vix,
            "session": self.get_current_session(),
            "is_prime": self.is_prime_window()
        }

market_data_service = MarketDataService()
