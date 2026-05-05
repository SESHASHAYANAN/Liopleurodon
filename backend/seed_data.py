"""
Liopleurodon — Seed Data
Pre-loaded featured job listings injected on startup.
Idempotent: uses dedup_hash to avoid duplicates.
"""

from datetime import datetime, timezone
from services.deduplication import generate_dedup_hash


def _make_seed_job(
    title, company, city, country, apply_url, also_url=None,
    salary_min=None, salary_max=None, salary_currency="USD", salary_period="yearly",
    visa=False, relocation=False, remote_type="onsite", experience_level=None,
    job_type="full-time", company_type="startup", vc_backer=None,
    description=None, source_tag="Seed",
):
    """Build a seed job dict with dedup hash."""
    dedup_key = generate_dedup_hash(company, title, city or "", "")
    return {
        "title": title,
        "company_name": company,
        "location_city": city,
        "location_country": country,
        "apply_url": apply_url,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_currency": salary_currency,
        "salary_period": salary_period,
        "visa_sponsorship": visa,
        "relocation_support": relocation,
        "remote_type": remote_type,
        "experience_level": experience_level or _classify_experience(title),
        "job_type": job_type,
        "company_type": company_type,
        "vc_backer": vc_backer,
        "description": description or f"{title} at {company}. Apply: {apply_url}",
        "source_platforms": [source_tag],
        "is_active": True,
        "is_featured": True,
        "is_stealth": False,
        "dedup_hash": dedup_key,
        "posted_date": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def _classify_experience(title: str) -> str:
    """Auto-classify experience from title keywords."""
    t = title.lower()
    if any(k in t for k in ["intern", "fresher", "trainee", "apprentice"]):
        return "intern"
    if any(k in t for k in ["junior", "associate", "jr", "entry"]):
        return "junior"
    if any(k in t for k in ["senior", "sr.", "sr ", "lead"]):
        return "senior"
    if any(k in t for k in ["staff", "principal", "vp", "director", "head of", "engineering director"]):
        return "staff"
    return "mid"


SEED_JOBS = [
    # ─── Atomic Semi — 13 Engineering Roles (SF) ───────────────
    _make_seed_job("Electrical Engineer", "Atomic Semi", "San Francisco", "USA",
                   "https://jobs.ashbyhq.com/AtomicSemi", visa=True,
                   description="Electrical Engineer at Atomic Semi. Design electrical systems for semiconductor equipment. Apply: https://jobs.ashbyhq.com/AtomicSemi | Also: https://atomicsemi.com/careers/"),
    _make_seed_job("Electronic Hardware Design Engineer", "Atomic Semi", "San Francisco", "USA",
                   "https://jobs.ashbyhq.com/AtomicSemi", visa=True,
                   description="Electronic Hardware Design Engineer at Atomic Semi. Design and prototype PCBs and electronic subsystems."),
    _make_seed_job("Mechanical Engineer", "Atomic Semi", "San Francisco", "USA",
                   "https://jobs.ashbyhq.com/AtomicSemi", visa=True,
                   description="Mechanical Engineer at Atomic Semi. Mechanical design for semiconductor manufacturing equipment."),
    _make_seed_job("Mechatronics Engineer", "Atomic Semi", "San Francisco", "USA",
                   "https://jobs.ashbyhq.com/AtomicSemi", visa=True,
                   description="Mechatronics Engineer at Atomic Semi. Integrate mechanical, electrical, and software systems."),
    _make_seed_job("Semiconductor Equipment Engineer", "Atomic Semi", "San Francisco", "USA",
                   "https://jobs.ashbyhq.com/AtomicSemi", visa=True,
                   description="Semiconductor Equipment Engineer at Atomic Semi. Build and maintain semiconductor fabrication tools."),
    _make_seed_job("Robotics Software Engineer", "Atomic Semi", "San Francisco", "USA",
                   "https://jobs.ashbyhq.com/AtomicSemi", visa=True,
                   description="Robotics Software Engineer at Atomic Semi. Develop robotics and automation software in Python/C++."),
    _make_seed_job("Technical Program Manager", "Atomic Semi", "San Francisco", "USA",
                   "https://jobs.ashbyhq.com/AtomicSemi", visa=True,
                   description="Technical Program Manager at Atomic Semi. Lead cross-functional engineering programs."),
    _make_seed_job("Automation Software Engineering Intern", "Atomic Semi", "San Francisco", "USA",
                   "https://jobs.ashbyhq.com/AtomicSemi", visa=True, job_type="internship",
                   description="Automation Software Engineering Intern at Atomic Semi. Build automation tools for semiconductor fab."),
    _make_seed_job("Circuit Design Intern", "Atomic Semi", "San Francisco", "USA",
                   "https://jobs.ashbyhq.com/AtomicSemi", visa=True, job_type="internship",
                   description="Circuit Design Intern at Atomic Semi. Analog and digital circuit design for prototype systems."),
    _make_seed_job("Development Technician", "Atomic Semi", "San Francisco", "USA",
                   "https://jobs.ashbyhq.com/AtomicSemi", visa=True,
                   description="Development Technician at Atomic Semi. Hands-on fabrication and testing of semiconductor equipment."),
    _make_seed_job("PCBA Technician", "Atomic Semi", "San Francisco", "USA",
                   "https://jobs.ashbyhq.com/AtomicSemi", visa=True,
                   description="PCBA Technician at Atomic Semi. PCB assembly, soldering, rework, and inspection."),
    _make_seed_job("Prototype Machinist", "Atomic Semi", "San Francisco", "USA",
                   "https://jobs.ashbyhq.com/AtomicSemi", visa=True,
                   description="Prototype Machinist at Atomic Semi. CNC and manual machining for rapid prototyping."),
    _make_seed_job("Business Operations Generalist", "Atomic Semi", "San Francisco", "USA",
                   "https://jobs.ashbyhq.com/AtomicSemi", visa=True,
                   description="Business Operations Generalist at Atomic Semi. Support procurement, finance, and HR operations."),

    # ─── DataAnnotation — AI Trainer (Remote) ──────────────────
    _make_seed_job("AI Trainer / Software Engineer Analyst", "DataAnnotation", "Remote", "USA",
                   "https://www.dataannotation.tech", remote_type="remote",
                   salary_min=30, salary_max=100, salary_period="hourly",
                   description="AI Trainer at DataAnnotation. Train AI models by providing high-quality data annotations. $30-$100/hr. Also via Indeed: https://www.indeed.com/q-data-annotation-ai-trainer-jobs.html"),

    # ─── Hibachi — Web3 Data Engineer (Remote) ─────────────────
    _make_seed_job("Web3 Data Engineer", "Hibachi", "Remote", "Global",
                   "https://web3.career/data-engineer-hibachi/148310", remote_type="remote",
                   salary_min=140000, salary_max=200000,
                   description="Web3 Data Engineer at Hibachi. Build data pipelines for blockchain and Web3 applications. $140k-$200k USD."),

    # ─── Integra (Sibernetik) — Data Engineer (Indonesia) ──────
    _make_seed_job("Data Engineer", "Sibernetik Integra Data", "Remote", "Indonesia",
                   "https://dealls.com/en/loker/data-engineer-91~sibernetik", remote_type="remote",
                   salary_currency="IDR",
                   description="Data Engineer at Sibernetik Integra Data. Build and maintain data infrastructure for analytics."),

    # ─── OKX — Multiple Roles (Remote) ─────────────────────────
    _make_seed_job("Data Engineer", "OKX", "Remote", "Global",
                   "https://web3.career/web3-companies/okx+remote", remote_type="remote",
                   salary_min=114000, salary_max=200000,
                   description="Data Engineer at OKX. Build real-time data infrastructure for crypto exchange."),
    _make_seed_job("Senior Staff Engineer AI Agent", "OKX", "Remote", "Global",
                   "https://web3.career/web3-companies/okx+remote", remote_type="remote",
                   salary_min=200000, salary_max=300000,
                   description="Senior Staff Engineer AI Agent at OKX. Lead AI agent development for trading systems."),
    _make_seed_job("AI Agent Security Research Engineer", "OKX", "Remote", "Global",
                   "https://web3.career/web3-companies/okx+remote", remote_type="remote",
                   salary_min=150000, salary_max=250000,
                   description="AI Agent Security Research Engineer at OKX. Research and build security for AI-powered trading agents."),
    _make_seed_job("Security Engineer", "OKX", "Remote", "Global",
                   "https://web3.career/web3-companies/okx+remote", remote_type="remote",
                   salary_min=140000, salary_max=220000,
                   description="Security Engineer at OKX. Secure crypto exchange infrastructure and smart contracts."),
    _make_seed_job("Quant Developer", "OKX", "Remote", "Global",
                   "https://web3.career/web3-companies/okx+remote", remote_type="remote",
                   salary_min=180000, salary_max=300000,
                   description="Quant Developer at OKX. Build quantitative trading strategies and execution systems."),
    _make_seed_job("Frontend Engineer", "OKX", "Remote", "Global",
                   "https://web3.career/web3-companies/okx+remote", remote_type="remote",
                   salary_min=120000, salary_max=200000,
                   description="Frontend Engineer at OKX. Build React-based trading interfaces for crypto exchange."),
    _make_seed_job("Engineering Director", "OKX", "Remote", "Global",
                   "https://web3.career/web3-companies/okx+remote", remote_type="remote",
                   salary_min=250000, salary_max=300000,
                   description="Engineering Director at OKX. Lead engineering organization for crypto exchange platform."),
    _make_seed_job("Principal Engineer Middleware", "OKX", "Remote", "Global",
                   "https://web3.career/web3-companies/okx+remote", remote_type="remote",
                   salary_min=200000, salary_max=280000,
                   description="Principal Engineer Middleware at OKX. Design and build middleware platform for trading systems."),
    _make_seed_job("Vulnerability Scanner Engineer", "OKX", "Remote", "Global",
                   "https://web3.career/web3-companies/okx+remote", remote_type="remote",
                   salary_min=130000, salary_max=200000,
                   description="Vulnerability Scanner Engineer at OKX. Build automated vulnerability scanning for crypto exchange."),

    # ─── Phantom — Crypto Wallet Roles (Remote) ────────────────
    _make_seed_job("Staff Engineer", "Phantom", "Remote", "Global",
                   "https://www.linkedin.com/company/phantomwallet/jobs", remote_type="remote",
                   description="Staff Engineer at Phantom. Build the leading multi-chain crypto wallet."),
    _make_seed_job("DevOps Engineer", "Phantom", "Remote", "Global",
                   "https://www.linkedin.com/company/phantomwallet/jobs", remote_type="remote",
                   description="DevOps Engineer at Phantom. Infrastructure and CI/CD for the Phantom crypto wallet."),
    _make_seed_job("Copywriter", "Phantom", "Remote", "Global",
                   "https://www.linkedin.com/company/phantomwallet/jobs", remote_type="remote",
                   description="Copywriter at Phantom. Create compelling content for the leading crypto wallet brand."),

    # ─── Zinnia — Senior Data Engineer (Remote USA) ────────────
    _make_seed_job("Senior Data Engineer", "Zinnia", "Remote", "USA",
                   "https://job-boards.greenhouse.io/zinnia/jobs/4656310006", remote_type="remote",
                   salary_min=122000, salary_max=123000,
                   description="Senior Data Engineer at Zinnia. Build data infrastructure for insurance technology platform. $122k-$123k."),

    # ─── Keyrock — Senior Data Engineer (Brussels) ─────────────
    _make_seed_job("Senior Data Engineer", "Keyrock", "Brussels", "Belgium",
                   "https://jobs.ashbyhq.com/keyrock", remote_type="hybrid",
                   salary_min=36000, salary_max=75000, salary_currency="EUR",
                   visa=True, relocation=True,
                   description="Senior Data Engineer at Keyrock. Build data pipelines for crypto market making. EU Blue Card visa sponsorship available. €36k-€75k."),

    # ─── Astranis (YC W16) — Internships (SF) ─────────────────
    _make_seed_job("Software Engineering Intern", "Astranis", "San Francisco", "USA",
                   "https://www.ziprecruiter.com/co/Astranis-Space-Technologies/Jobs/Internship",
                   job_type="internship", company_type="vc_backed", vc_backer="YC W16",
                   salary_min=29, salary_max=29, salary_period="hourly", relocation=True,
                   description="SWE Intern at Astranis (YC W16). Work on satellite communication software. $29/hr."),
    _make_seed_job("Hardware Engineering Intern", "Astranis", "San Francisco", "USA",
                   "https://www.ziprecruiter.com/co/Astranis-Space-Technologies/Jobs/Internship",
                   job_type="internship", company_type="vc_backed", vc_backer="YC W16",
                   salary_min=29, salary_max=29, salary_period="hourly", relocation=True,
                   description="Hardware Engineering Intern at Astranis (YC W16). Design hardware for satellites. $29/hr."),
    _make_seed_job("DevOps Intern", "Astranis", "San Francisco", "USA",
                   "https://www.ziprecruiter.com/co/Astranis-Space-Technologies/Jobs/Internship",
                   job_type="internship", company_type="vc_backed", vc_backer="YC W16",
                   salary_min=29, salary_max=29, salary_period="hourly", relocation=True,
                   description="DevOps Intern at Astranis (YC W16). Build CI/CD and infrastructure for space tech. $29/hr."),
    _make_seed_job("Propulsion Engineering Intern", "Astranis", "San Francisco", "USA",
                   "https://www.ziprecruiter.com/co/Astranis-Space-Technologies/Jobs/Internship",
                   job_type="internship", company_type="vc_backed", vc_backer="YC W16",
                   salary_min=29, salary_max=29, salary_period="hourly", relocation=True,
                   description="Propulsion Intern at Astranis (YC W16). Electric propulsion for GEO satellites. $29/hr."),
    _make_seed_job("Network Planning Sales Engineer", "Astranis", "San Francisco", "USA",
                   "https://www.ziprecruiter.com/co/Astranis-Space-Technologies/Jobs/Internship",
                   job_type="internship", company_type="vc_backed", vc_backer="YC W16",
                   salary_min=29, salary_max=29, salary_period="hourly", relocation=True,
                   description="Network Planning Sales Engineer Intern at Astranis (YC W16). $29/hr."),

    # ─── Reality Defender (YC W22) — AI Roles (NYC) ────────────
    _make_seed_job("Computer Vision Intern", "Reality Defender", "New York", "USA",
                   "https://www.getclera.com/jobs/companies/reality-defender",
                   job_type="internship", company_type="vc_backed", vc_backer="YC W22",
                   salary_min=28.85, salary_max=46.15, salary_period="hourly",
                   description="Computer Vision Intern at Reality Defender (YC W22). Build deepfake detection. $28.85-$46.15/hr."),

    # ─── FamPay (YC W20) — India Roles ─────────────────────────
    _make_seed_job("TA Intern", "FamPay", "Bengaluru", "India",
                   "https://www.workatastartup.com", job_type="internship",
                   company_type="vc_backed", vc_backer="YC W20", salary_currency="INR",
                   description="Talent Acquisition Intern at FamPay (YC W20). Help build India's first neobank for teenagers."),
    _make_seed_job("Product Engineer", "FamPay", "Bengaluru", "India",
                   "https://www.workatastartup.com",
                   company_type="vc_backed", vc_backer="YC W20", salary_currency="INR",
                   description="Product Engineer at FamPay (YC W20). Build consumer fintech products for Gen Z. Also: https://www.ycombinator.com/jobs"),
]


async def inject_seed_data():
    """Inject seed data into Supabase. Idempotent via dedup_hash."""
    from database import get_supabase_admin

    db = get_supabase_admin()
    inserted = 0
    skipped = 0

    # First, try to add is_featured column if it doesn't exist
    # (gracefully fails if column already exists)
    try:
        # Test if is_featured column exists by querying it
        db.table("jobs").select("is_featured").limit(1).execute()
    except Exception:
        # Column doesn't exist — we'll just skip the is_featured field
        print("[Seed] Note: is_featured column not found in jobs table, adding it via ALTER TABLE is recommended")

    for job in SEED_JOBS:
        try:
            # Check if already exists
            existing = (db.table("jobs")
                       .select("id")
                       .eq("dedup_hash", job["dedup_hash"])
                       .execute())

            if existing.data and len(existing.data) > 0:
                skipped += 1
                continue

            # Try insert with is_featured
            try:
                db.table("jobs").insert(job).execute()
                inserted += 1
            except Exception:
                # If is_featured column doesn't exist, insert without it
                clean = {k: v for k, v in job.items() if k != "is_featured"}
                db.table("jobs").insert(clean).execute()
                inserted += 1

        except Exception as e:
            print(f"[Seed] Error inserting {job.get('title')}: {e}")

    print(f"[Seed] Done: {inserted} inserted, {skipped} already existed")
    return {"inserted": inserted, "skipped": skipped}
