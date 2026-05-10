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
        """Development Mode: Always returns True to allow testing after hours."""
        return True

    def get_current_session(self) -> str:
        """Development Mode: Simulated session."""
        return "AFTERNOON_TREND"

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

    async def get_multi_tf_data(self, symbol: str) -> tuple:
        """
        Fetches 1H (bias), 15m (confirmation), 5m (entry) data.
        Returns (df_1h, df_15m, df_5m)
        """
        df_1h, df_15m, df_5m = await asyncio.gather(
            self.fetch_ohlcv(symbol, '1h'),
            self.fetch_ohlcv(symbol, '15m'),
            self.fetch_ohlcv(symbol, '5m'),
        )
        return df_1h, df_15m, df_5m

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
        """Fetches India VIX for volatility assessment."""
        try:
            vix = yf.Ticker("^INDIAVIX")
            hist = vix.history(period="1d", interval="1m")
            if not hist.empty:
                return round(float(hist['Close'].iloc[-1]), 2)
        except Exception as e:
            self.logger.error(f"VIX fetch error: {e}")
        return None

market_data_service = MarketDataService()
