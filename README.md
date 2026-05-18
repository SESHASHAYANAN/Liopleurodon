# 🦕 Liopleurodon

**Global Job Aggregation Platform** — scrapes, deduplicates, and serves job listings from 10+ sources with AI-powered matching and career insights.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Backend Setup](#backend-setup)
- [Frontend Setup](#frontend-setup)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)

---

## Overview

Liopleurodon is a full-stack job aggregation platform that:

- **Scrapes** job listings from 10+ sources (LinkedIn, Wellfound, Y Combinator, Adzuna, JSearch, TheMuse, Findwork, SerpAPI, Apify, Indian Startups, and more)
- **Deduplicates** listings using intelligent normalisation
- **Serves** a polished dashboard with filters, search, and company pages
- **Provides AI features** — resume review, career recommendations, and keyword-based job matching
- **Auto-refreshes** data via scheduled scrapers (API scrapers every 1 hour, web scrapers every 10 minutes)

---

## Architecture

```
┌────────────────────┐        ┌────────────────────┐
│   Next.js Frontend │◄──────►│  FastAPI Backend    │
│   (Port 3000)      │  REST  │  (Port 8000)       │
└────────────────────┘        └────────┬───────────┘
                                       │
                              ┌────────▼───────────┐
                              │   Supabase (DB)     │
                              │   PostgreSQL        │
                              └────────────────────┘
```

| Layer    | Tech                                     |
| -------- | ---------------------------------------- |
| Frontend | Next.js 16, React 19, Tailwind CSS 4, Framer Motion |
| Backend  | Python, FastAPI, APScheduler, HTTPX      |
| Database | Supabase (PostgreSQL)                    |
| AI       | Groq, Google Gemini, OpenRouter          |

---

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** and **npm**
- A **Supabase** project (free tier works)
- API keys for at least one job-search provider (see [Environment Variables](#environment-variables))

---

## Backend Setup

```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create the .env file (see Environment Variables section below)
cp .env.example .env   # or create manually

# 5. Run the development server
uvicorn main:app --reload --port 8000
```

The API will be available at **http://localhost:8000**.

- Interactive docs: **http://localhost:8000/docs**
- Health check: **http://localhost:8000/health**

---

## Frontend Setup

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Create the .env.local file (see Environment Variables section below)
#    Required variables:
#      NEXT_PUBLIC_API_URL=http://localhost:8000
#      NEXT_PUBLIC_SUPABASE_URL=<your-supabase-url>
#      NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-supabase-anon-key>

# 4. Run the development server
npm run dev
```

The frontend will be available at **http://localhost:3000**.

---

## Environment Variables

### Backend (`backend/.env`)

```env
# ── Supabase ──
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_ANON_KEY=<your-anon-key>
SUPABASE_SERVICE_KEY=<your-service-role-key>

# ── Job Search APIs (add whichever you have) ──
JSEARCH_API_KEY=
SERPAPI_KEY=
ADZUNA_APP_ID=
ADZUNA_API_KEY=
THEIRSTACK_API_KEY=
APIFY_TOKEN=
THEMUSE_API_KEY=
FINDWORK_API_KEY=

# ── AI Providers (at least one recommended) ──
GROQ_API_KEY=
GEMINI_API_KEY=
OPENROUTER_API_KEY=
SAMBANOVA_API_KEY=

# ── Algolia (optional) ──
ALGOLIA_APP_ID=
ALGOLIA_API_KEY=
ALGOLIA_INDEX_NAME=jobhacker_jobs
```

### Frontend (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://<your-project>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-anon-key>
```

> **Note:** Never commit `.env` or `.env.local` files. They are already in `.gitignore`.

---

## Database Setup

The project uses **Supabase** as its PostgreSQL database. To set up the schema:

1. Go to your [Supabase Dashboard](https://supabase.com/dashboard) → SQL Editor
2. Run the migration files in order:
   - `supabase/migrations/001_initial_schema.sql`
   - `supabase/migrations/002_featured_and_staleness.sql`
3. Or run the complete schema in one go:
   - `supabase/migrations/supabase_complete_schema.sql`

---

## API Endpoints

| Method | Route                 | Description                       |
| ------ | --------------------- | --------------------------------- |
| GET    | `/`                   | App info and status               |
| GET    | `/health`             | Health check                      |
| GET    | `/api/jobs`           | List / search / filter jobs       |
| POST   | `/api/scrape`         | Trigger a manual scrape           |
| GET    | `/api/companies`      | List companies                    |
| GET    | `/api/users`          | User management                   |
| GET    | `/api/alerts`         | Job alerts                        |
| POST   | `/api/ai/*`           | AI features (resume, matching)    |

Full interactive documentation is at **http://localhost:8000/docs** once the backend is running.

---

## Project Structure

```
Liopleurodon/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Environment config (pydantic-settings)
│   ├── database.py             # Supabase client setup
│   ├── batch_fetch.py          # Bulk job-fetching script
│   ├── requirements.txt        # Python dependencies
│   ├── routers/
│   │   ├── jobs.py             # /api/jobs endpoints
│   │   ├── scrape.py           # /api/scrape endpoints
│   │   ├── companies.py        # /api/companies endpoints
│   │   ├── users.py            # /api/users endpoints
│   │   ├── alerts.py           # /api/alerts endpoints
│   │   └── ai.py               # /api/ai endpoints
│   ├── scrapers/
│   │   ├── adzuna.py           # Adzuna API scraper
│   │   ├── apify.py            # Apify scraper
│   │   ├── findwork.py         # Findwork API scraper
│   │   ├── india_startups.py   # Indian startup job scraper
│   │   ├── jsearch.py          # JSearch API scraper
│   │   ├── linkedin.py         # LinkedIn scraper
│   │   ├── serpapi.py          # SerpAPI scraper
│   │   ├── theirstack.py       # TheirStack scraper
│   │   ├── themuse.py          # TheMuse API scraper
│   │   ├── web_scraper.py      # General web scraper + stale job cleanup
│   │   ├── wellfound.py        # Wellfound (AngelList) scraper
│   │   └── yc_jobs.py          # Y Combinator jobs scraper
│   └── services/
│       ├── ai_service.py       # AI provider integrations
│       ├── ats_detector.py     # ATS compatibility detector
│       ├── deduplication.py    # Job deduplication logic
│       ├── embedding_service.py# Embedding / vector service
│       ├── normalizer.py       # Data normalisation pipeline
│       ├── scheduler.py        # Periodic scrape scheduler
│       └── vc_tagger.py        # VC-backed company tagger
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.js       # Root layout
│   │   │   ├── page.js         # Landing page
│   │   │   ├── globals.css     # Global styles
│   │   │   ├── dashboard/      # Dashboard page
│   │   │   ├── search/         # Search page
│   │   │   └── company/        # Company page
│   │   ├── components/
│   │   │   ├── Navbar.jsx      # Top navigation bar
│   │   │   ├── JobFeed.jsx     # Main job feed
│   │   │   ├── JobCard.jsx     # Individual job card
│   │   │   ├── JobDetailPanel.jsx # Job detail side panel
│   │   │   ├── FilterPanel.jsx # Filter / search sidebar
│   │   │   ├── ApplyModal.jsx  # Application modal
│   │   │   ├── AuthModal.jsx   # Authentication modal
│   │   │   ├── TrendingSidebar.jsx # Trending jobs sidebar
│   │   │   ├── EmptyState.jsx  # Empty state component
│   │   │   └── SkeletonCard.jsx# Loading skeleton
│   │   ├── context/            # React context providers
│   │   └── lib/                # Utility libraries
│   ├── package.json
│   └── next.config.mjs
├── supabase/
│   └── migrations/             # SQL migration files
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start (TL;DR)

```bash
# Terminal 1 — Backend
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
# Add your .env file with Supabase credentials
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
# Add your .env.local file
npm run dev
```

Open **http://localhost:3000** and start exploring jobs! 🎉

---

## License

This project is for educational and personal use.
