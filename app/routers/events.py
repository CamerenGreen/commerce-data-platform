from fastapi import APIRouter, Depends, Response, status

from app.database import Databases
from app.dependencies import get_databases
from app.config import get_settings
from app.repositories.commerce import CommerceRepository
from app.repositories.events import EventRepository
from app.schemas import EventCreate
from app.services.analytics import AnalyticsService

router = APIRouter(tags=["events"])


@router.post("/events", status_code=status.HTTP_202_ACCEPTED)
async def ingest_event(
    payload: EventCreate,
    response: Response,
    databases: Databases = Depends(get_databases),
):
    inserted = await EventRepository(databases.mongo).insert(payload)
    if not inserted:
        response.status_code = status.HTTP_200_OK
    else:
        analytics = AnalyticsService(
            CommerceRepository(databases.postgres),
            EventRepository(databases.mongo),
            databases.redis,
            get_settings().cache_ttl_seconds,
        )
        await analytics.invalidate()
    return {"accepted": inserted, "duplicate": not inserted, "event_id": payload.event_id}


@router.get("/events/recent")
async def recent_events(
    limit: int = 20,
    databases: Databases = Depends(get_databases),
):
    safe_limit = max(1, min(limit, 100))
    return await EventRepository(databases.mongo).recent_events(safe_limit)
