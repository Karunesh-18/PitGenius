from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import archive_up
from .routers import circuits, drivers, live, races, standings, strategy, teams, tire_degradation

settings = get_settings()

app = FastAPI(title="PitGenius API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(drivers.router)
app.include_router(teams.router)
app.include_router(races.router)
app.include_router(standings.router)
app.include_router(circuits.router)
app.include_router(strategy.router)
app.include_router(tire_degradation.router)
app.include_router(live.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "archive": "up" if archive_up() else "down"}
