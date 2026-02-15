import asyncio
import logging
import asyncpg
from fastapi import FastAPI
from fastapi.requests import Request
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles

from db import create_db
from routes import router
from listener import queue_handler
from bluetooth import Device

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Start queue listener, init ws clients set, init queue
    :param app: App
    :return: None
    """
    app.state.db_pool = await asyncpg.create_pool(
        user="app",
        password="63gS2&f|3umA",
        database="app",
        host="127.0.0.1",
        port=5432,
        min_size=1
    )
    await create_db(app)
    app.state.ble_task = None
    app.state.ble_client = None
    app.state.ble_device = Device(
        name=None,
        address=None,
        time=None,
        lastupdate=None,
    )
    app.state.ble_task = None
    app.state.ble_client = None
    app.state.ws_clients = set()
    app.state.queue = asyncio.Queue(maxsize=5000)
    app.state.logger = logging.getLogger("uvicorn.error")
    app.state.queue_task = asyncio.create_task(queue_handler(app))
    app.state.logger.info("App state initialized")
    yield
    app.state.logger.info("App stopping")
    await app.state.db_pool.close()
    app.state.queue_task.cancel()
    if app.state.ble_task is not None:
        app.state.ble_task.cancel()

# Main FastAPI App
app = FastAPI(lifespan=lifespan)

# Static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add cache static
@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response

# Routes
app.include_router(router)

