"""FastAPI application entry point for IPL Analytics API."""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.models.schemas import HealthResponse
from api.routers import analytics, matches, players, teams, venues
from monitoring.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("api_starting", version="1.0.0")
    from ingestion.sources.sample_data import save_sample_data
    save_sample_data("data/samples")
    yield
    logger.info("api_shutting_down")


app = FastAPI(
    title="IPL Real-Time Analytics API",
    description=(
        "REST API for IPL cricket analytics, player stats, "
        "team comparisons, and win probability predictions."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time, 4))
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "path": request.url.path},
    )


app.include_router(players.router, prefix="/api/v1")
app.include_router(matches.router, prefix="/api/v1")
app.include_router(teams.router, prefix="/api/v1")
app.include_router(venues.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root() -> dict:
    return {"message": "IPL Real-Time Analytics API", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    return HealthResponse()


@app.get("/api/v1/status")
async def api_status() -> dict:
    return {
        "status": "operational",
        "version": "1.0.0",
        "endpoints": {
            "players": "/api/v1/players",
            "matches": "/api/v1/matches",
            "teams": "/api/v1/teams",
            "venues": "/api/v1/venues",
            "analytics": "/api/v1/analytics",
        },
    }
