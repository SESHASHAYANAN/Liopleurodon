"""
Liopleurodon -- Batch Live Job Fetcher (Resilient)
Expands the database with live jobs using ALL existing scrapers.
Has built-in network retry logic + starts from where we left off.
"""

import asyncio
import sys
import os
import httpx

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timezone
from services.scheduler import scrape_all_sources
from scrapers.web_scraper import run_web_scrape


async def check_network() -> bool:
    """Quick connectivity check."""
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get("https://httpbin.org/status/200")
            return r.status_code == 200
    except Exception:
        return False


async def wait_for_network(max_wait=120):
    """Wait until network is available, up to max_wait seconds."""
    for i in range(max_wait // 5):
        if await check_network():
            return True
        print(f"    [net] Waiting for network... ({(i+1)*5}s)", flush=True)
        await asyncio.sleep(5)
    return False


# Remaining queries (12 onward -- queries 1-11 already completed)
BATCH_QUERIES = [
    # Continuing from query 12
    ("NLP engineer", "United States"),
    ("computer vision engineer", "United States"),
    ("AI researcher", "India"),
    ("AI researcher", "United States"),
    ("data scientist AI", "India"),
    ("data scientist AI", "United States"),
    ("ML ops engineer", "India"),
    ("ML ops engineer", "United States"),
    ("prompt engineer", "United States"),
    ("prompt engineer", "India"),
    ("AI product manager", "United States"),

    # == Fresher / Entry-level / Intern ==
    ("software engineer fresher", "India"),
    ("software engineer entry level", "United States"),
    ("junior software developer", "India"),
    ("junior software developer", "United States"),
    ("software engineer intern", "India"),
    ("software engineer intern", "United States"),
    ("data science intern", "India"),
    ("data science intern", "United States"),
    ("machine learning intern", "India"),
    ("machine learning intern", "United States"),
    ("frontend developer fresher", "India"),
    ("backend developer fresher", "India"),
    ("junior data analyst", "India"),
    ("junior data analyst", "United States"),
    ("graduate software engineer", "United States"),
    ("entry level AI engineer", "United States"),
    ("entry level AI engineer", "India"),
    ("fresher python developer", "India"),
    ("junior react developer", "United States"),

    # == Startup roles ==
    ("startup software engineer", "India"),
    ("startup software engineer", "United States"),
    ("startup AI engineer", "United States"),
    ("early stage startup engineer", "United States"),
    ("founding engineer", "United States"),
    ("founding engineer", "India"),
    ("series A startup engineer", "United States"),

    # == Stealth startup ==
    ("stealth startup engineer", "United States"),
    ("stealth startup developer", "India"),
    ("stealth mode startup", "United States"),
    ("stealth AI startup", "United States"),

    # == Key cities ==
    ("AI engineer", "Bangalore"),
    ("AI engineer", "San Francisco"),
    ("AI engineer", "New York"),
    ("machine learning engineer", "Hyderabad"),
    ("data scientist", "Pune"),
    ("software engineer", "Chennai"),
    ("AI engineer", "Remote"),
    ("machine learning engineer", "Remote"),

    # == Additional high-demand ==
    ("python developer AI", "India"),
    ("python developer AI", "United States"),
    ("data engineer", "India"),
    ("data engineer", "United States"),
    ("cloud engineer AI", "United States"),
    ("DevOps engineer startup", "India"),
    ("react developer startup", "United States"),
    ("full stack developer AI", "India"),
    ("full stack developer AI", "United States"),
]


async def run_batch():
    total = len(BATCH_QUERIES)
    print(f"\n{'='*60}")
    print(f"  LIOPLEURODON -- Live Batch Fetcher (Resilient)")
    print(f"  {total} remaining queries, all existing scrapers")
    print(f"{'='*60}\n")

    # Check network first
    print("[Pre-check] Testing network connectivity...", flush=True)
    if not await wait_for_network(30):
        print("[FATAL] No network. Exiting.", flush=True)
        return

    print("[OK] Network is up.\n", flush=True)

    grand_found = 0
    grand_inserted = 0
    grand_updated = 0
    consecutive_failures = 0

    for i, (query, location) in enumerate(BATCH_QUERIES, 1):
        print(f"  [{i:2d}/{total}] '{query}' @ '{location}' ...", end=" ", flush=True)

        try:
            result = await asyncio.wait_for(
                scrape_all_sources(query=query, location=location),
                timeout=45,
            )
            found = result.get("jobs_found", 0)
            ins = result.get("jobs_inserted", 0)
            upd = result.get("jobs_updated", 0)
            grand_found += found
            grand_inserted += ins
            grand_updated += upd
            print(f"=> {found} found, {ins} new, {upd} updated", flush=True)

            if found > 0:
                consecutive_failures = 0
            else:
                consecutive_failures += 1

        except asyncio.TimeoutError:
            print(f"=> TIMEOUT", flush=True)
            consecutive_failures += 1
        except Exception as e:
            err = str(e)[:60]
            print(f"=> ERR: {err}", flush=True)
            consecutive_failures += 1

        # If 3+ consecutive failures, check network and wait
        if consecutive_failures >= 3:
            print("\n    [!] Multiple failures -- checking network...", flush=True)
            if not await wait_for_network(60):
                print("    [!] Network still down. Stopping.", flush=True)
                break
            print("    [!] Network recovered. Continuing.\n", flush=True)
            consecutive_failures = 0

        # Respect rate limits -- 2s between queries
        await asyncio.sleep(2)

    print(f"\n{'='*60}")
    print(f"  DONE @ {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}")
    print(f"  Total found:    {grand_found}")
    print(f"  Total inserted: {grand_inserted}")
    print(f"  Total updated:  {grand_updated}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(run_batch())
