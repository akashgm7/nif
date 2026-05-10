from fastapi import APIRouter
from services.external_data import external_data_service

router = APIRouter()

@router.get("/news")
async def get_market_news():
    return await external_data_service.fetch_market_news()

@router.get("/institutional")
async def get_institutional_activity():
    return await external_data_service.fetch_institutional_activity()

@router.get("/volatility")
async def get_volatility_events():
    return await external_data_service.fetch_volatility_events()
