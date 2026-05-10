"""
Telegram Bot Service — Indian Market Sniper Alerts
Sends institutional-grade signal messages to Telegram.
"""
import httpx
import os
import logging
from typing import Dict, Any
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")

class TelegramService:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id   = os.getenv("TELEGRAM_CHAT_ID")
        self.base_url  = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        self.logger    = logging.getLogger(__name__)

    async def send_signal(self, signal: Dict[str, Any]):
        if not self.bot_token or not self.chat_id:
            self.logger.warning("Telegram credentials not configured.")
            return

        direction = signal.get('direction', 'LONG')
        emoji_dir  = "📈" if direction == "LONG" else "📉"
        emoji_main = "🎯" if direction == "LONG" else "🔻"
        now_ist    = datetime.now(IST).strftime("%d %b %Y | %I:%M %p IST")

        reasons_text = "\n".join([f"  {r}" for r in signal.get('reasons', [])])

        message = (
            f"{emoji_main} *NIFTY SNIPER — GOLDEN SETUP* {emoji_main}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 *Index:* {signal['symbol']}\n"
            f"🕐 *Time:* {now_ist}\n"
            f"{emoji_dir} *Direction:* `{direction}`\n"
            f"📐 *Setup:* {signal.get('setup_type', 'Fibonacci Sniper')}\n"
            f"🔷 *Fib Zone:* {signal.get('fib_zone', '0.618–0.786')}\n"
            f"📑 *Timeframe:* {signal.get('timeframe', '15m')} | Session: {signal.get('session', '—')}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 *Entry:* `{signal['entry']:,.2f}`\n"
            f"🛑 *Stop Loss:* `{signal['stop_loss']:,.2f}`\n"
            f"✅ *TP1:* `{signal['take_profit_1']:,.2f}`\n"
            f"🚀 *TP2:* `{signal['take_profit_2']:,.2f}`\n"
            f"⚖️ *RR Ratio:* `{signal.get('risk_reward', '1:3')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🧠 *AI Confidence:* `{signal.get('confidence', 0)}%`\n"
            f"📝 *Confluence Evidence:*\n"
            f"{reasons_text}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ _This is a demo paper trade. Not financial advice._\n"
        )

        async with httpx.AsyncClient() as client:
            try:
                await client.post(self.base_url, json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True
                }, timeout=10)
                self.logger.info(f"✅ Telegram alert sent: {signal['symbol']} {direction}")
            except Exception as e:
                self.logger.error(f"❌ Telegram error: {e}")

    async def send_trade_alert(self, text: str):
        """Generic alert (breakeven, close, VIX warning etc.)"""
        if not self.bot_token or not self.chat_id:
            return
        async with httpx.AsyncClient() as client:
            try:
                await client.post(self.base_url, json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": "Markdown"
                }, timeout=10)
            except Exception as e:
                self.logger.error(f"❌ Telegram alert error: {e}")


telegram_service = TelegramService()
