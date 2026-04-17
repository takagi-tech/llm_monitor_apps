from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .routers import endpoints

app = FastAPI(title="LLM Monitor")

app.include_router(endpoints.router)

@app.get("/", response_class=HTMLResponse)
async def index():
    with open("app/templates/index.html") as f:
        return f.read()