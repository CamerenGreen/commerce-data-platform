from datetime import UTC, datetime, timedelta

from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError

from app.schemas import EventCreate


class EventRepository:
    def __init__(self, database):
        self.collection = database.events

    async def ensure_indexes(self) -> None:
        await self.collection.create_index([("event_id", ASCENDING)], unique=True)
        await self.collection.create_index([("occurred_at", ASCENDING)])
        await self.collection.create_index(
            [("customer_id", ASCENDING), ("occurred_at", ASCENDING)]
        )
        await self.collection.create_index(
            [("session_id", ASCENDING), ("occurred_at", ASCENDING)]
        )

    async def insert(self, event: EventCreate) -> bool:
        document = event.model_dump(mode="python")
        document["ingested_at"] = datetime.now(UTC)
        if document["customer_id"] is not None:
            document["customer_id"] = str(document["customer_id"])
        document["event_id"] = str(document["event_id"])
        try:
            await self.collection.insert_one(document)
            return True
        except DuplicateKeyError:
            return False

    async def funnel_counts(self, days: int) -> dict[str, int]:
        start = datetime.now(UTC) - timedelta(days=days)
        pipeline = [
            {"$match": {"occurred_at": {"$gte": start}}},
            {
                "$group": {
                    "_id": "$event_type",
                    "count": {"$sum": 1},
                }
            },
        ]
        counts = {"product_view": 0, "add_to_cart": 0, "checkout_started": 0}
        async for row in await self.collection.aggregate(pipeline):
            if row["_id"] in counts:
                counts[row["_id"]] = row["count"]
        return counts

    async def recent_events(self, limit: int) -> list[dict]:
        cursor = self.collection.find({}, {"_id": 0}).sort("occurred_at", -1).limit(limit)
        return [document async for document in cursor]

