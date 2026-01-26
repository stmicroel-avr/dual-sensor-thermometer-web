import json
from fastapi import FastAPI
import uvicorn


async def broadcast(app: FastAPI, message: dict) -> None:
    """
    Broadcast message to all connected clients
    :param app: App instance
    :param message: Message to broadcast
    :return: None
    """
    for ws in list(app.state.ws_clients):
        try:
            await ws.send_text(json.dumps(message))
        except:
            app.state.ws_clients.remove(ws)