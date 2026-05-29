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
    # ─── Cleanup expired jobs on startup ───────────────────────
    try:
        from scrapers.web_scraper import mark_stale_jobs
        await mark_stale_jobs()
        print("[Liopleurodon] Expired job cleanup completed on startup.")
    except Exception as e:
        print(f"[Liopleurodon] Startup cleanup error (non-fatal): {e}")

    # ─── API-based scrapers (every 1 hour for faster growth to 2500+) ──
    from services.scheduler import run_periodic_scrapes
    scheduler.add_job(
        run_periodic_scrapes,
        "interval",
        hours=1,
        id="scrape_all",
    )

    # ─── India job scale-up (every 40 minutes → target 3000+) ──
    from scale_india_jobs import run_india_scale
    scheduler.add_job(
        run_india_scale,
        "interval",
        minutes=40,
        id="india_scale",
    )

    # ─── Web scrapers (every 10 minutes) ───────────────────────
    from scrapers.web_scraper import run_web_scrape, mark_stale_jobs
    scheduler.add_job(
        run_web_scrape,
        "interval",
        minutes=10,
        id="web_scrape",
    )

    # ─── Stale + expired job cleanup (every 10 minutes) ────────
    scheduler.add_job(
        mark_stale_jobs,
        "interval",
        minutes=10,
        id="stale_cleanup",
    )

    scheduler.start()
    print("[Liopleurodon] Backend started! API scrapers: 1h, India scale: 40min, Web scrapers: 10min.")
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
