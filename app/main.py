from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import connect, disconnect
from app.repositories.events import EventRepository
from app.routers import analytics, commerce, events

BASE_DIR = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.databases = await connect(get_settings())
    await EventRepository(app.state.databases.mongo).ensure_indexes()
    yield
    await disconnect(app.state.databases)


app = FastAPI(
    title="Commerce Data Platform API",
    version="1.0.0",
    description="Polyglot persistence demo: PostgreSQL + MongoDB + Redis",
    lifespan=lifespan,
)
app.include_router(commerce.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health")
async def health(request: Request):
    databases = request.app.state.databases
    postgres_ok = await databases.postgres.fetchval("SELECT 1") == 1
    mongo_ok = (await databases.mongo_client.admin.command("ping"))["ok"] == 1
    redis_ok = await databases.redis.ping()
    return {
        "status": "healthy" if all((postgres_ok, mongo_ok, redis_ok)) else "degraded",
        "dependencies": {
            "postgres": postgres_ok,
            "mongo": mongo_ok,
            "redis": redis_ok,
        },
    }
