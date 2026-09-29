import json
from decimal import Decimal

import pytest

from app.services.analytics import AnalyticsService


class FakeCommerce:
    def __init__(self):
        self.purchase_calls = 0

    async def purchase_count(self, days):
        self.purchase_calls += 1
        return 2

    async def revenue_summary(self, days):
        return [{"day": "2026-01-01", "orders": 2, "revenue": Decimal("150.50")}]

    async def top_products(self, limit):
        return [{"name": "Keyboard", "revenue": Decimal("150.50")}]


class FakeEvents:
    async def funnel_counts(self, days):
        return {"product_view": 10, "add_to_cart": 4, "checkout_started": 3}


class FakeRedis:
    def __init__(self):
        self.values = {}

    async def get(self, key):
        return self.values.get(key)

    async def set(self, key, value, ex):
        self.values[key] = value

    async def scan_iter(self, match):
        for key in list(self.values):
            yield key

    async def delete(self, *keys):
        for key in keys:
            self.values.pop(key, None)


@pytest.mark.asyncio
async def test_funnel_calculates_rates_and_caches_result():
    commerce = FakeCommerce()
    cache = FakeRedis()
    service = AnalyticsService(commerce, FakeEvents(), cache, 30)

    first = await service.funnel(30)
    second = await service.funnel(30)

    assert first["view_to_cart_rate"] == 40.0
    assert first["cart_to_purchase_rate"] == 50.0
    assert first["cache"] == "miss"
    assert second["cache"] == "hit"
    assert commerce.purchase_calls == 1


@pytest.mark.asyncio
async def test_invalidation_removes_analytics_keys():
    cache = FakeRedis()
    cache.values["analytics:funnel:30"] = json.dumps({"purchases": 1})
    service = AnalyticsService(FakeCommerce(), FakeEvents(), cache, 30)

    await service.invalidate()

    assert cache.values == {}

