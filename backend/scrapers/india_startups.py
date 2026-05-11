"""
Liopleurodon — Indian Startup Job Scrapers
High-quality junior-level, full-time, onsite Indian startup jobs.
Sources: Adzuna India (multi-city), Internshala, Freshersworld, StartupJobs India, CutShort pages.
"""

import httpx
import asyncio
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from scrapers.web_scraper import _make_job, _fetch_page, HEADERS


# ─── Indian Cities for targeted scraping ────────────────────────
INDIAN_CITIES = [
    "Bangalore", "Mumbai", "Hyderabad", "Pune", "Chennai",
    "Delhi", "Gurgaon", "Noida", "Kolkata", "Ahmedabad",
]

JUNIOR_KEYWORDS = [
    "junior software engineer", "fresher developer", "associate software engineer",
    "graduate engineer trainee", "junior data analyst", "entry level developer",
    "junior full stack developer", "junior backend developer", "junior frontend developer",
    "trainee software engineer", "junior python developer", "associate data scientist",
]


async def scrape_adzuna_india_junior(client: httpx.AsyncClient) -> list:
    """Scrape Adzuna India for junior/fresher full-time onsite startup jobs across cities."""
    jobs = []
    queries = [
        "junior software engineer", "fresher developer startup",
        "associate engineer", "graduate trainee technology",
        "entry level developer", "junior data analyst",
        "junior python developer", "junior full stack developer",
    ]
    for query in queries[:4]:  # Limit to avoid rate limits
        try:
            resp = await client.get(
                "https://api.adzuna.com/v1/api/jobs/in/search/1",
                params={
                    "app_id": "4fbc6de3",
                    "app_key": "09ba5e03b9a6bc6fe505e47c95b527fa",
                    "what": query,
                    "what_exclude": "senior lead principal director",
                    "results_per_page": 30,
                    "sort_by": "date",
                    "content-type": "application/json",
                },
                headers=HEADERS,
                timeout=30,
            )
            data = resp.json()
            for item in (data.get("results", []) or [])[:30]:
                title = item.get("title", "")
                company = item.get("company", {}).get("display_name", "")
                location = item.get("location", {}).get("display_name", "India")
                url = item.get("redirect_url", item.get("adref", ""))
                desc = item.get("description", "")
                salary_min = item.get("salary_min")
                salary_max = item.get("salary_max")
                created = item.get("created", "")

                if title and company:
                    job = _make_job(
                        title=title, company=company, location=location,
                        apply_url=url, description=desc,
                        source="Adzuna-IN-Junior",
                        posted_date=created if created else None,
                    )
                    job["job_type"] = "full-time"
                    job["remote_type"] = "onsite"
                    job["experience_level"] = "junior"
                    job["salary_currency"] = "INR"
                    if salary_min:
                        job["salary_min"] = salary_min
                    if salary_max:
                        job["salary_max"] = salary_max
                    jobs.append(job)
            await asyncio.sleep(1)
        except Exception as e:
            print(f"[IndiaStartups] adzuna junior query '{query}' error: {e}")
    return jobs


async def scrape_internshala_jobs(client: httpx.AsyncClient) -> list:
    """Scrape Internshala fresher jobs — one of India's biggest fresher platforms."""
    jobs = []
    pages = [
        "https://internshala.com/fresher-jobs/full-time/",
        "https://internshala.com/fresher-jobs/software-development/",
        "https://internshala.com/fresher-jobs/data-science/",
    ]
    for page_url in pages:
        try:
            html = await _fetch_page(client, page_url)
            if not html:
                continue
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select(
                "div.individual_internship, div.internship_meta, "
                "div[class*='job'], a[href*='/fresher-job/'], "
                "div.container-fluid .internship_list_container div[class*='internship']"
            )
            if not cards:
                cards = soup.select("a[href*='/job/'], a[href*='/fresher']")

            seen = set()
            for card in cards[:25]:
                link = card if card.name == "a" else card.select_one("a[href]")
                if not link:
                    continue
                href = link.get("href", "")
                if href in seen or not href:
                    continue
                seen.add(href)

                title_el = card.select_one("h3, h4, .job-internship-name, .profile, [class*='title']")
                title = title_el.get_text(strip=True) if title_el else link.get_text(strip=True)
                company_el = card.select_one(".company_name, .company-name, [class*='company']")
                company = company_el.get_text(strip=True) if company_el else ""
                loc_el = card.select_one(".location_link, [class*='location'], .loc")
                location = loc_el.get_text(strip=True) if loc_el else "India"

                full_url = f"https://internshala.com{href}" if href.startswith("/") else href
                if title and len(title) > 3:
                    job = _make_job(
                        title=title, company=company or "Indian Startup",
                        location=location, apply_url=full_url,
                        source="Internshala",
                    )
                    job["experience_level"] = "junior"
                    job["job_type"] = "full-time"
                    job["remote_type"] = "onsite"
                    job["company_type"] = "startup"
                    jobs.append(job)
            await asyncio.sleep(1)
        except Exception as e:
            print(f"[IndiaStartups] internshala error: {e}")
    return jobs


async def scrape_freshersworld(client: httpx.AsyncClient) -> list:
    """Scrape freshersworld.com — India's largest fresher job portal."""
    jobs = []
    urls = [
        "https://www.freshersworld.com/jobs/category/it-software-jobs",
        "https://www.freshersworld.com/jobs/category/startup-jobs",
    ]
    for page_url in urls:
        try:
            html = await _fetch_page(client, page_url)
            if not html:
                continue
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select(
                "div.job-container, div.job-list, "
                "div[class*='job'], a[href*='/job/'], "
                "div.latest-jobs-block .job-details"
            )
            if not cards:
                cards = soup.select("a[href*='freshersworld.com/jobs']")

            seen = set()
            for card in cards[:25]:
                link = card if card.name == "a" else card.select_one("a[href]")
                if not link:
                    continue
                href = link.get("href", "")
                if href in seen or not href:
                    continue
                seen.add(href)

                title_el = card.select_one("h2, h3, h4, .job-title, [class*='title'], span.wrap-title")
                title = title_el.get_text(strip=True) if title_el else link.get_text(strip=True)
                company_el = card.select_one(".company-name, [class*='company'], .org")
                company = company_el.get_text(strip=True) if company_el else ""
                loc_el = card.select_one(".location, [class*='loc'], .city")
                location = loc_el.get_text(strip=True) if loc_el else "India"

                full_url = href if href.startswith("http") else f"https://www.freshersworld.com{href}"
                if title and len(title) > 3:
                    job = _make_job(
                        title=title, company=company or "Indian Company",
                        location=location, apply_url=full_url,
                        source="Freshersworld",
                    )
                    job["experience_level"] = "junior"
                    job["job_type"] = "full-time"
                    job["remote_type"] = "onsite"
                    jobs.append(job)
            await asyncio.sleep(1)
        except Exception as e:
            print(f"[IndiaStartups] freshersworld error: {e}")
    return jobs


async def scrape_cutshort(client: httpx.AsyncClient) -> list:
    """Scrape CutShort — Indian startup hiring platform."""
    jobs = []
    try:
        html = await _fetch_page(client, "https://cutshort.io/jobs")
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(
            "div[class*='job'], a[href*='/job/'], "
            "div.job-card, div.listing, article"
        )
        if not cards:
            cards = soup.select("a[href*='cutshort.io/j']")

        seen = set()
        for card in cards[:30]:
            link = card if card.name == "a" else card.select_one("a[href]")
            if not link:
                continue
            href = link.get("href", "")
            if href in seen or not href:
                continue
            seen.add(href)

            title_el = card.select_one("h2, h3, h4, [class*='title'], [class*='designation']")
            title = title_el.get_text(strip=True) if title_el else link.get_text(strip=True)
            company_el = card.select_one("[class*='company'], [class*='org']")
            company = company_el.get_text(strip=True) if company_el else ""
            loc_el = card.select_one("[class*='location'], [class*='loc']")
            location = loc_el.get_text(strip=True) if loc_el else "India"

            full_url = f"https://cutshort.io{href}" if href.startswith("/") else href
            if title and len(title) > 3:
                job = _make_job(
                    title=title, company=company or "Indian Startup",
                    location=location, apply_url=full_url,
                    source="CutShort",
                )
                job["company_type"] = "startup"
                jobs.append(job)
    except Exception as e:
        print(f"[IndiaStartups] cutshort error: {e}")
    return jobs


async def scrape_wellfound_india(client: httpx.AsyncClient) -> list:
    """Scrape Wellfound (AngelList) India startup jobs."""
    jobs = []
    pages = [
        "https://wellfound.com/jobs?locations=India",
        "https://wellfound.com/jobs?locations=Bangalore",
        "https://wellfound.com/jobs?locations=Mumbai",
    ]
    for page_url in pages:
        try:
            html = await _fetch_page(client, page_url)
            if not html:
                continue
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select(
                "div[class*='job'], a[href*='/jobs/'], "
                "div.styles_result, div[class*='listing']"
            )
            if not cards:
                cards = soup.select("a[href*='/company/']")

            seen = set()
            for card in cards[:20]:
                link = card if card.name == "a" else card.select_one("a[href]")
                if not link:
                    continue
                href = link.get("href", "")
                if href in seen or not href:
                    continue
                seen.add(href)

                title_el = card.select_one("h2, h3, h4, [class*='title']")
                title = title_el.get_text(strip=True) if title_el else link.get_text(strip=True)
                company_el = card.select_one("[class*='company'], [class*='org']")
                company = company_el.get_text(strip=True) if company_el else ""
                loc_el = card.select_one("[class*='location']")
                location = loc_el.get_text(strip=True) if loc_el else "India"

                full_url = f"https://wellfound.com{href}" if href.startswith("/") else href
                if title and len(title) > 3:
                    job = _make_job(
                        title=title, company=company or "India Startup",
                        location=location, apply_url=full_url,
                        source="Wellfound-IN",
                    )
                    job["company_type"] = "startup"
                    jobs.append(job)
            await asyncio.sleep(1)
        except Exception as e:
            print(f"[IndiaStartups] wellfound-india error: {e}")
    return jobs


async def scrape_startup_jobs_india(client: httpx.AsyncClient) -> list:
    """Scrape multiple Indian startup job aggregator pages."""
    jobs = []
    targets = [
        ("https://www.naukri.com/startup-jobs", "Naukri-Startups"),
        ("https://www.shine.com/job-search/startup-jobs", "Shine-Startups"),
        ("https://www.timesjobs.com/candidate/job-search.html?searchType=Home_Search&from=submit&txtKeywords=junior+developer+startup&cboWorkExp1=0&cboWorkExp2=2", "TimesJobs"),
    ]
    for page_url, source_tag in targets:
        try:
            html = await _fetch_page(client, page_url)
            if not html:
                continue
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select(
                "div[class*='job'], article, div[class*='card'], "
                "div[class*='listing'], a[href*='/job/']"
            )
            seen = set()
            for card in cards[:20]:
                link = card if card.name == "a" else card.select_one("a[href]")
                if not link:
                    continue
                href = link.get("href", "")
                if href in seen or not href:
                    continue
                seen.add(href)

                title_el = card.select_one("h2, h3, h4, [class*='title'], [class*='desig']")
                title = title_el.get_text(strip=True) if title_el else link.get_text(strip=True)
                company_el = card.select_one("[class*='company'], [class*='org']")
                company = company_el.get_text(strip=True) if company_el else ""
                loc_el = card.select_one("[class*='location'], [class*='loc']")
                location = loc_el.get_text(strip=True) if loc_el else "India"

                full_url = href if href.startswith("http") else page_url
                if title and len(title) > 3:
                    job = _make_job(
                        title=title, company=company or "Indian Startup",
                        location=location, apply_url=full_url,
                        source=source_tag,
                    )
                    job["company_type"] = "startup"
                    job["remote_type"] = "onsite"
                    jobs.append(job)
            await asyncio.sleep(1)
        except Exception as e:
            print(f"[IndiaStartups] {source_tag} error: {e}")
    return jobs


# ─── Orchestrator: Run all India startup scrapers ───────────────

async def run_india_startup_scrape(client: httpx.AsyncClient) -> list:
    """Run all Indian startup-focused scrapers and return combined jobs."""
    print("[IndiaStartups] Starting Indian startup job scrape...")
    all_jobs = []

    scrapers = [
        ("Adzuna-IN-Junior", scrape_adzuna_india_junior(client)),
        ("Internshala", scrape_internshala_jobs(client)),
        ("Freshersworld", scrape_freshersworld(client)),
        ("CutShort", scrape_cutshort(client)),
        ("Wellfound-IN", scrape_wellfound_india(client)),
        ("StartupJobs-IN", scrape_startup_jobs_india(client)),
    ]

    for name, coro in scrapers:
        try:
            result = await coro
            if result:
                all_jobs.extend(result)
                print(f"  [IndiaStartups] {name}: {len(result)} jobs")
        except Exception as e:
            print(f"  [IndiaStartups] {name} error: {e}")
        await asyncio.sleep(1)

    print(f"[IndiaStartups] Total: {len(all_jobs)} Indian startup jobs found")
    return all_jobs
