from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse,JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.websockets import WebSocket, WebSocketDisconnect

from bluetooth import *

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Main page
    :param request: Request
    :return: TemplateResponse
    """
    return templates.TemplateResponse(
        "index.html",
        {"request": request},
    )

@router.get("/scan", response_class=JSONResponse)
async def scan(request: Request):
    """
    Scan available devices
    :param request: Request
    :return: JSONResponse
    """
    data = await ble_scan(request.app)
    return {"data": data}

@router.post("/connect", response_class=JSONResponse)
async def connect(request: Request):
    """
    Connect endpoint to bluetooth device
    :param request: Request
    :return: JSONResponse
    """
    data = await request.json()
    if data is None or 'addr' not in data:
        return {"success": False}

    if request.app.state.ble_task and not request.app.state.ble_task.done():
        return {"success": True, "detail": "already connected"}

    request.app.state.ble_task = asyncio.create_task(ble_connect_worker(request.app, data['addr']))
    request.app.state.ble_device = Device(
        address=data['addr'],
        name=data['name'],
        time=data['time'],
    )

    return {"success": True}

@router.get("/current_bluetooth_connection", response_class=JSONResponse)
async def get_current_ble_connect(request: Request):
    if request.app.state.ble_task and not request.app.state.ble_task.done():
        return {
            "success": True,
            "data": {
                "name": request.app.state.ble_device.name,
                "addr": request.app.state.ble_device.address,
                "time": request.app.state.ble_device.time,
            },
        }
    return {"success": False}

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """
    Websocket endpoint
    :param ws: WebSocket
    :return:
    """
    await ws.accept()
    ws.app.state.logger.info("Websocket client connected")
    ws.app.state.ws_clients.add(ws)
    
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        ws.app.state.logger.info("Websocket client disconnected")
        ws.app.state.ws_clients.remove(ws)
