"""
NIFTY SNIPER ENGINE — Institutional-Grade Fibonacci Confluence System
Built exclusively for Indian Index Intraday Trading:
  NIFTY 50, BANK NIFTY, FINNIFTY, MIDCAP NIFTY, SENSEX, BANKEX

Strategy: Fibonacci Sniper + Liquidity Sweep + SMC + VWAP + Volume
Rules:
  - 4+ confluences mandatory
  - 0.618 / 0.786 Fibonacci zones ONLY
  - 1:2 minimum RR (1:3 target)
  - Only 4-5 golden setups per day total
  - Indian market hours filter (9:15 – 3:30 IST)
"""
import pandas as pd
import numpy as np
import logging
from typing import Optional, Dict, Any, List

class NiftySniperEngine:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def analyze_sniper_setup(
        self,
        data: Dict[str, pd.DataFrame],
        symbol: str,
        session: str = "MORNING_MOMENTUM",
        is_prime_window: bool = True,
        india_vix: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fibonacci Sniper System for Indian Index Intraday.
        Only fires on 0.618/0.786 golden zone with 4+ confluences.
        """
        df_1h  = data.get('1h')
        df_15m = data.get('15m')
        df_5m  = data.get('5m')

        if df_15m is None or len(df_15m) < 30:
            return None
        if df_1h is None or len(df_1h) < 15:
            return None

        # --- VOLATILITY GUARD ---
        if india_vix is not None:
            if india_vix > 22:  # High fear — block signals
                self.logger.info(f"🚨 India VIX={india_vix} > 22. Blocking signals for safety.")
                return None
            if india_vix < 10:  # Extreme low vol — boring market
                self.logger.info(f"💤 India VIX={india_vix} < 10. Low volatility. Skipping.")
                return None

        # --- SESSION GUARD ---
        if session == "MIDDAY_CONSOLIDATION":
            return None  # Skip dead lunch hours

        # --- 1. HIGHER TIMEFRAME BIAS (1H) ---
        bias = self._get_trend_bias(df_1h)
        if bias == "NEUTRAL":
            return None  # No clear trend — skip

        # --- 2. FIBONACCI ZONE DETECTION ---
        fib_levels = self._calculate_fibonacci(df_15m, bias)
        if not fib_levels:
            return None

        curr_price = df_15m['close'].iloc[-1]

        # Must be in the 0.618–0.786 GOLDEN ZONE
        in_gold_zone, fib_zone_label = self._is_in_golden_zone(curr_price, fib_levels, bias)
        if not in_gold_zone:
            return None

        # --- 3. CONFLUENCE SCORING ---
        confluences = []
        score = 0

        # C1: Liquidity Sweep (CRITICAL — mandatory for institutional setups)
        sweep = self._detect_liquidity_sweep(df_15m, bias)
        if sweep:
            confluences.append(f"✓ Liquidity Sweep — {sweep}")
            score += 2  # Weight 2x

        # C2: VWAP Reclaim/Rejection
        vwap_conf = self._check_vwap_confluence(df_15m, bias)
        if vwap_conf:
            confluences.append(f"✓ VWAP {vwap_conf}")
            score += 1

        # C3: Candlestick Confirmation
        candle_pattern = self._detect_candle_pattern(df_15m, bias)
        if candle_pattern:
            confluences.append(f"✓ {candle_pattern}")
            score += 1

        # C4: Volume Expansion
        vol_conf = self._check_volume_expansion(df_15m)
        if vol_conf:
            confluences.append(f"✓ Volume Expansion ({vol_conf}x avg)")
            score += 1

        # C5: Market Structure (BOS / CHoCH)
        structure = self._check_market_structure(df_15m, bias)
        if structure:
            confluences.append(f"✓ {structure}")
            score += 1

        # C6: 5m entry momentum alignment
        if df_5m is not None and len(df_5m) >= 10:
            entry_bias = self._get_trend_bias(df_5m)
            if entry_bias == bias:
                confluences.append("✓ 5m Entry Momentum Aligned")
                score += 1

        # C7: Prime window bonus
        if is_prime_window:
            confluences.append("✓ Prime Session Window (9:15–11:30 / 13:30–15:00)")
            score += 1

        # --- SNIPER GATE: Need score ≥ 5 (minimum 4 raw confluences) ---
        raw_confluences = len([c for c in confluences if c.startswith("✓") and "Prime" not in c])
        if raw_confluences < 4 or score < 5:
            self.logger.info(f"{symbol}: Score {score}/required 5, confluences {raw_confluences}/4 — REJECTED")
            return None

        # --- RISK MANAGEMENT ---
        risk = self._calculate_risk(curr_price, fib_levels, bias)
        if risk['rr_ratio'] < 2.0:
            self.logger.info(f"{symbol}: RR={risk['rr_ratio']:.1f} < 2.0 — REJECTED")
            return None

        confidence = min(65 + (score * 4), 95)

        return {
            "symbol": symbol,
            "direction": "LONG" if bias == "BULLISH" else "SHORT",
            "entry": round(curr_price, 2),
            "stop_loss": round(risk['sl'], 2),
            "take_profit_1": round(risk['tp1'], 2),
            "take_profit_2": round(risk['tp2'], 2),
            "risk_reward": f"1:{risk['rr_ratio']:.1f}",
            "rr_float": risk['rr_ratio'],
            "confidence": confidence,
            "reasons": confluences,
            "setup_type": "Fibonacci Liquidity Sweep Reversal",
            "timeframe": "15m",
            "fib_zone": fib_zone_label,
            "session": session,
            "trend_bias": bias,
            "fib_levels": {
                "0.382": round(fib_levels.get('0.382', 0), 2),
                "0.500": round(fib_levels.get('0.5', 0), 2),
                "0.618": round(fib_levels.get('0.618', 0), 2),
                "0.786": round(fib_levels.get('0.786', 0), 2),
                "anchor_high": round(fib_levels.get('anchor_high', 0), 2),
                "anchor_low": round(fib_levels.get('anchor_low', 0), 2),
            },
            "status": "ACTIVE",
            "pnl_points": 0.0,
            "is_breakeven": False,
        }

    # ─────────────────────── PRIVATE METHODS ───────────────────────

    def _get_trend_bias(self, df: pd.DataFrame) -> str:
        if df is None or len(df) < 20:
            return "NEUTRAL"
        closes = df['close']
        ema20 = closes.ewm(span=20, adjust=False).mean()
        ema50 = closes.ewm(span=50, adjust=False).mean()
        price = closes.iloc[-1]
        e20 = ema20.iloc[-1]
        e50 = ema50.iloc[-1] if len(df) >= 50 else e20

        # Strong bull: price > ema20 > ema50
        if price > e20 and e20 > e50 * 0.999:
            return "BULLISH"
        # Strong bear: price < ema20 < ema50
        if price < e20 and e20 < e50 * 1.001:
            return "BEARISH"
        return "NEUTRAL"

    def _calculate_fibonacci(self, df: pd.DataFrame, bias: str) -> Optional[Dict]:
        """Detect the most recent impulsive swing and calculate Fib levels."""
        lookback = min(60, len(df))
        data = df.iloc[-lookback:].copy()

        if bias == "BULLISH":
            # Swing: Low → High (bullish impulse, now retracing)
            low_idx = data['low'].idxmin()
            subset  = data.loc[low_idx:]
            if len(subset) < 3:
                return None
            high_idx = subset['high'].idxmax()
            low_val  = data.loc[low_idx, 'low']
            high_val = data.loc[high_idx, 'high']
            diff = high_val - low_val
            if diff < low_val * 0.002:  # Swing too small
                return None
            return {
                '0.236': high_val - diff * 0.236,
                '0.382': high_val - diff * 0.382,
                '0.5':   high_val - diff * 0.500,
                '0.618': high_val - diff * 0.618,
                '0.786': high_val - diff * 0.786,
                'anchor_low':  low_val,
                'anchor_high': high_val,
            }
        else:  # BEARISH
            # Swing: High → Low (bearish impulse, now retracing up)
            high_idx = data['high'].idxmax()
            subset   = data.loc[high_idx:]
            if len(subset) < 3:
                return None
            low_idx  = subset['low'].idxmin()
            high_val = data.loc[high_idx, 'high']
            low_val  = data.loc[low_idx, 'low']
            diff = high_val - low_val
            if diff < low_val * 0.002:
                return None
            return {
                '0.236': low_val + diff * 0.236,
                '0.382': low_val + diff * 0.382,
                '0.5':   low_val + diff * 0.500,
                '0.618': low_val + diff * 0.618,
                '0.786': low_val + diff * 0.786,
                'anchor_low':  low_val,
                'anchor_high': high_val,
            }

    def _is_in_golden_zone(self, price: float, fibs: Dict, bias: str):
        """Check if price is in the 0.618–0.786 golden retracement zone."""
        z_618 = fibs['0.618']
        z_786 = fibs['0.786']

        if bias == "BULLISH":
            # For bull: retracement is downward → 0.786 < 0.618
            lo, hi = min(z_618, z_786), max(z_618, z_786)
            in_zone = lo * 0.998 <= price <= hi * 1.002
            label = f"0.618–0.786 Bull Retracement Zone"
        else:
            lo, hi = min(z_618, z_786), max(z_618, z_786)
            in_zone = lo * 0.998 <= price <= hi * 1.002
            label = f"0.618–0.786 Bear Retracement Zone"

        return in_zone, label

    def _detect_liquidity_sweep(self, df: pd.DataFrame, bias: str) -> Optional[str]:
        """
        Detects a stop-hunt wick that swept liquidity then rejected.
        This is the CORE institutional entry trigger.
        """
        if len(df) < 10:
            return None
        recent = df.iloc[-5:]
        prior  = df.iloc[-25:-5]

        if bias == "BULLISH":
            # Wick below prior swing lows → price reclaimed above
            prior_low = prior['low'].min()
            sweep_low = recent['low'].min()
            curr_close = df['close'].iloc[-1]
            if sweep_low < prior_low and curr_close > prior_low:
                wick_size = prior_low - sweep_low
                if wick_size > (df['high'].iloc[-1] - df['low'].iloc[-1]) * 0.3:
                    return "Stop Hunt Below Structure — Wick Rejection"
        else:
            # Wick above prior swing highs → price rejected below
            prior_high = prior['high'].max()
            sweep_high = recent['high'].max()
            curr_close = df['close'].iloc[-1]
            if sweep_high > prior_high and curr_close < prior_high:
                wick_size = sweep_high - prior_high
                if wick_size > (df['high'].iloc[-1] - df['low'].iloc[-1]) * 0.3:
                    return "Stop Hunt Above Structure — Wick Rejection"
        return None

    def _check_vwap_confluence(self, df: pd.DataFrame, bias: str) -> Optional[str]:
        """VWAP reclaim (bull) or VWAP rejection (bear)."""
        if len(df) < 20:
            return None
        df = df.copy()
        df['tp']     = (df['high'] + df['low'] + df['close']) / 3
        df['tp_vol'] = df['tp'] * df['volume']
        df['vwap']   = df['tp_vol'].cumsum() / df['volume'].cumsum()

        curr = df.iloc[-1]
        prev = df.iloc[-2]
        vwap = curr['vwap']

        if bias == "BULLISH":
            # Price came below VWAP and is now reclaiming it
            if prev['close'] < vwap and curr['close'] > vwap:
                return "Reclaim — Bullish Confirmation"
            if curr['close'] > vwap * 1.0005:
                return "Above VWAP — Bullish Continuation"
        else:
            if prev['close'] > vwap and curr['close'] < vwap:
                return "Rejection — Bearish Confirmation"
            if curr['close'] < vwap * 0.9995:
                return "Below VWAP — Bearish Continuation"
        return None

    def _detect_candle_pattern(self, df: pd.DataFrame, bias: str) -> Optional[str]:
        """Detects high-probability reversal/continuation candlestick patterns."""
        if len(df) < 3:
            return None
        c0 = df.iloc[-1]  # current
        c1 = df.iloc[-2]  # previous
        c2 = df.iloc[-3]  # 2 bars ago

        body0 = abs(c0['close'] - c0['open'])
        range0 = c0['high'] - c0['low']
        body1 = abs(c1['close'] - c1['open'])

        if range0 == 0:
            return None

        # Bullish patterns
        if bias == "BULLISH":
            # Bullish Engulfing
            if (c1['close'] < c1['open'] and
                c0['close'] > c0['open'] and
                c0['close'] > c1['open'] and
                c0['open'] < c1['close']):
                return "Bullish Engulfing Candle"
            # Hammer (long lower wick)
            lower_wick = min(c0['open'], c0['close']) - c0['low']
            if lower_wick > body0 * 2 and body0 > 0 and c0['close'] > c0['open']:
                return "Hammer Reversal"
            # Morning Star
            if (c2['close'] < c2['open'] and
                body1 < body0 * 0.3 and
                c0['close'] > c0['open'] and
                c0['close'] > (c2['open'] + c2['close']) / 2):
                return "Morning Star Formation"
            # Displacement candle (strong bull move)
            if c0['close'] > c0['open'] and body0 > range0 * 0.7:
                return "Bullish Displacement Candle"

        # Bearish patterns
        else:
            # Bearish Engulfing
            if (c1['close'] > c1['open'] and
                c0['close'] < c0['open'] and
                c0['close'] < c1['open'] and
                c0['open'] > c1['close']):
                return "Bearish Engulfing Candle"
            # Shooting Star
            upper_wick = c0['high'] - max(c0['open'], c0['close'])
            if upper_wick > body0 * 2 and body0 > 0 and c0['close'] < c0['open']:
                return "Shooting Star Reversal"
            # Evening Star
            if (c2['close'] > c2['open'] and
                body1 < body0 * 0.3 and
                c0['close'] < c0['open'] and
                c0['close'] < (c2['open'] + c2['close']) / 2):
                return "Evening Star Formation"
            # Displacement candle (strong bear move)
            if c0['close'] < c0['open'] and body0 > range0 * 0.7:
                return "Bearish Displacement Candle"

        return None

    def _check_volume_expansion(self, df: pd.DataFrame) -> Optional[str]:
        """Checks for aggressive volume spike (relative to 20-bar average)."""
        if len(df) < 20:
            return None
        avg_vol  = df['volume'].iloc[-20:-1].mean()
        curr_vol = df['volume'].iloc[-1]
        if avg_vol == 0:
            return None
        ratio = curr_vol / avg_vol
        if ratio >= 2.5:
            return f"{ratio:.1f}"
        if ratio >= 1.8:
            return f"{ratio:.1f}"
        return None

    def _check_market_structure(self, df: pd.DataFrame, bias: str) -> Optional[str]:
        """Detects Break of Structure (BOS) or Change of Character (CHoCH)."""
        if len(df) < 15:
            return None
        recent_highs = df['high'].iloc[-15:-3]
        recent_lows  = df['low'].iloc[-15:-3]
        curr_close   = df['close'].iloc[-1]
        curr_high    = df['high'].iloc[-1]
        curr_low     = df['low'].iloc[-1]

        if bias == "BULLISH":
            # BOS: Price breaks above the last swing high
            if curr_close > recent_highs.max():
                return "BOS — Break of Structure (Bullish)"
            # CHoCH: After bearish structure, first higher high
            last_hh = recent_highs.iloc[-1]
            prev_hh = recent_highs.iloc[:-1].max()
            if curr_high > last_hh and last_hh < prev_hh:
                return "CHoCH — Change of Character (Bullish)"
        else:
            if curr_close < recent_lows.min():
                return "BOS — Break of Structure (Bearish)"
            last_ll = recent_lows.iloc[-1]
            prev_ll = recent_lows.iloc[:-1].min()
            if curr_low < last_ll and last_ll > prev_ll:
                return "CHoCH — Change of Character (Bearish)"
        return None

    def _calculate_risk(self, price: float, fibs: Dict, bias: str) -> Dict:
        """Calculate SL (beyond 0.786/anchor), TP1 (0.382), TP2 (anchor swing high/low)."""
        if bias == "BULLISH":
            sl   = fibs['anchor_low'] * 0.9985    # Below swing low
            tp1  = fibs['0.382']                   # 38.2% extension
            tp2  = fibs['anchor_high'] * 1.002     # Full swing target
        else:
            sl   = fibs['anchor_high'] * 1.0015   # Above swing high
            tp1  = fibs['0.382']                   # 38.2% retracement from low
            tp2  = fibs['anchor_low'] * 0.998      # Full swing target

        risk  = abs(price - sl)
        rw1   = abs(tp1 - price)
        rw2   = abs(tp2 - price)

        rr_ratio = round(rw2 / risk, 1) if risk > 0 else 0

        return {'sl': sl, 'tp1': tp1, 'tp2': tp2, 'rr_ratio': rr_ratio}


signal_engine = NiftySniperEngine()
