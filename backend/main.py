"""
Liopleurodon — FastAPI Main Application
Global job aggregation platform backend.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import get_settings
from routers import jobs, scrape, companies, users, alerts, ai


scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    # Start the APScheduler
    from services.scheduler import run_periodic_scrapes
    scheduler.add_job(
        run_periodic_scrapes,
        "interval",
        hours=2,
        id="scrape_all",
    )
    scheduler.start()
    print("[Liopleurodon] Backend started! Scraper scheduled every 2 hours.")
    yield
    scheduler.shutdown()
    print("[Liopleurodon] Backend shutting down.")


app = FastAPI(
    title="Liopleurodon",
    description="Global Job Aggregation Platform — scrapes, deduplicates, and serves job listings from 10+ sources.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(jobs.router)
app.include_router(scrape.router)
app.include_router(companies.router)
app.include_router(users.router)
app.include_router(alerts.router)
app.include_router(ai.router)


@app.get("/")
async def root():
    return {
        "name": "Liopleurodon",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
