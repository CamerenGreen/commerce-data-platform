import json
from decimal import Decimal

from redis.asyncio import Redis

from app.repositories.commerce import CommerceRepository
from app.repositories.events import EventRepository


class AnalyticsService:
    def __init__(
        self,
        commerce: CommerceRepository,
        events: EventRepository,
        redis: Redis,
        cache_ttl: int,
    ):
        self.commerce = commerce
        self.events = events
        self.redis = redis
        self.cache_ttl = cache_ttl

    async def funnel(self, days: int) -> dict:
        cache_key = f"analytics:funnel:{days}"
        cached = await self.redis.get(cache_key)
        if cached:
            return {**json.loads(cached), "cache": "hit"}

        event_counts = await self.events.funnel_counts(days)
        purchases = await self.commerce.purchase_count(days)
        views = event_counts["product_view"]
        carts = event_counts["add_to_cart"]
        result = {
            "window_days": days,
            "product_views": views,
            "add_to_carts": carts,
            "checkouts": event_counts["checkout_started"],
            "purchases": purchases,
            "view_to_cart_rate": round(carts / views * 100, 2) if views else 0.0,
            "cart_to_purchase_rate": round(purchases / carts * 100, 2) if carts else 0.0,
        }
        await self.redis.set(cache_key, json.dumps(result), ex=self.cache_ttl)
        return {**result, "cache": "miss"}

    async def invalidate(self) -> None:
        keys = [key async for key in self.redis.scan_iter(match="analytics:*")]
        if keys:
            await self.redis.delete(*keys)

    async def dashboard(self, days: int) -> dict:
        funnel = await self.funnel(days)
        revenue = await self.commerce.revenue_summary(days)
        top_products = await self.commerce.top_products(5)

        def serializable(row: dict) -> dict:
            return {
                key: float(value) if isinstance(value, Decimal) else value.isoformat()
                if hasattr(value, "isoformat")
                else value
                for key, value in row.items()
            }

        return {
            "funnel": funnel,
            "revenue": [serializable(row) for row in revenue],
            "top_products": [serializable(row) for row in top_products],
        }

