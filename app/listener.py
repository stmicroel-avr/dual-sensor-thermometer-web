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
            app.state.logger.warning(f'New queue event: {message}')
            await broadcast(app, message)
        except Exception:
            app.state.logger.exception("Queue handler crashed")

