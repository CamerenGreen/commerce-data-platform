from fastapi import APIRouter, Depends, Query

from app.config import get_settings
from app.database import Databases
from app.dependencies import get_databases
from app.repositories.commerce import CommerceRepository
from app.repositories.events import EventRepository
from app.services.analytics import AnalyticsService

router = APIRouter(tags=["analytics"])


def service(databases: Databases) -> AnalyticsService:
    return AnalyticsService(
        CommerceRepository(databases.postgres),
        EventRepository(databases.mongo),
        databases.redis,
        get_settings().cache_ttl_seconds,
    )


@router.get("/analytics/funnel")
async def funnel(
    days: int = Query(default=30, ge=1, le=365),
    databases: Databases = Depends(get_databases),
):
    return await service(databases).funnel(days)


@router.get("/analytics/dashboard")
async def dashboard(
    days: int = Query(default=30, ge=1, le=365),
    databases: Databases = Depends(get_databases),
):
    return await service(databases).dashboard(days)

