from dataclasses import dataclass

import asyncpg
from pymongo import AsyncMongoClient
from redis.asyncio import Redis

from app.config import Settings


@dataclass
class Databases:
    postgres: asyncpg.Pool
    mongo_client: AsyncMongoClient
    mongo: object
    redis: Redis


async def connect(settings: Settings) -> Databases:
    postgres = await asyncpg.create_pool(settings.postgres_dsn, min_size=2, max_size=10)
    mongo_client = AsyncMongoClient(settings.mongo_dsn)
    mongo = mongo_client[settings.mongo_database]
    redis = Redis.from_url(settings.redis_dsn, decode_responses=True)
    await mongo_client.admin.command("ping")
    await redis.ping()
    return Databases(postgres, mongo_client, mongo, redis)


async def disconnect(databases: Databases) -> None:
    await databases.postgres.close()
    await databases.mongo_client.close()
    await databases.redis.aclose()

