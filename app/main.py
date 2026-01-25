from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from routes import router

# Main FastAPI App
app = FastAPI()

# Static directory
app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)

# Add cache static
@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"

    return response

# Routes
app.include_router(router)
