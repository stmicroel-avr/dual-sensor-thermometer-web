import time

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

async def write_events(app: FastAPI, metrics: dict):
    """
    Write metrics to database
    :param app: Application instance
    :param metrics: Metrics dictionary
    :return:
    """
    t = int(time.time())
    for k, v in metrics.items():
        await app.state.db.execute('INSERT INTO metrics(sensor_id, value, created_at) VALUES (?, ?, ?)', (k, v, t))
    await app.state.db.commit()