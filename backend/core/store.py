"""
Central in-memory store — Indian Market Sniper Platform.
Tracks signals, daily limit, active trade state, cooldowns.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, date
import pytz

IST = pytz.timezone("Asia/Kolkata")

# ── Shared In-Memory Stores ──
signal_store: List[Dict[str, Any]] = []
scanner_state: List[Dict[str, Any]] = []
last_signal_times: Dict[str, datetime] = {}
daily_signal_dates: Dict[str, int] = {}   # {date_str: count}

# Paper trade state
active_paper_trade: Optional[Dict[str, Any]] = None
paper_trade_history: List[Dict[str, Any]] = []


# ─────────────── Signal Management ───────────────

def add_signal(signal: Dict[str, Any]) -> Dict[str, Any]:
    symbol = signal["symbol"]
    signal["id"] = len(signal_store) + 1
    signal["created_at"] = datetime.now(IST).isoformat()
    signal["outcome"] = None
    signal["status"]  = "ACTIVE"
    signal["exit_price"] = None
    signal["pnl_points"] = 0.0
    signal["is_breakeven"] = False

    signal_store.append(signal)
    last_signal_times[symbol] = datetime.now(IST)

    # Track daily count
    today = date.today().isoformat()
    daily_signal_dates[today] = daily_signal_dates.get(today, 0) + 1

    # Set as active paper trade
    global active_paper_trade
    active_paper_trade = signal

    # Cap store size
    if len(signal_store) > 200:
        signal_store.pop(0)

    return signal


def get_daily_signal_count() -> int:
    today = date.today().isoformat()
    return daily_signal_dates.get(today, 0)


def has_active_trade() -> bool:
    """Returns True if there's a currently ACTIVE paper trade."""
    global active_paper_trade
    if active_paper_trade is None:
        return False
    return active_paper_trade.get("status") == "ACTIVE"


def close_active_trade(outcome: str, exit_price: float, pnl_points: float):
    """Closes the active paper trade with result."""
    global active_paper_trade
    if active_paper_trade is None:
        return

    active_paper_trade["outcome"]    = outcome  # WIN / LOSS / BREAKEVEN
    active_paper_trade["status"]     = "CLOSED"
    active_paper_trade["exit_price"] = exit_price
    active_paper_trade["pnl_points"] = pnl_points
    active_paper_trade["closed_at"]  = datetime.now(IST).isoformat()

    paper_trade_history.append(active_paper_trade.copy())

    # Update in signal_store
    for s in signal_store:
        if s["id"] == active_paper_trade["id"]:
            s.update(active_paper_trade)
            break

    active_paper_trade = None


def get_active_trade() -> Optional[Dict[str, Any]]:
    return active_paper_trade


def update_signal(signal_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    for s in signal_store:
        if s["id"] == signal_id:
            s.update(data)
            global active_paper_trade
            if active_paper_trade and active_paper_trade.get("id") == signal_id:
                active_paper_trade.update(data)
            return s
    return None


def is_in_cooldown(symbol: str, cooldown_minutes: int = 90) -> bool:
    if symbol not in last_signal_times:
        return False
    elapsed = datetime.now(IST) - last_signal_times[symbol]
    return elapsed < timedelta(minutes=cooldown_minutes)


def get_signals(limit: int = 50) -> List[Dict[str, Any]]:
    return list(reversed(signal_store[-limit:]))


# ─────────────── Scanner State ───────────────

def set_scanner_state(state: List[Dict[str, Any]]):
    global scanner_state
    scanner_state = state


def get_scanner_state() -> List[Dict[str, Any]]:
    return scanner_state
