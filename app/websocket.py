from fastapi import FastAPI


async def broadcast(app: FastAPI, message: str) -> None:
    """
    Broadcast message to all connected clients
    :param app: App instance
    :param message: Message to broadcast
    :return: None
    """
    for ws in list(app.state.ws_clients):
        try:
            await ws.send_text(message)
        except:
            app.state.ws_clients.remove(ws)