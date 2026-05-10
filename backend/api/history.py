from fastapi import APIRouter
from services.market_data import market_data_service

router = APIRouter()

@router.get("/ohlcv")
async def get_ohlcv(symbol: str, timeframe: str = "15m", limit: int = 100):
    df = await market_data_service.fetch_ohlcv(symbol, timeframe)
    if df is None:
        return []
        
    # Take the last `limit` rows
    if len(df) > limit:
        df = df.iloc[-limit:]
        
    return [
        {
            "time": int(row['timestamp'].timestamp()),
            "open": float(row['open']),
            "high": float(row['high']),
            "low": float(row['low']),
            "close": float(row['close'])
        }
        for _, row in df.iterrows()
    ]
