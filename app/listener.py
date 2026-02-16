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
    ts_h = None
    ts_m = None
    ts = dt.datetime.now()

    should_write_minute = app.state.app.queue_last_event_minute is None or (
        ts.minute != app.state.app.queue_last_event_minute
    )
    should_write_hour = app.state.app.queue_last_event_hour is None or (
        ts.hour != app.state.app.queue_last_event_hour
    )

    if should_write_hour:
        app.state.app.queue_last_event_hour = ts.hour
        ts_h = ts.replace(minute=0, second=0, microsecond=0)

    if should_write_minute:
        ts_m = ts.replace(second=0, microsecond=0)
        app.state.app.queue_last_event_minute = ts.minute

    async with app.state.db_pool.acquire() as conn:
        for sensor_id, value in metrics.items():
            clear_value = float(value) if value is not None else None
            await conn.execute(
                "INSERT INTO metrics(sensor_id, value, created_at) VALUES($1, $2, $3)",
                sensor_id,
                clear_value,
                ts
            )

            if should_write_hour:
                await conn.execute(
                    "INSERT INTO hour_metrics(sensor_id, value, created_at) VALUES($1, $2, $3)",
                    sensor_id,
                    clear_value,
                    ts_h
                )

            if should_write_minute:
                await conn.execute(
                    "INSERT INTO minute_metrics(sensor_id, value, created_at) VALUES($1, $2, $3)",
                    sensor_id,
                    clear_value,
                    ts_m
                )
