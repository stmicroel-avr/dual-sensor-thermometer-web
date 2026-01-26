from dataclasses import dataclass, field
from asyncio import Queue
import Websocket
from fastapi import WebSocket

@dataclass
class WebSocketRuntime:
    clients: list[Websocket] = field(default_factory=list)
    queues: Queue = field(default_factory=lambda: Queue(maxsize=5000))