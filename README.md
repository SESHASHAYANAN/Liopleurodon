<div align="center">

# 🦕 Liopleurodon

**A production-grade, self-sustaining global job aggregation engine.**
Scrapes, normalizes, and matches jobs from 10+ sources in real time, using free-tier resources and AI embeddings.

[![Active Users](https://img.shields.io/badge/Active_Users-4%2C000%2B-4f46e5?style=for-the-badge&logo=users&logoColor=white)](#)
[![Forever Free](https://img.shields.io/badge/Forever-Free-10b981?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](#)
[![Live Sources](https://img.shields.io/badge/Live_Sources-10%2B-06b6d4?style=for-the-badge&logo=rss&logoColor=white)](#)
[![AI Powered](https://img.shields.io/badge/AI_Powered-Matching-3b82f6?style=for-the-badge&logo=openai&logoColor=white)](#)

---

[Introduction](#-1-introduction--market-context) · [Solution](#-2-the-liopleurodon-solution) · [Why This Exists](#-3-why-this-repo-exists) · [Architecture](#%EF%B8%8F-4-system-architecture) · [System Design](#%EF%B8%8F-5-detailed-system-design--ingestion-pipelines) · [Frontend & Backend](#%EF%B8%8F-6-frontend--backend-mechanics) · [Setup](#-7-how-to-clone-and-setup) · [App Walkthrough](#-8-detailed-app-walkthrough) · [Repo Structure](#-9-repository-structure-map) · [Features](#-10-key-platform-features) · [Roadmap](#-11-scalability--future-roadmaps) · [Why It Matters](#-12-why-it-matters)

</div>

---
https://docs.google.com/document/d/1K-UdutdoeTzoOLuKIxrLRe-knEw6zi10krWmBTwqs8s/edit?usp=sharing

## 📌 1. Introduction & Market Context

Finding a job has become a monetized gatekeeper's market. The job-hunting landscape is saturated with platforms that commodify access to information. What should be an open channel between talent and opportunity is instead hidden behind paywalls, premium subscriptions, and artificial scarcity networks.

> [!WARNING]
> **The Current Job Platform Crisis**
>
> - **Subscribed Gatekeeping** — Top aggregator services restrict notifications, semantic searches, and early-stage listings behind steep monthly subscription paywalls.
> - **Data Silt & Fragmentation** — Opportunities are scattered across dozens of isolated platforms (YC, LinkedIn, Wellfound, custom startup boards), forcing developers to maintain 10+ logins.
> - **The Cost Barrier** — Job seekers are asked to pay money to look for work, creating an unequal playing field where access is sold to the highest bidder.

As developers and founders, we believe that discovering career opportunities should be **transparent**, **lightning-fast**, and **open to everyone** — without an entry fee.

---

## 💡 2. The Liopleurodon Solution

Liopleurodon is a fully functional, self-updating, high-performance portal designed to aggregate, de-duplicate, classify, and match jobs across 10+ major developer platforms. By combining direct HTML scrapers and public API ingestions, it removes intermediate brokers to provide direct, clean data pipelines.

| | Principle | Details |
|---|---|---|
| ⚡ | **Live Real-Time Ingestion** | Executes live web scraping on scheduled intervals — every 10 minutes for web content, every 1 hour for APIs — capturing listings before they saturate. |
| 🛠️ | **Built Entirely From Scratch** | Scraping modules, data pipelines, normalization models, and keyword ranking matrices are all custom-built without bloated third-party software. |
| 🆓 | **Free API Integrations** | Built on top of free tiers and public APIs (Adzuna, JSearch, TheirStack, Groq, OpenRouter) — no paid license dependencies. |
| 💲 | **Total Infrastructure Cost: $0** | Optimized serverless routines, client computations, and Supabase's free SQL backend mean the entire ecosystem costs exactly zero to operate. |

> [!NOTE]
> **Side Project → 2,000+ Active Users**
>
> Liopleurodon started as a personal script to bypass broker sites. Today, it serves over 2,000 active developers finding jobs globally. We are committed to keeping this platform **forever free** and fully open-source.

---

## 🎯 3. Why This Repo Exists

This codebase is released to dismantle the closed loops of job aggregation. It serves two distinct audiences:

- **For Job Seekers** — A lightning-fast, ad-free portal to discover real opportunities without paying monthly fees. Find real, un-sponsored start-up work, filter by VC-backers, remote parameters, and discover visa sponsorship with zero telemetry tracking.

- **For Developers** — A robust, production-ready blueprint of a modern web scraper infrastructure. It demonstrates how to orchestrate asynchronous tasks in Python, manage PostgreSQL databases with Supabase, implement pgvector semantic match queries, and construct clean React/Next.js interfaces.

By reading and deploying this project, you gain a clear understanding of data pipelines, scraping rate-limits, deduplication heuristics, and AI integrations.

---

## 🏗️ 4. System Architecture

The platform splits responsibilities between a client-heavy Next.js dashboard, an asynchronous FastAPI gateway serving operations, and a Supabase backend handling real-time data storage, vector matching, and user status schemas.

### Architectural Layers

**🌐 Next.js Client Frontend (App Router)**
> React 19 · Tailwind CSS v4 · Framer Motion · Lucide Icons
>
> Handles user interactions, responsive job filters, bookmarks state, visual job board dashboards, and drag-and-drop resume scanner panels.

**⚙️ FastAPI Gateway & Worker Processors**
> Python 3.10+ · APScheduler Daemon · BeautifulSoup4 · HTTPX Async
>
> - **Web Scrapers Pipeline** — Direct Beautiful Soup crawls & API ingestion routines running on 10+ major developer sources.
> - **AI Router & Matching** — Resume parsing via PyPDF2, Llama-3.3 score evaluations, and semantic matching matrices.

**💾 Supabase Cloud Database**
> PostgreSQL · pgvector Indexes · Row Level Security (RLS)
>
> Persists normalized job tables, tracks bookmarks, schedules user email/web notifications, handles authentication tokens, and queries semantic matches using vector distances.

### Technology Stack

| Layer | Core Technologies | Responsibility |
|---|---|---|
| **Frontend** | Next.js 16 (App Router), React 19, Tailwind v4, Framer Motion | Render landing UI, filters, application boards, PDF upload, and client caching |
| **Backend** | FastAPI, Python 3.10+, Uvicorn, APScheduler, HTTPX | Orchestrate scraper scheduler loops, process AI calls, compute score math, expose health routes |
| **Database** | Supabase (PostgreSQL), pgvector, Row Level Security (RLS) | Store aggregated jobs, tracking application state, user bookmarks, alerts configuration, and vector profiles |
| **AI Logic** | Groq API, Google Gemini, OpenRouter (Llama 3.3 / Gemini Flash) | Parse PDF layout structures, categorize matching/missing tech-stack lists, output career advisor summaries |

---

## ⚙️ 5. Detailed System Design & Ingestion Pipelines

The platform manages dynamic data flow through a multi-stage ingestion pipeline. Raw job postings must be extracted, cleansed, normalized, deduplicated, and stored securely within 30-day window loops.

### 🔑 The Hashing Deduplication Protocol

To prevent identical postings from flooding the feed across different directories (e.g., ArcDev and LinkedIn reporting the same role), the backend generates a unique SHA-256 identifier based on structural properties:

```
dedup_hash = SHA256( Lowercase( CompanyName + Title + LocationCity ) )
```

Because the hash ignores date variables, when a scraper discovers the same job again, it runs a SQL `ON CONFLICT` operation in Supabase to simply update the `last_seen_at` timestamp and refresh details, rather than creating duplicates.

### ⛓️ Scraper Pipeline Sequence

1. **Raw Source Scrape** → Fetch HTML pages or call REST APIs from 10+ sources
2. **HTML Parsing / API Extraction** → Extract structured job data using BeautifulSoup or JSON parsing
3. **Classification Engine** → Classify by domain, experience level, and tech stack
4. **SHA-256 Hashing Normalization** → Generate unique dedup hashes for each listing
5. **Deduplication Check** → Compare hashes against existing records (`ON CONFLICT`)
6. **Supabase Storage** → Upsert rows into the PostgreSQL database
7. **Stale Cleanup Loop** → Mark `is_active = False` if `last_seen_at > 30 Days`

### 💾 Database Schema

The relational data model centers around four core tables:

| Table | Purpose | Key Relationships |
|---|---|---|
| `jobs` | Stores all job attributes (title, company, salary, source, etc.) | Primary table — referenced by all others |
| `saved_jobs` | User bookmarks linked to specific listings | Foreign key → `jobs.id` |
| `user_applications` | Tracks application state (applied, interview, offered) | Foreign key → `jobs.id` |
| `job_alerts` | Aggregates alert configurations for automated notifications | Joins on `job_id` |

---

## ⚙️ 6. Frontend & Backend Mechanics

### ⚡ How the Frontend Works

The frontend utilizes **Next.js 16** App Router with hybrid features:

- **Auth Context Syncing** — A top-level React Auth Context communicates directly with Supabase Client instance to observe JWT tokens and route dashboard access.
- **Dynamic Layout Panels** — Uses Tailwind v4 utilities combined with `framer-motion` cards to slide open comprehensive job detail panels without breaking feed context.
- **Interactive State Management** — Client handles responsive toggling of filtering states (overlay for mobile devices, sidebar for desktop layout resolutions).

### ⚙️ How the Backend Works

The **FastAPI Backend** handles computational bottlenecks and API mappings:

- **Lifespan Task Schedulers** — Uses FastAPI's async lifespan context combined with `APScheduler` to start concurrent task execution (API scrapers every hour, site scrapers every 10 mins).
- **Fast Validation Routers** — Uses `Pydantic` to enforce typing parameters across endpoints (e.g., `/api/ai/keyword-match`).
- **Modular Routers Design** — Split into distinct files (AI routers, jobs router, companies router, alerts manager) in the `routers/` directory to keep the core clean.

### ↔️ API Interaction Example

The resume matching flow demonstrates how the frontend and backend interact:

1. **User** uploads a PDF via the Next.js client
2. **Client** sends the file to `FastAPI: /api/ai/match-resume-pdf`
3. **Backend** extracts text using PyPDF2
4. **AI Processing** via Groq API evaluates and scores the match
5. **JSON Results** are returned to the client for display

---

## 🚀 7. How to Clone and Setup

Follow these instructions to deploy both the FastAPI backend and Next.js frontend in a local development environment.

### 📋 Prerequisites

- **Node.js** — v18.0.0 or higher
- **Python** — v3.10.0 or higher
- **Supabase** — A free account with an active PostgreSQL project
- **API Keys** *(optional but recommended)* — Groq, OpenRouter, JSearch, Adzuna

### 📦 Step 1: Clone Repository & Install Backend

```bash
git clone https://github.com/SESHASHAYANAN/Liopleurodon.git
cd Liopleurodon

# Navigate to backend and create virtual environment
cd backend
python -m venv venv

# Activate Virtual Environment (Windows)
venv\Scripts\activate

# Activate Virtual Environment (macOS / Linux)
source venv/bin/activate

# Install all python requirements
pip install -r requirements.txt
```

### 📦 Step 2: Install Frontend Dependencies

```bash
# Navigate to frontend from root directory
cd ../frontend
npm install
```

### 🔑 Step 3: Environment Setup

Create the following environment files in the respective folders:

**Backend** → `backend/.env`

```env
SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_ANON_KEY=your-anon-public-key
SUPABASE_SERVICE_KEY=your-service-role-admin-key

# Scraper Provider Keys
JSEARCH_API_KEY=your-jsearch-key
ADZUNA_APP_ID=your-adzuna-id
ADZUNA_API_KEY=your-adzuna-key

# AI Orchestration Keys
GROQ_API_KEY=your-groq-api-key
OPENROUTER_API_KEY=your-openrouter-key
```

**Frontend** → `frontend/.env.local`

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-supabase-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-public-key
```

### 🏃 Step 4: Run Development Servers

| System | Directory | Command | Port |
|---|---|---|---|
| Backend REST Server | `/backend` | `uvicorn main:app --reload --port 8000` | `http://localhost:8000` |
| Next.js Frontend UI | `/frontend` | `npm run dev` | `http://localhost:3000` |

### 🔧 Step 5: Development Workflow & Ingestions

To test the scrapers manually without waiting for scheduler loop updates:

```bash
# Run All Scrapers
python refresh_jobs.py

# Run India-Specific Ingestions
python ingest_india_fast.py

# Perform Database Stale Cleanup
python verify_jobs.py
```

> [!IMPORTANT]
> **Production Deployment**
>
> For production, host the Next.js app on **Vercel** and the FastAPI backend on **Render**, **Fly.io**, or **AWS**. Ensure you configure Supabase PostgreSQL migrations using the scripts in `supabase/migrations/`. Use cron scheduling services if deploying FastAPI to serverless environments where stateful background scheduling is restricted.

---

## 📱 8. Detailed App Walkthrough

### 1. Homepage Feed

<h3>The command center of the job search experience. Displays aggregated cards containing salary, location, tech tags, and source verification. </h3>

<img width="1366" height="768" alt="image" src="https://github.com/user-attachments/assets/575dcb31-926e-404f-8269-2ad5daf5cb1a" />

| Internal Mechanics | User Flow |
|---|---|
| Uses client-side sorting filters combined with cursor pagination. Feeds compile metadata dynamically and classify logos/backers. | User enters landing page → Feed queries Supabase for active listings → UI updates state asynchronously using Framer Motion. |

> 💡 **Value:** Instant access to a sorted list of developer jobs with no login needed.

### 2. Filtering Panel

<h3>Fine-grained search constraints supporting parameters such as remote status, location patterns, salary thresholds, and corporate attributes. </h3>

<img width="1366" height="768" alt="image" src="https://github.com/user-attachments/assets/de1f061f-66dc-4e8c-a4ac-730adc7b1ce5" />


| Internal Mechanics | User Flow |
|---|---|
| Uses a composite SQL where-clause constructor. Experience levels and domains are automatically matched using SQL text mappings. | User clicks checkboxes → Parameters serialize into URL query string → API executes matched SQL filter requests. |

> 💡 **Value:** Quickly filter out noise, showing only remote, high-paying jobs with visa support.

### 3. User Dashboard

<h3>A personalized hub for registered users. Handles saved jobs, job applications, alert intervals, and AI settings. </h3>

<img width="1366" height="738" alt="image" src="https://github.com/user-attachments/assets/4686e607-c668-4115-bf64-a1b143ae4214" />


| Internal Mechanics | User Flow |
|---|---|
| Connects to user profiles via UUID. Integrates database tables for application state, tracking status changes. | User clicks bookmark → Entry writes to `saved_jobs` table → Dashboard fetches bookmarks to display on next load. |

> 💡 **Value:** Keep track of application statuses and manage alerts in a single interface.

### 4. AI Resume Matching

<h3>Drag-and-drop resume scanner. Automatically matches technical skills, lists gaps, and scores matches against active jobs.</h3>

<img width="1366" height="768" alt="image" src="https://github.com/user-attachments/assets/a00f9fa2-ac31-48e2-8961-b3f9e662f133" />
<img width="1366" height="768" alt="image" src="https://github.com/user-attachments/assets/c1bf8524-6a83-496e-8e32-2c5d0a9d201e" />

| Internal Mechanics | User Flow |
|---|---|
| Uses PyPDF2 parsing combined with a Groq API model (Llama-3.3-70b). Employs semantic embedding scores. | User uploads PDF → Backend extracts raw text → AI analyzes skills → Dashboard displays categorized matches. |

> 💡 **Value:** Instantly identify which jobs match your resume, highlighting gaps to address.

---

## 📂 9. Repository Structure Map

| Directory / File | Role & Responsibility | Tech Stack |
|---|---|---|
| **📂 `backend/`** | **Core FastAPI server, ingestion routines, and background worker logic** | **FastAPI / Python** |
| &nbsp;&nbsp;&nbsp;&nbsp;`main.py` | API gateway, CORS configuration, lifespan scheduling initialization | Uvicorn / APScheduler |
| &nbsp;&nbsp;&nbsp;&nbsp;`config.py` | Global environment and configuration model validation | Pydantic Settings |
| &nbsp;&nbsp;&nbsp;&nbsp;`routers/` | Handles API endpoint divisions (AI, Jobs, Alerts, Users) | FastAPI Router |
| &nbsp;&nbsp;&nbsp;&nbsp;`scrapers/` | Direct crawlers and REST feed ingestion parsers | BeautifulSoup / httpx |
| &nbsp;&nbsp;&nbsp;&nbsp;`services/` | Core business logic: de-duplication hashers, AI scoring calls | Python / Groq SDK |
| **📂 `frontend/`** | **Interactive user client web application dashboard** | **Next.js / React 19** |
| &nbsp;&nbsp;&nbsp;&nbsp;`src/app/` | Next.js application pages: feed, dashboard, auth paths | App Router |
| &nbsp;&nbsp;&nbsp;&nbsp;`src/components/` | Reusable UI blocks (Job cards, Navbars, Filtering sidebars) | Tailwind CSS v4 |
| **📂 `supabase/`** | **Database migration schemas and security declarations** | **SQL / migrations** |

---

## ✨ 10. Key Platform Features

| | Feature | Description |
|---|---|---|
| 🔄 | **Custom Ingestion Engine** | Runs BeautifulSoup and custom extraction routines on 10+ sites including Wellfound, HasJob, YC, MigrateMate, and Arc.dev. |
| 🔐 | **Algorithmic Deduplication** | Utilizes structural SHA-256 metadata hashing. Ensures duplicate listings across platforms are consolidated cleanly. |
| 🤖 | **AI Resume Reviewer** | Scans PDF and text resumes, returns structured JSON stats, matching levels, missing requirements, and match scoring. |
| 🧹 | **Automatic Cleanups** | Active jobs older than 30 days are systematically flagged as inactive by background task processors. |

---

## 📈 11. Scalability & Future Roadmaps

While Liopleurodon is built to run on free infrastructure tiers, it is designed with production-grade scaling in mind. Our roadmap includes:

- **Vector Embeddings Scale** — Add HNSW vector index files to PostgreSQL to speed up semantic matching as database entries exceed 50,000.
- **Scraper Parallelization** — Migrate tasks from standard cron to Celery or Redis queues to execute scrapers in parallel without blocking FastAPI.
- **Automated Alerts** — Add automated communication channels like Telegram, Slack, and email notifications for newly posted matched positions.
- **API Caching Layer** — Use Redis to cache the landing page payload, reducing read queries to Supabase under heavy concurrent traffic.

---

## 🌱 12. Why It Matters

When information is gatekept, job seekers suffer. By distributing this codebase, we aim to provide a template for open data access.

> *"Open source software is not just about writing code; it's about removing artificial barriers, aligning access to data, and giving developers the tools to discover their path forward on their own terms."*

---

<div align="center">

### Commitment to Open Source

Liopleurodon is a real product, developed from the ground up, used daily by real developers, and committed to remaining **100% free** and community-driven.

Developed with ♥ by **SESHASHAYANAN** and the Open Source Community.

</div>
