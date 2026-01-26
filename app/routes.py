import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse,JSONResponse
from fastapi.templating import Jinja2Templates

from bluetooth import ble_scan, ble_connect_worker

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

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
    data = await ble_scan()
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

    return {"success": True}

# @router.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await ws.accept()
