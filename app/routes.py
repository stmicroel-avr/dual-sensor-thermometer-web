from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse,JSONResponse
from fastapi.templating import Jinja2Templates
from bluetooth import ble_scan

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request},
    )

@router.get("/scan", response_class=JSONResponse)
async def scan(request: Request):
    data = await ble_scan()
    return {"data": data}
