"""
External Data Service — Indian Market Intelligence
Provides: India VIX, FII/DII data, Indian market news, RBI calendar.
"""
import httpx
import logging
import os
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")

class ExternalDataService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def fetch_market_news(self):
        """
        Returns Indian market news/events relevant to index trading.
        Uses mock data (production: integrate NewsAPI/Moneycontrol/ET Markets RSS).
        """
        now_ist = datetime.now(IST)
        return [
            {
                "title": "RBI Monetary Policy Committee Meeting — Watch for Rate Decision",
                "sentiment": "Neutral",
                "source": "RBI.org.in",
                "impact": "HIGH",
                "time": "Upcoming"
            },
            {
                "title": "FII Activity: Net Buyers — ₹1,842 Cr in Equities Today",
                "sentiment": "Bullish",
                "source": "NSDL",
                "impact": "MEDIUM",
                "time": now_ist.strftime("%I:%M %p")
            },
            {
                "title": "India VIX Rising — Signals Elevated Uncertainty Before Expiry",
                "sentiment": "Bearish",
                "source": "NSE India",
                "impact": "MEDIUM",
                "time": now_ist.strftime("%I:%M %p")
            },
            {
                "title": "SGX Nifty Positive — Indicates Gap-Up Opening for NIFTY 50",
                "sentiment": "Bullish",
                "source": "SGX",
                "impact": "LOW",
                "time": "Pre-Market"
            },
            {
                "title": "US Markets Closed Flat — No Major Overnight Impact Expected",
                "sentiment": "Neutral",
                "source": "NYSE/NASDAQ",
                "impact": "LOW",
                "time": "Overnight"
            },
        ]

    async def fetch_institutional_activity(self):
        """FII / DII activity mock — production: integrate NSE/BSE data."""
        return [
            {
                "type": "FII",
                "description": "FII Net Buy: ₹1,842 Cr in Cash Segment",
                "impact": "BULLISH",
                "time": "Today"
            },
            {
                "type": "DII",
                "description": "DII Net Buy: ₹2,109 Cr — Strong Domestic Support",
                "impact": "BULLISH",
                "time": "Today"
            },
            {
                "type": "OPTION_OI",
                "description": "Max Pain NIFTY: 22,500 | PCR: 1.12 (Slightly Bullish)",
                "impact": "NEUTRAL",
                "time": "15 min ago"
            },
            {
                "type": "VIX",
                "description": "India VIX: 13.45 — Low Fear, Trend-Friendly Environment",
                "impact": "BULLISH",
                "time": "Live"
            },
        ]

    async def fetch_volatility_events(self):
        """Upcoming high-impact Indian market events."""
        return [
            {"event": "RBI MPC Meeting", "date": "June 4–6, 2026", "impact": "CRITICAL"},
            {"event": "India CPI Data", "date": "June 12, 2026", "impact": "HIGH"},
            {"event": "NSE Monthly Expiry", "date": "May 29, 2026", "impact": "HIGH"},
            {"event": "Union Budget Session", "date": "July 2026", "impact": "CRITICAL"},
            {"event": "India GDP Q4 Data", "date": "May 31, 2026", "impact": "MEDIUM"},
        ]


external_data_service = ExternalDataService()
