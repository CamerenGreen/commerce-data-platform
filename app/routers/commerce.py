from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.database import Databases
from app.dependencies import get_databases
from app.repositories.commerce import CommerceRepository
from app.schemas import Customer, CustomerCreate, Order, OrderCreate
from app.services.analytics import AnalyticsService
from app.repositories.events import EventRepository
from app.config import get_settings

router = APIRouter(tags=["commerce"])


@router.get("/products")
async def list_products(databases: Databases = Depends(get_databases)):
    return await CommerceRepository(databases.postgres).list_products()


@router.post("/customers", response_model=Customer, status_code=status.HTTP_201_CREATED)
async def create_customer(
    payload: CustomerCreate,
    databases: Databases = Depends(get_databases),
):
    try:
        return await CommerceRepository(databases.postgres).create_customer(payload)
    except asyncpg.UniqueViolationError as error:
        raise HTTPException(status_code=409, detail="email already exists") from error


@router.post("/orders", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_order(payload: OrderCreate, databases: Databases = Depends(get_databases)):
    try:
        return await CommerceRepository(databases.postgres).create_order(payload)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except asyncpg.SerializationError as error:
        raise HTTPException(status_code=409, detail="concurrent update; retry request") from error


@router.post("/orders/{order_id}/pay", response_model=Order)
async def pay_order(order_id: UUID, databases: Databases = Depends(get_databases)):
    commerce = CommerceRepository(databases.postgres)
    order = await commerce.mark_order_paid(order_id)
    if order is None:
        raise HTTPException(status_code=409, detail="order does not exist or is not pending")

    # The item list is intentionally empty for this command response; the write is atomic.
    order["items"] = []
    analytics = AnalyticsService(
        commerce,
        EventRepository(databases.mongo),
        databases.redis,
        get_settings().cache_ttl_seconds,
    )
    await analytics.invalidate()
    return order
