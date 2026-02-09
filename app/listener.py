import datetime as dt
from fastapi import FastAPI
from websocket import broadcast

async def queue_handler(app: FastAPI):
    """
    Await new queue events
    :param app: Application instance
    :return: coroutine
    """
    app.state.logger.info("Queuing events started")
    while True:
        try:
            message = await app.state.queue.get()
            app.state.logger.debug(f'New queue event: {message}')
            metrics = {
                k: float(v) for k, v in (pair.split(":") for pair in message.strip(";").split(";") if pair)
            }

            await broadcast(app, metrics)
            await write_events(app, metrics)
        except Exception:
            app.state.logger.exception("Queue handler crashed")

async def write_events(app: FastAPI, metrics: dict) -> None:
    """
    Write metrics to PostgreSQL (asyncpg)
    """
    # Если хочешь "как было" — время одно на все записи
    ts = dt.datetime.now()  # TIMESTAMP (без TZ)

    async with app.state.db_pool.acquire() as conn:
        for sensor_id, value in metrics.items():
            await conn.execute(
                "INSERT INTO metrics(sensor_id, value, created_at) VALUES($1, $2, $3)",
                sensor_id,
                float(value) if value is not None else None,
                ts,
            )
