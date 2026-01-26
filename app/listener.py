import asyncio
import logging
from fastapi import FastAPI

async def queue_handler(app: FastAPI):
    """
    Await new queue events
    :param app: Application instance
    :return: coroutine
    """

    logger = logging.getLogger("uvicorn.error")
    logger.info("Queuing events started")
    while True:
        message = await app.state.queue.get()
        logger.warning(f'New queue event: {message}')
        await asyncio.sleep(0.1)