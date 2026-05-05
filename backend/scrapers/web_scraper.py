"""
Liopleurodon — Web Scraper
HTML scraper for 9 live job sources. Runs every 10 minutes.
Uses httpx + BeautifulSoup to extract job listings from web pages.
"""

import httpx
import re
import asyncio
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from services.deduplication import generate_dedup_hash


# ─── Experience Classification ──────────────────────────────────
def classify_experience(title: str) -> str:
    """Auto-classify experience level from title keywords."""
    t = title.lower()
    if any(k in t for k in ["intern", "fresher", "trainee", "apprentice", "co-op"]):
        return "intern"
    if any(k in t for k in ["junior", "jr.", "jr ", "associate", "entry level", "entry-level", "graduate"]):
        return "junior"
    if any(k in t for k in ["senior", "sr.", "sr ", "lead", "principal", "architect"]):
        return "senior"
    if any(k in t for k in ["staff", "principal", "vp", "vice president", "director", "head of", "chief", "cto", "ceo"]):
        return "staff"
    return "mid"


# ─── Job Domain Classification ──────────────────────────────────
def classify_domain(title: str) -> str:
    """Auto-classify job domain from title keywords."""
    t = title.lower()
    if any(k in t for k in ["data engineer", "data scientist", "data analyst", "analytics", "bi ", "business intelligence", "etl", "data pipeline"]):
        return "Data Science & Engineering"
    if any(k in t for k in ["ml ", "machine learning", "ai ", "artificial intelligence", "deep learning", "nlp", "computer vision", "genai", "gen ai", "llm"]):
        return "AI-ML-GenAI"
    if any(k in t for k in ["product manager", "product owner", "product lead", "product director"]):
        return "Product Management"
    if any(k in t for k in ["frontend", "front-end", "front end", "react", "vue", "angular", "ui engineer", "ui developer"]):
        return "Frontend Engineering"
    if any(k in t for k in ["backend", "back-end", "back end", "api ", "server", "systems engineer"]):
        return "Backend Engineering"
    if any(k in t for k in ["full stack", "fullstack", "full-stack"]):
        return "Full Stack Engineering"
    if any(k in t for k in ["devops", "sre", "site reliability", "infrastructure", "platform engineer", "cloud engineer"]):
        return "DevOps & Infrastructure"
    if any(k in t for k in ["security", "cybersecurity", "infosec", "penetration", "vulnerability"]):
        return "Security"
    if any(k in t for k in ["mobile", "ios", "android", "flutter", "react native"]):
        return "Mobile Development"
    if any(k in t for k in ["designer", "ux", "ui/ux", "product design"]):
        return "Design"
    if any(k in t for k in ["quant", "quantitative", "trading"]):
        return "Quantitative Finance"
    if any(k in t for k in ["web3", "blockchain", "crypto", "smart contract", "solidity", "defi"]):
        return "Web3 & Crypto"
    return "Software Engineering"


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


async def _fetch_page(client: httpx.AsyncClient, url: str) -> str:
    """Fetch a web page with error handling."""
    try:
        resp = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"[WebScraper] Failed to fetch {url}: {e}")
        return ""


def _first_sentence(text: str) -> str:
    """Extract first sentence from description."""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text).strip()  # strip HTML
    text = re.sub(r'\s+', ' ', text).strip()
    match = re.match(r'^(.+?[.!?])\s', text)
    if match:
        return match.group(1)[:300]
    return text[:300]


def _parse_salary(text: str) -> tuple:
    """Extract salary range from text."""
    if not text:
        return None, None
    # Match patterns like $100k - $200k, $100,000-$200,000, $30/hr, etc.
    patterns = [
        r'\$\s*([\d,]+)\s*[kK]\s*[-–—to]+\s*\$?\s*([\d,]+)\s*[kK]',
        r'\$\s*([\d,]+)\s*[-–—to]+\s*\$?\s*([\d,]+)',
        r'([\d,]+)\s*[kK]\s*[-–—to]+\s*([\d,]+)\s*[kK]',
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            s_min = float(m.group(1).replace(',', ''))
            s_max = float(m.group(2).replace(',', ''))
            if s_min < 1000:  # likely in K
                s_min *= 1000
            if s_max < 1000:
                s_max *= 1000
            return s_min, s_max
    return None, None


def _detect_visa(text: str) -> bool:
    """Check if visa sponsorship is mentioned."""
    if not text:
        return False
    t = text.lower()
    return any(k in t for k in ["visa sponsor", "sponsorship", "h1b", "h-1b", "visa support", "work permit"])


def _detect_relocation(text: str) -> bool:
    """Check if relocation is mentioned."""
    if not text:
        return False
    t = text.lower()
    return any(k in t for k in ["relocation support", "relocation assist", "relocation package", "relocation provided"])


def _detect_remote(text: str) -> str:
    """Detect remote type from text."""
    if not text:
        return "onsite"
    t = text.lower()
    if any(k in t for k in ["remote", "work from home", "wfh", "anywhere"]):
        if any(k in t for k in ["hybrid", "partial remote", "flex"]):
            return "hybrid"
        return "remote"
    if "hybrid" in t:
        return "hybrid"
    return "onsite"


def _make_job(title, company, location, apply_url, description="", salary_text="",
              source="WebScraper", remote_hint="", posted_date=None):
    """Build a normalized job dict from scraped data."""
    city = location.split(",")[0].strip() if location else ""
    country = location.split(",")[-1].strip() if location and "," in location else ""
    full_text = f"{title} {description} {salary_text} {remote_hint}"
    sal_min, sal_max = _parse_salary(salary_text or full_text)
    remote = _detect_remote(remote_hint or full_text)

    # Dedup hash: company + title + city (NO date, so same job doesn't duplicate)
    dedup = generate_dedup_hash(company, title, city, "")

    now = datetime.now(timezone.utc).isoformat()
    return {
        "title": title.strip(),
        "company_name": company.strip(),
        "location_city": city or None,
        "location_country": country or None,
        "apply_url": apply_url,
        "description": _first_sentence(description) or f"{title} at {company}",
        "salary_min": sal_min,
        "salary_max": sal_max,
        "salary_currency": "USD",
        "salary_period": "yearly",
        "experience_level": classify_experience(title),
        "job_type": "internship" if "intern" in title.lower() else "full-time",
        "remote_type": remote,
        "visa_sponsorship": _detect_visa(full_text),
        "relocation_support": _detect_relocation(full_text),
        "company_type": "startup",
        "source_platforms": [source],
        "is_active": True,
        "is_stealth": False,
        "dedup_hash": dedup,
        "posted_date": posted_date or now,
        "created_at": now,
        "updated_at": now,
        "last_seen_at": now,
    }


# ─── Individual Site Scrapers ───────────────────────────────────

async def scrape_workatastartup(client: httpx.AsyncClient) -> list:
    """Scrape workatastartup.com using their Algolia-powered search."""
    jobs = []
    try:
        resp = await client.post(
            "https://45bwzj1sgc-dsn.algolia.net/1/indexes/*/queries",
            headers={
                "x-algolia-api-key": "NDcyMjRjOGVkNmMzZDkyZDVhODQ1MGQyNGYyYTQ5NmRjMzhhM2Y3NjUxOTkzZTcwNDFiNTdhOGFiZjcwMmIxYXRhZ0ZpbHRlcnM9",
                "x-algolia-application-id": "45BWZJ1SGC",
                "Content-Type": "application/json",
            },
            json={
                "requests": [
                    {"indexName": "YCJob_production", "params": "query=&hitsPerPage=30&page=0"},
                ]
            },
            timeout=30,
        )
        data = resp.json()
        hits = data.get("results", [{}])[0].get("hits", [])
        for hit in hits:
            job = _make_job(
                title=hit.get("title", ""),
                company=hit.get("company_name", ""),
                location=hit.get("location", "Remote"),
                apply_url=hit.get("url", "https://www.workatastartup.com"),
                description=hit.get("description", ""),
                remote_hint="remote" if hit.get("remote") else "",
                source="YC-WATS",
            )
            if hit.get("salary_min"):
                job["salary_min"] = hit["salary_min"]
            if hit.get("salary_max"):
                job["salary_max"] = hit["salary_max"]
            job["company_type"] = "vc_backed"
            job["vc_backer"] = f"YC {hit.get('batch', '')}".strip()
            jobs.append(job)
    except Exception as e:
        print(f"[WebScraper] workatastartup error: {e}")
    return jobs


async def scrape_yc_jobs(client: httpx.AsyncClient) -> list:
    """Scrape ycombinator.com/jobs."""
    jobs = []
    try:
        html = await _fetch_page(client, "https://www.ycombinator.com/jobs")
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        # YC jobs page uses specific div structure
        listings = soup.select("a[href*='/companies/']")
        seen = set()
        for link in listings[:40]:
            href = link.get("href", "")
            if href in seen or not href:
                continue
            seen.add(href)
            title_el = link.select_one("span, div")
            title = title_el.get_text(strip=True) if title_el else link.get_text(strip=True)
            if not title or len(title) < 3:
                continue
            full_url = f"https://www.ycombinator.com{href}" if href.startswith("/") else href
            jobs.append(_make_job(
                title=title,
                company="YC Company",
                location="Remote",
                apply_url=full_url,
                source="YC-Jobs",
            ))
    except Exception as e:
        print(f"[WebScraper] ycombinator/jobs error: {e}")
    return jobs


async def scrape_simplify_yc(client: httpx.AsyncClient) -> list:
    """Scrape simplify.jobs YC Internships page."""
    jobs = []
    try:
        html = await _fetch_page(client, "https://simplify.jobs/l/YC-Internships")
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        # Simplify uses card-based layout
        cards = soup.select("[class*='job'], [class*='card'], [class*='listing'], a[href*='/p/']")
        for card in cards[:30]:
            title = ""
            company = ""
            url = ""

            title_el = card.select_one("h2, h3, [class*='title']")
            if title_el:
                title = title_el.get_text(strip=True)
            company_el = card.select_one("[class*='company'], [class*='org']")
            if company_el:
                company = company_el.get_text(strip=True)

            link = card if card.name == "a" else card.select_one("a")
            if link:
                href = link.get("href", "")
                url = f"https://simplify.jobs{href}" if href.startswith("/") else href

            if title and len(title) > 3:
                jobs.append(_make_job(
                    title=title,
                    company=company or "YC Startup",
                    location="Remote, USA",
                    apply_url=url or "https://simplify.jobs/l/YC-Internships",
                    source="Simplify",
                ))
    except Exception as e:
        print(f"[WebScraper] simplify error: {e}")
    return jobs


async def scrape_arc_dev(client: httpx.AsyncClient) -> list:
    """Scrape arc.dev remote data science jobs."""
    jobs = []
    try:
        html = await _fetch_page(client, "https://arc.dev/remote-jobs/data-science")
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("[class*='job'], article, [class*='card'], [class*='listing']")
        for card in cards[:30]:
            title_el = card.select_one("h2, h3, h4, [class*='title']")
            title = title_el.get_text(strip=True) if title_el else ""
            company_el = card.select_one("[class*='company'], [class*='org'], [class*='employer']")
            company = company_el.get_text(strip=True) if company_el else ""
            loc_el = card.select_one("[class*='location'], [class*='loc']")
            location = loc_el.get_text(strip=True) if loc_el else "Remote"
            link = card.select_one("a[href]")
            href = link.get("href", "") if link else ""
            url = f"https://arc.dev{href}" if href.startswith("/") else href
            salary_el = card.select_one("[class*='salary'], [class*='compensation'], [class*='pay']")
            salary = salary_el.get_text(strip=True) if salary_el else ""

            if title and len(title) > 3:
                jobs.append(_make_job(
                    title=title,
                    company=company or "Arc.dev Company",
                    location=location,
                    apply_url=url or "https://arc.dev/remote-jobs/data-science",
                    salary_text=salary,
                    remote_hint="remote",
                    source="ArcDev",
                ))
    except Exception as e:
        print(f"[WebScraper] arc.dev error: {e}")
    return jobs


async def scrape_web3_career(client: httpx.AsyncClient, path: str, source_tag: str) -> list:
    """Generic web3.career scraper."""
    jobs = []
    try:
        url = f"https://web3.career/{path}"
        html = await _fetch_page(client, url)
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select("tr[class*='job'], div[class*='job'], a[href*='/']")
        for row in rows[:30]:
            title_el = row.select_one("h2, h3, h4, td:first-child, [class*='title']")
            title = title_el.get_text(strip=True) if title_el else ""
            company_el = row.select_one("[class*='company'], td:nth-child(2), [class*='org']")
            company = company_el.get_text(strip=True) if company_el else ""
            loc_el = row.select_one("[class*='location'], [class*='loc']")
            location = loc_el.get_text(strip=True) if loc_el else "Remote"
            salary_el = row.select_one("[class*='salary'], [class*='compensation']")
            salary = salary_el.get_text(strip=True) if salary_el else ""
            link = row if row.name == "a" else row.select_one("a[href]")
            href = link.get("href", "") if link else ""
            apply = f"https://web3.career{href}" if href.startswith("/") else (href or url)

            if title and len(title) > 3 and company:
                jobs.append(_make_job(
                    title=title,
                    company=company,
                    location=location,
                    apply_url=apply,
                    salary_text=salary,
                    remote_hint="remote",
                    source=source_tag,
                ))
    except Exception as e:
        print(f"[WebScraper] web3.career/{path} error: {e}")
    return jobs


async def scrape_migratemate(client: httpx.AsyncClient) -> list:
    """Scrape migratemate.co visa sponsorship jobs."""
    jobs = []
    try:
        html = await _fetch_page(client, "https://migratemate.co/visa-sponsorship-jobs-in/california/backend-software-developer")
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("[class*='job'], article, [class*='card'], [class*='listing']")
        for card in cards[:30]:
            title_el = card.select_one("h2, h3, h4, [class*='title']")
            title = title_el.get_text(strip=True) if title_el else ""
            company_el = card.select_one("[class*='company'], [class*='org'], [class*='employer']")
            company = company_el.get_text(strip=True) if company_el else ""
            loc_el = card.select_one("[class*='location'], [class*='loc']")
            location = loc_el.get_text(strip=True) if loc_el else "California, USA"
            link = card.select_one("a[href]")
            href = link.get("href", "") if link else ""
            url = href if href.startswith("http") else f"https://migratemate.co{href}"

            if title and len(title) > 3:
                job = _make_job(
                    title=title,
                    company=company or "Visa Sponsor Company",
                    location=location,
                    apply_url=url or "https://migratemate.co",
                    source="MigrateMate",
                )
                job["visa_sponsorship"] = True  # All jobs on migratemate offer visa sponsorship
                jobs.append(job)
    except Exception as e:
        print(f"[WebScraper] migratemate error: {e}")
    return jobs


async def scrape_arbeitnow(client: httpx.AsyncClient) -> list:
    """Scrape arbeitnow.com engineering jobs (has JSON API)."""
    jobs = []
    try:
        # arbeitnow has a JSON API
        resp = await client.get(
            "https://www.arbeitnow.com/api/job-board-api",
            params={"page": 1},
            headers=HEADERS,
            timeout=30,
        )
        data = resp.json()
        for item in (data.get("data", []) or [])[:30]:
            title = item.get("title", "")
            company = item.get("company_name", "")
            location = item.get("location", "")
            url = item.get("url", "https://www.arbeitnow.com")
            desc = item.get("description", "")
            remote = "remote" if item.get("remote", False) else "onsite"
            tags = item.get("tags", [])

            if title and company:
                job = _make_job(
                    title=title,
                    company=company,
                    location=location,
                    apply_url=url,
                    description=desc,
                    remote_hint=remote,
                    source="Arbeitnow",
                )
                if tags:
                    job["tech_stack"] = tags[:10]
                jobs.append(job)
    except Exception as e:
        print(f"[WebScraper] arbeitnow error: {e}")
    return jobs


# ─── Main Scrape Orchestrator ───────────────────────────────────

async def run_web_scrape() -> dict:
    """Run all web scrapers and return combined results."""
    print(f"[WebScraper] Starting scrape cycle at {datetime.now(timezone.utc).isoformat()}")

    async with httpx.AsyncClient(timeout=30) as client:
        tasks = [
            scrape_workatastartup(client),
            scrape_yc_jobs(client),
            scrape_simplify_yc(client),
            scrape_arc_dev(client),
            scrape_web3_career(client, "data-science+remote-jobs", "Web3-DS"),
            scrape_web3_career(client, "remote-jobs", "Web3-Remote"),
            scrape_web3_career(client, "web3-companies/okx+remote", "Web3-OKX"),
            scrape_migratemate(client),
            scrape_arbeitnow(client),
        ]

        # Small delays between requests to be respectful
        results = []
        for i, task in enumerate(tasks):
            result = await task
            results.append(result)
            if i < len(tasks) - 1:
                await asyncio.sleep(1)  # 1 second between sites

    # Flatten
    all_jobs = []
    for batch in results:
        if isinstance(batch, list):
            all_jobs.extend(batch)

    # Deduplicate and store
    inserted, updated = await _store_scraped_jobs(all_jobs)

    print(f"[WebScraper] Cycle complete: {len(all_jobs)} found, {inserted} inserted, {updated} updated")
    return {"total_found": len(all_jobs), "inserted": inserted, "updated": updated}


async def _store_scraped_jobs(jobs: list) -> tuple:
    """Store scraped jobs in Supabase with deduplication."""
    from database import get_supabase_admin

    db = get_supabase_admin()
    inserted = 0
    updated = 0
    now = datetime.now(timezone.utc).isoformat()

    for job in jobs:
        if not job.get("dedup_hash") or not job.get("title"):
            continue
        try:
            existing = (db.table("jobs")
                       .select("id, dedup_hash")
                       .eq("dedup_hash", job["dedup_hash"])
                       .execute())

            if existing.data and len(existing.data) > 0:
                # Update timestamp only (dedup rule)
                db.table("jobs").update({
                    "updated_at": now,
                    "last_seen_at": now,
                    "is_active": True,
                }).eq("dedup_hash", job["dedup_hash"]).execute()
                updated += 1
            else:
                # Clean fields that may not exist in DB
                clean = {k: v for k, v in job.items() if v is not None and k not in ["last_seen_at"]}
                # Try with last_seen_at, fallback without
                try:
                    clean["last_seen_at"] = now
                    db.table("jobs").insert(clean).execute()
                except Exception:
                    clean.pop("last_seen_at", None)
                    db.table("jobs").insert(clean).execute()
                inserted += 1
        except Exception as e:
            print(f"[WebScraper] DB error for '{job.get('title', '')}': {e}")

    return inserted, updated


async def mark_stale_jobs():
    """Mark jobs as inactive if not seen in 3 scrape cycles (30 minutes)."""
    from database import get_supabase_admin
    from datetime import timedelta

    db = get_supabase_admin()
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
        # Only mark stale jobs from web scraper sources (not API scrapers or seed data)
        web_sources = ["WebScraper", "YC-WATS", "YC-Jobs", "Simplify", "ArcDev",
                       "Web3-DS", "Web3-Remote", "Web3-OKX", "MigrateMate", "Arbeitnow"]

        # Get jobs from web sources that haven't been seen recently
        for source in web_sources:
            try:
                stale = (db.table("jobs")
                        .select("id")
                        .eq("is_active", True)
                        .contains("source_platforms", [source])
                        .lt("updated_at", cutoff)
                        .execute())

                if stale.data:
                    for job in stale.data:
                        db.table("jobs").update({
                            "is_active": False,
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                        }).eq("id", job["id"]).execute()

                    print(f"[WebScraper] Marked {len(stale.data)} stale jobs from {source}")
            except Exception as e:
                print(f"[WebScraper] Staleness check error for {source}: {e}")
    except Exception as e:
        print(f"[WebScraper] mark_stale_jobs error: {e}")
