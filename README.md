<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 960px; margin: 0 auto; padding: 20px; background-color: #ffffff;">

  <!-- HERO SECTION -->
  <div style="text-align: center; margin-bottom: 40px; padding: 50px 30px; background: linear-gradient(135deg, #f5f3ff 0%, #ecfdf5 100%); border-radius: 24px; border: 1px solid #e2e8f0; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.02);">
    <div style="font-size: 70px; margin-bottom: 12px; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.05));">🦕</div>
    <h1 style="font-size: 50px; font-weight: 900; color: #4f46e5; margin: 0 0 16px 0; letter-spacing: -1.5px; line-height: 1.1;">Liopleurodon</h1>
    <p style="font-size: 20px; color: #475569; max-width: 700px; margin: 0 auto 28px auto; font-weight: 500; line-height: 1.5;">
      A production-grade, self-sustaining global job aggregation engine. Scrapes, normalizes, and matches jobs from 10+ sources in real time using free-tier resources and AI embeddings.
    </p>
    <div style="display: flex; justify-content: center; gap: 14px; flex-wrap: wrap;">
      <span style="background-color: #4f46e5; color: #ffffff; padding: 8px 18px; border-radius: 24px; font-size: 13px; font-weight: 700; box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.15);">📈 2,000+ Active Users</span>
      <span style="background-color: #10b981; color: #ffffff; padding: 8px 18px; border-radius: 24px; font-size: 13px; font-weight: 700; box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.15);">💸 Forever Free</span>
      <span style="background-color: #06b6d4; color: #ffffff; padding: 8px 18px; border-radius: 24px; font-size: 13px; font-weight: 700; box-shadow: 0 4px 6px -1px rgba(6, 180, 212, 0.15);">🌐 10+ Live Sources</span>
      <span style="background-color: #3b82f6; color: #ffffff; padding: 8px 18px; border-radius: 24px; font-size: 13px; font-weight: 700; box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.15);">🤖 AI-Powered Matching</span>
    </div>
  </div>

  <!-- TABLE OF CONTENTS -->
  <div style="border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; margin-bottom: 32px; background-color: #f8fafc;">
    <h3 style="font-size: 18px; font-weight: 700; color: #0f172a; margin-top: 0; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
      <span>📋</span> Table of Contents
    </h3>
    <ul style="margin: 0; padding-left: 20px; font-size: 14px; color: #475569; display: grid; grid-template-columns: 1fr 1fr; gap: 8px 16px; list-style-type: square;">
      <li><a href="#introduction" style="color: #4f46e5; text-decoration: none; font-weight: 500;">Introduction & Market Context</a></li>
      <li><a href="#the-solution" style="color: #4f46e5; text-decoration: none; font-weight: 500;">The Liopleurodon Solution</a></li>
      <li><a href="#why-this-exists" style="color: #4f46e5; text-decoration: none; font-weight: 500;">Why This Repo Exists</a></li>
      <li><a href="#architecture" style="color: #4f46e5; text-decoration: none; font-weight: 500;">System Architecture</a></li>
      <li><a href="#system-design" style="color: #4f46e5; text-decoration: none; font-weight: 500;">System Design & Ingestion Flow</a></li>
      <li><a href="#frontend-backend" style="color: #4f46e5; text-decoration: none; font-weight: 500;">Frontend & Backend Mechanics</a></li>
      <li><a href="#setup" style="color: #4f46e5; text-decoration: none; font-weight: 500;">Clone & Setup Guide</a></li>
      <li><a href="#about-app" style="color: #4f46e5; text-decoration: none; font-weight: 500;">Deep Dive: Core App Features</a></li>
      <li><a href="#repo-structure" style="color: #4f46e5; text-decoration: none; font-weight: 500;">Repository Structure Map</a></li>
      <li><a href="#key-features" style="color: #4f46e5; text-decoration: none; font-weight: 500;">Key Platform Features</a></li>
      <li><a href="#scalability" style="color: #4f46e5; text-decoration: none; font-weight: 500;">Scalability & Future Roadmaps</a></li>
      <li><a href="#why-it-matters" style="color: #4f46e5; text-decoration: none; font-weight: 500;">Why It Matters</a></li>
    </ul>
  </div>

  <!-- SECTION: INTRODUCTION & PROBLEM -->
  <div id="introduction" style="border: 1px solid #e2e8f0; border-radius: 16px; padding: 32px; margin-bottom: 32px; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);">
    <h2 style="font-size: 24px; font-weight: 800; color: #0f172a; margin-top: 0; margin-bottom: 16px; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px; display: flex; align-items: center; gap: 8px;">
      <span style="color: #4f46e5;">📌</span> 1. Introduction & Market Context
    </h2>
    <p style="font-size: 15px; color: #334155; line-height: 1.7; margin-bottom: 20px;">
      Finding a job has become a monetized gatekeeper's market. The job-hunting landscape is saturated with platforms that commodify access to information. What should be an open channel between talent and opportunity is instead hidden behind paywalls, premium subscriptions, and artificial scarcity networks.
    </p>
    
    <!-- CALLOUT: MARKET PROBLEMS -->
    <div style="border-left: 4px solid #f59e0b; background-color: #fffbeb; padding: 18px; border-radius: 0 12px 12px 0; margin-bottom: 24px;">
      <strong style="color: #b45309; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; display: block; margin-bottom: 8px;">⚠️ The Current Job Platform Crisis</strong>
      <ul style="margin: 0; padding-left: 20px; font-size: 14px; color: #78350f; line-height: 1.6;">
        <li style="margin-bottom: 8px;"><strong>Subscribed Gatekeeping:</strong> Top aggregator services restrict notifications, semantic searches, and early-stage listings behind steep monthly subscription paywalls.</li>
        <li style="margin-bottom: 8px;"><strong>Data Silt & Fragmentation:</strong> Opportunities are scattered across dozens of isolated platforms (YC, LinkedIn, Wellfound, custom startup boards), forcing developers to maintain 10+ logins.</li>
        <li style="margin-bottom: 8px;"><strong>The Cost Barrier:</strong> Job seekers are asked to pay money to look for work, creating an unequal playing field where access is sold to the highest bidder.</li>
      </ul>
    </div>
    
    <p style="font-size: 15px; color: #334155; line-height: 1.7;">
      As developers and founders, we believe that discovering career opportunities should be transparent, lightning-fast, and open to everyone without an entry fee.
    </p>
  </div>

  <!-- SECTION: THE SOLUTION -->
  <div id="the-solution" style="border: 1px solid #e2e8f0; border-radius: 16px; padding: 32px; margin-bottom: 32px; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);">
    <h2 style="font-size: 24px; font-weight: 800; color: #0f172a; margin-top: 0; margin-bottom: 16px; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px; display: flex; align-items: center; gap: 8px;">
      <span style="color: #10b981;">💡</span> 2. The Liopleurodon Solution
    </h2>
    <p style="font-size: 15px; color: #334155; line-height: 1.7; margin-bottom: 24px;">
      Liopleurodon is a fully functional, self-updating, high-performance portal designed to aggregate, de-duplicate, classify, and match jobs across 10+ major developers platforms. By combining direct HTML scrapers and public API ingestions, it removes intermediate brokers to provide direct, clean data pipelines.
    </p>

    <!-- CORE PRODUCT PRINCIPLES GRID -->
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px;">
      <div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; background-color: #faf5ff;">
        <strong style="color: #7c3aed; font-size: 15px; display: block; margin-bottom: 6px;">⚡ Live Real-Time Ingestion</strong>
        <span style="font-size: 13.5px; color: #475569; line-height: 1.5; display: block;">
          The app executes live web scraping jobs each time the app runs and on scheduled intervals (every 10 minutes for web content, every 1 hour for APIs), capturing listings before they saturate.
        </span>
      </div>
      <div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; background-color: #ecfdf5;">
        <strong style="color: #059669; font-size: 15px; display: block; margin-bottom: 6px;">🛠️ Built Entirely From Scratch</strong>
        <span style="font-size: 13.5px; color: #475569; line-height: 1.5; display: block;">
          The scraping modules, data pipelines, normalization models, and keyword ranking matching matrices are custom built without bloated third-party software.
        </span>
      </div>
      <div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; background-color: #eff6ff;">
        <strong style="color: #2563eb; font-size: 15px; display: block; margin-bottom: 6px;">🆓 Free API Integrations</strong>
        <span style="font-size: 13.5px; color: #475569; line-height: 1.5; display: block;">
          We build on top of free tiers and public APIs (Adzuna, JSearch, TheirStack, Groq, OpenRouter) to provide maximum utility with no paid license dependencies.
        </span>
      </div>
      <div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; background-color: #fff7ed;">
        <strong style="color: #ea580c; font-size: 15px; display: block; margin-bottom: 6px;">💲 Total Infrastructure Cost: $0</strong>
        <span style="font-size: 13.5px; color: #475569; line-height: 1.5; display: block;">
          By optimizing serverless routines, client computations, and using Supabase's free SQL backend, the entire ecosystem costs exactly zero to operate.
        </span>
      </div>
    </div>

    <!-- CALLOUT: SCALE STATS -->
    <div style="border: 1px solid #d1fae5; background-color: #f0fdf4; border-radius: 12px; padding: 20px; display: flex; align-items: center; gap: 16px;">
      <div style="font-size: 32px;">🚀</div>
      <div>
        <strong style="color: #065f46; font-size: 15px; display: block;">Side Project to 2,000+ Active Users</strong>
        <span style="font-size: 13.5px; color: #047857; line-height: 1.5; display: block;">
          Liopleurodon started as a personal script to bypass broker sites. Today, it serves over 2,000 active developers finding jobs globally. We are committed to keeping this platform <strong>forever free</strong> and fully open-source.
        </span>
      </div>
    </div>
  </div>

  <!-- SECTION: WHY THIS EXISTS -->
  <div id="why-this-exists" style="border: 1px solid #e2e8f0; border-radius: 16px; padding: 32px; margin-bottom: 32px; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);">
    <h2 style="font-size: 24px; font-weight: 800; color: #0f172a; margin-top: 0; margin-bottom: 16px; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px; display: flex; align-items: center; gap: 8px;">
      <span style="color: #7c3aed;">🎯</span> 3. Why This Repo Exists
    </h2>
    <p style="font-size: 15px; color: #334155; line-height: 1.7; margin-bottom: 16px;">
      This codebase is released to dismantle the closed loops of job aggregation. It serves two distinct audiences:
    </p>
    <ul style="margin: 0; padding-left: 20px; font-size: 14.5px; color: #475569; line-height: 1.7; margin-bottom: 20px;">
      <li style="margin-bottom: 10px;">
        <strong>For Job Seekers:</strong> A lightning-fast, ad-free portal to discover real opportunities without paying monthly fees. Find real, un-sponsored start-up work, filter by VC-backers, remote parameters, and discover visa sponsorship with zero telemetry tracking.
      </li>
      <li style="margin-bottom: 10px;">
        <strong>For Developers:</strong> A robust, production-ready blueprint of a modern web scraper infrastructure. It demonstrates how to orchestrate asynchronous tasks in Python, manage PostgreSQL databases with Supabase, implement pgvector semantic match queries, and construct clean React/Next.js interfaces.
      </li>
    </ul>
    <p style="font-size: 15px; color: #334155; line-height: 1.7;">
      By reading and deploying this project, you gain a clear understanding of data pipelines, scraping rate-limits, deduplication heuristics, and AI integrations.
    </p>
  </div>

  <!-- SECTION: ARCHITECTURE -->
  <div id="architecture" style="border: 1px solid #e2e8f0; border-radius: 16px; padding: 32px; margin-bottom: 32px; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);">
    <h2 style="font-size: 24px; font-weight: 800; color: #0f172a; margin-top: 0; margin-bottom: 16px; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px; display: flex; align-items: center; gap: 8px;">
      <span style="color: #06b6d4;">🏗️</span> 4. System Architecture
    </h2>
    <p style="font-size: 15px; color: #334155; line-height: 1.7; margin-bottom: 20px;">
      The platform splits responsibilities between a client-heavy Next.js dashboard, an asynchronous FastAPI gateway serving operations, and a Supabase backend handling real-time data storage, vector matching, and user status schemas.
    </p>

    <!-- ARCHITECTURE DIAGRAM BLOCK -->
    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; margin-bottom: 24px;">
      <div style="text-align: center; font-family: monospace; font-size: 12px; color: #475569; overflow-x: auto; white-space: pre; line-height: 1.4;">
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    Next.js Frontend                                          │
│                    (React 19 / Tailwind CSS 4 / Lucide / Framer Motion)                      │
└──────────────────────────────┬──────────────────────────────▲────────────────────────────────┘
                               │ HTTP REST Requests           │ Client Auth & Direct DB Query
                               ▼ (Port 8000)                  │ (Supabase Client SDK)
┌─────────────────────────────────────────────────────────────┴────────────────────────────────┐
│                                    FastAPI Gateway                                           │
│                     (Python 3.10+ / Async Tasks / Uvicorn Server)                            │
├──────────────────────────────┬──────────────────────────────┬────────────────────────────────┤
│    Scrapers Pipeline         │      AI Parser/Matcher       │     Task Scheduler             │
│    (BeautifulSoup / httpx)   │     (Groq / OpenRouter)      │     (APScheduler Loop)         │
└──────────────┬───────────────┴──────────────┬───────────────┴──────────────┬─────────────────┘
               │ Write Scraped Jobs           │ Read/Embed Vectors           │ Check Alerts & Status
               ▼                              ▼                              ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   Supabase Database                                          │
│                     (PostgreSQL DB / pgvector Embeddings / RLS Policies)                     │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
      </div>
      <div style="text-align: center; margin-top: 12px; font-size: 12px; color: #64748b; font-style: italic;">
        Figure 4.1: High-Level Client-Server Architecture & Communication Lines
      </div>
    </div>

    <!-- TECHNOLOGY STACK TABLE -->
    <table style="width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 13.5px;">
      <thead>
        <tr style="background-color: #f1f5f9; text-align: left; border-bottom: 2px solid #cbd5e1;">
          <th style="padding: 10px 12px; font-weight: 700; color: #0f172a;">Layer</th>
          <th style="padding: 10px 12px; font-weight: 700; color: #0f172a;">Core Technologies</th>
          <th style="padding: 10px 12px; font-weight: 700; color: #0f172a;">Responsibility</th>
        </tr>
      </thead>
      <tbody>
        <tr style="border-bottom: 1px solid #e2e8f0;">
          <td style="padding: 10px 12px; font-weight: 600; color: #4f46e5;">Frontend</td>
          <td style="padding: 10px 12px; font-family: monospace;">Next.js 16 (App Router), React 19, Tailwind v4, Framer Motion</td>
          <td style="padding: 10px 12px; color: #475569;">Render landing UI, filters, application boards, PDF upload, and client caching.</td>
        </tr>
        <tr style="border-bottom: 1px solid #e2e8f0;">
          <td style="padding: 10px 12px; font-weight: 600; color: #10b981;">Backend</td>
          <td style="padding: 10px 12px; font-family: monospace;">FastAPI, Python 3.10+, Uvicorn, APScheduler, HTTPX</td>
          <td style="padding: 10px 12px; color: #475569;">Orchestrate scraper scheduler loops, process AI calls, compute score math, expose health routes.</td>
        </tr>
        <tr style="border-bottom: 1px solid #e2e8f0;">
          <td style="padding: 10px 12px; font-weight: 600; color: #06b6d4;">Database</td>
          <td style="padding: 10px 12px; font-family: monospace;">Supabase (PostgreSQL), pgvector, Row Level Security (RLS)</td>
          <td style="padding: 10px 12px; color: #475569;">Store aggregated jobs, tracking applications state, user bookmarks, alerts configuration, and vector profiles.</td>
        </tr>
        <tr>
          <td style="padding: 10px 12px; font-weight: 600; color: #f59e0b;">AI Logic</td>
          <td style="padding: 10px 12px; font-family: monospace;">Groq API, Google Gemini, OpenRouter (Llama 3.3 / Gemini Flash)</td>
          <td style="padding: 10px 12px; color: #475569;">Parse PDF layout structures, categorize matching/missing tech-stack lists, output career advisor summaries.</td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- SECTION: SYSTEM DESIGN -->
  <div id="system-design" style="border: 1px solid #e2e8f0; border-radius: 16px; padding: 32px; margin-bottom: 32px; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);">
    <h2 style="font-size: 24px; font-weight: 800; color: #0f172a; margin-top: 0; margin-bottom: 16px; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px; display: flex; align-items: center; gap: 8px;">
      <span style="color: #3b82f6;">⚙️</span> 5. Detailed System Design & Ingestion Pipelines
    </h2>
    <p style="font-size: 15px; color: #334155; line-height: 1.7; margin-bottom: 20px;">
      The platform manages dynamic data flow through a multi-stage ingestion pipeline. Raw job postings must be extracted, cleansed, normalized, deduplicated, and stored securely within 30 days window loops.
    </p>

    <!-- INGESTION & DE-DUPLICATION EXPLANATION -->
    <div style="background-color: #faf5ff; border: 1px solid #e9d5ff; border-radius: 12px; padding: 20px; margin-bottom: 24px;">
      <strong style="color: #6b21a8; font-size: 15px; display: block; margin-bottom: 8px;">🔑 The Hashing Deduplication Protocol</strong>
      <span style="font-size: 13.5px; color: #581c87; line-height: 1.6; display: block; margin-bottom: 10px;">
        To prevent identical postings from flooding the feed across different directories (e.g. ArcDev and LinkedIn reporting the same role), the backend generates a unique SHA-256 identifier based on structural properties:
      </span>
      <code style="display: block; background-color: #ffffff; border: 1px solid #ddd6fe; padding: 10px 14px; border-radius: 6px; font-family: monospace; font-size: 13px; color: #7c3aed; font-weight: bold; margin-bottom: 12px; text-align: center;">
        dedup_hash = SHA256( Lowercase( CompanyName + Title + LocationCity ) )
      </code>
      <span style="font-size: 13.5px; color: #581c87; line-height: 1.6; display: block;">
        Because the hash ignores date variables, when a scraper discovers the same job again, it runs a SQL `ON CONFLICT` operation in Supabase to simply update the <code>last_seen_at</code> timestamp and refresh details, rather than creating duplicates.
      </span>
    </div>

    <!-- SCRAPER PIPELINE DIAGRAM -->
    <h3 style="font-size: 16px; font-weight: 700; color: #0f172a; margin-top: 24px; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
      <span>⛓️</span> Scraper Pipeline Sequence
    </h3>
    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 24px;">
      <div style="font-family: monospace; font-size: 12px; color: #334155; line-height: 1.5; overflow-x: auto; white-space: pre;">
[ Raw Source Scrape ] ──► [ HTML Parsing / API Extraction ] ──► [ Classification Engine ]
                                                                       │ (Classify Domain / Level)
                                                                       ▼
[ Supabase Storage ]  ◄── [ Deduplication Check ] ◄─── [ SHA-256 Hashing Normalization ]
       │ (Upsert Rows)            (Hash Conflict?)
       ▼
[ Stale Cleanup Loop ] ──► (Mark is_active = False if last_seen_at &gt; 30 Days)
      </div>
      <div style="text-align: center; margin-top: 10px; font-size: 11px; color: #64748b; font-style: italic;">
        Figure 5.1: Real-Time Job Ingestion & Hashing Workflow
      </div>
    </div>

    <!-- DATABASE INTERACTION DIAGRAM -->
    <h3 style="font-size: 16px; font-weight: 700; color: #0f172a; margin-top: 24px; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
      <span>💾</span> Database Architecture & Data Flows
    </h3>
    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px;">
      <div style="font-family: monospace; font-size: 12px; color: #334155; line-height: 1.5; overflow-x: auto; white-space: pre;">
                    ┌─────────────────────────┐
                    │      jobs table         │◄───────────────────┐
                    │ (Stores Job Attributes) │                    │
                    └─────┬──────────────┬────┘                    │
                          │              │                         │
            Foreign Key   ▼              ▼  Foreign Key            │ Join on job_id
     ┌────────────────────┴──┐        ┌──┴───────────────────┐     │
     │   saved_jobs table    │        │ user_applications    │     │
     │ (Bookmarks, User IDs) │        │ (Tracking state)     │     │
     └───────────────────────┘        └──────────────────────┘     │
                                                                   │
                                      ┌──────────────────────┐     │
                                      │   job_alerts table   ├─────┘
                                      │ (Aggregates Alerts)  │
                                      └──────────────────────┘
      </div>
      <div style="text-align: center; margin-top: 10px; font-size: 11px; color: #64748b; font-style: italic;">
        Figure 5.2: Relational Schema & Schema Dependencies in Supabase PostgreSQL
      </div>
    </div>
  </div>

  <!-- SECTION: FRONTEND & BACKEND MECHANICS -->
  <div id="frontend-backend" style="border: 1px solid #e2e8f0; border-radius: 16px; padding: 32px; margin-bottom: 32px; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);">
    <h2 style="font-size: 24px; font-weight: 800; color: #0f172a; margin-top: 0; margin-bottom: 16px; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px; display: flex; align-items: center; gap: 8px;">
      <span style="color: #ec4899;">⚙️</span> 6. Frontend & Backend Mechanics
    </h2>
    
    <div style="margin-bottom: 20px;">
      <strong style="color: #4f46e5; font-size: 16px; display: block; margin-bottom: 8px;">⚡ How the Frontend Works</strong>
      <p style="font-size: 14.5px; color: #334155; margin: 0 0 12px 0; line-height: 1.6;">
        The frontend utilizes <strong>Next.js 16</strong> App Router with hybrid features:
      </p>
      <ul style="margin: 0; padding-left: 20px; font-size: 14px; color: #475569; line-height: 1.6;">
        <li style="margin-bottom: 6px;"><strong>Auth Context Syncing:</strong> A top-level React Auth Context communicates directly with Supabase Client instance to observe JWT tokens and route dashboard access.</li>
        <li style="margin-bottom: 6px;"><strong>Dynamic Layout panels:</strong> Uses Tailwind v4 utilities combined with <code>framer-motion</code> cards to slide open comprehensive job detail panels without breaking feed context.</li>
        <li style="margin-bottom: 6px;"><strong>Interactive State management:</strong> Client handles responsive toggling of filtering states (overlay for mobile devices, sidebar for desktop layout resolutions).</li>
      </ul>
    </div>

    <div>
      <strong style="color: #10b981; font-size: 16px; display: block; margin-bottom: 8px;">⚙️ How the Backend Works</strong>
      <p style="font-size: 14.5px; color: #334155; margin: 0 0 12px 0; line-height: 1.6;">
        The <strong>FastAPI Backend</strong> handles computational bottlenecks and API mappings:
      </p>
      <ul style="margin: 0; padding-left: 20px; font-size: 14px; color: #475569; line-height: 1.6;">
        <li style="margin-bottom: 6px;"><strong>Lifespan Task Schedulers:</strong> Uses FastAPI's async lifespan context combined with <code>APScheduler</code> to start concurrent task execution (API scrapers every hour, site scrapers every 10 mins).</li>
        <li style="margin-bottom: 6px;"><strong>Fast Validation Routers:</strong> Uses <code>Pydantic</code> to enforce typing parameters across endpoints (e.g. <code>/api/ai/keyword-match</code>).</li>
        <li style="margin-bottom: 6px;"><strong>Modular Routers Design:</strong> Split into distinct files (AI routers, jobs router, companies router, alerts manager) in the <code>routers/</code> directory to keep the core clean.</li>
      </ul>
    </div>

    <!-- INTERACTION DIAGRAM -->
    <h3 style="font-size: 16px; font-weight: 700; color: #0f172a; margin-top: 24px; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
      <span>↔️</span> Frontend/Backend API Interplay
    </h3>
    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px;">
      <div style="font-family: monospace; font-size: 12px; color: #334155; line-height: 1.5; overflow-x: auto; white-space: pre;">
[ Next.js Client ] ──(Upload PDF)──► [ FastAPI: /api/ai/match-resume-pdf ] ──► [ PyPDF2 Extraction ]
        ▲                                                                            │
        │                                                                            ▼
        └──────────(JSON Results)◄─── [ AI Processing (Groq API matching) ] ◄────────┘
      </div>
      <div style="text-align: center; margin-top: 10px; font-size: 11px; color: #64748b; font-style: italic;">
        Figure 6.1: Sync API flow during PDF resume matching
      </div>
    </div>
  </div>

  <!-- SECTION: HOW TO CLONE AND SETUP -->
  <div id="setup" style="border: 1px solid #e2e8f0; border-radius: 16px; padding: 32px; margin-bottom: 32px; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);">
    <h2 style="font-size: 24px; font-weight: 800; color: #0f172a; margin-top: 0; margin-bottom: 16px; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px; display: flex; align-items: center; gap: 8px;">
      <span style="color: #6366f1;">🚀</span> 7. How to Clone and Setup
    </h2>
    <p style="font-size: 15px; color: #334155; line-height: 1.6; margin-bottom: 20px;">
      Follow these instructions to deploy both the FastAPI backend and Next.js frontend in a local development environment.
    </p>

    <!-- PREREQUISITES -->
    <h3 style="font-size: 16px; font-weight: 700; color: #0f172a; margin-top: 20px; margin-bottom: 10px;">📋 Prerequisites</h3>
    <ul style="margin: 0; padding-left: 20px; font-size: 14px; color: #475569; line-height: 1.6; margin-bottom: 20px;">
      <li><strong>Node.js:</strong> v18.0.0 or higher</li>
      <li><strong>Python:</strong> v3.10.0 or higher</li>
      <li><strong>Supabase:</strong> A free account with an active PostgreSQL project</li>
      <li><strong>API Keys (Optional but Recommended):</strong> Groq, OpenRouter, JSearch, Adzuna</li>
    </ul>

    <!-- INSTALLATION -->
    <h3 style="font-size: 16px; font-weight: 700; color: #0f172a; margin-top: 20px; margin-bottom: 10px;">📦 Step 1: Clone Repository & Install Backend</h3>
    <pre style="background-color: #0f172a; color: #f8fafc; padding: 16px; border-radius: 12px; overflow-x: auto; font-family: monospace; font-size: 13.5px; line-height: 1.5; border: 1px solid #1e293b; margin-bottom: 20px;"><code>git clone https://github.com/SESHASHAYANAN/Liopleurodon.git
cd Liopleurodon

# Navigate to backend and create virtual environment
cd backend
python -m venv venv

# Activate Virtual Environment (Windows)
venv\Scripts\activate

# Activate Virtual Environment (macOS / Linux)
source venv/bin/activate

# Install all python requirements
pip install -r requirements.txt</code></pre>

    <h3 style="font-size: 16px; font-weight: 700; color: #0f172a; margin-top: 20px; margin-bottom: 10px;">📦 Step 2: Install Frontend Dependencies</h3>
    <pre style="background-color: #0f172a; color: #f8fafc; padding: 16px; border-radius: 12px; overflow-x: auto; font-family: monospace; font-size: 13.5px; line-height: 1.5; border: 1px solid #1e293b; margin-bottom: 20px;"><code># Navigate to frontend from root directory
cd ../frontend
npm install</code></pre>

    <!-- ENVIRONMENT SETUP -->
    <h3 style="font-size: 16px; font-weight: 700; color: #0f172a; margin-top: 20px; margin-bottom: 10px;">🔑 Step 3: Environment Setup</h3>
    <p style="font-size: 14px; color: #475569; margin-bottom: 12px;">Create the following environment files in the respective folders:</p>
    
    <div style="display: grid; grid-template-columns: 1fr; gap: 16px; margin-bottom: 24px;">
      <div>
        <strong style="font-size: 13.5px; color: #0f172a; display: block; margin-bottom: 6px;">Backend Environment Variables: <code>backend/.env</code></strong>
        <pre style="background-color: #0f172a; color: #f8fafc; padding: 14px; border-radius: 8px; overflow-x: auto; font-family: monospace; font-size: 12.5px; line-height: 1.4; border: 1px solid #1e293b; margin: 0;"><code>SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_ANON_KEY=your-anon-public-key
SUPABASE_SERVICE_KEY=your-service-role-admin-key

# Scraper Provider Keys
JSEARCH_API_KEY=your-jsearch-key
ADZUNA_APP_ID=your-adzuna-id
ADZUNA_API_KEY=your-adzuna-key

# AI Orchestration Keys
GROQ_API_KEY=your-groq-api-key
OPENROUTER_API_KEY=your-openrouter-key</code></pre>
      </div>
      <div>
        <strong style="font-size: 13.5px; color: #0f172a; display: block; margin-bottom: 6px;">Frontend Environment Variables: <code>frontend/.env.local</code></strong>
        <pre style="background-color: #0f172a; color: #f8fafc; padding: 14px; border-radius: 8px; overflow-x: auto; font-family: monospace; font-size: 12.5px; line-height: 1.4; border: 1px solid #1e293b; margin: 0;"><code>NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-supabase-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-public-key</code></pre>
      </div>
    </div>

    <!-- RUN COMMANDS -->
    <h3 style="font-size: 16px; font-weight: 700; color: #0f172a; margin-top: 20px; margin-bottom: 10px;">🏃 Step 4: Run Development Servers</h3>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px; font-size: 13.5px;">
      <thead>
        <tr style="background-color: #f8fafc; border-bottom: 1px solid #e2e8f0; text-align: left;">
          <th style="padding: 10px; font-weight: bold;">System</th>
          <th style="padding: 10px; font-weight: bold;">Directory</th>
          <th style="padding: 10px; font-weight: bold;">Terminal Command</th>
          <th style="padding: 10px; font-weight: bold;">Port Address</th>
        </tr>
      </thead>
      <tbody>
        <tr style="border-bottom: 1px solid #f1f5f9;">
          <td style="padding: 10px;">Backend REST Server</td>
          <td style="padding: 10px; font-family: monospace;">/backend</td>
          <td style="padding: 10px;"><code style="background-color: #f1f5f9; padding: 4px 8px; border-radius: 4px; font-family: monospace;">uvicorn main:app --reload --port 8000</code></td>
          <td style="padding: 10px; font-family: monospace;">http://localhost:8000</td>
        </tr>
        <tr>
          <td style="padding: 10px;">Next.js Frontend UI</td>
          <td style="padding: 10px; font-family: monospace;">/frontend</td>
          <td style="padding: 10px;"><code style="background-color: #f1f5f9; padding: 4px 8px; border-radius: 4px; font-family: monospace;">npm run dev</code></td>
          <td style="padding: 10px; font-family: monospace;">http://localhost:3000</td>
        </tr>
      </tbody>
    </table>

    <!-- WORKFLOW & PRODUCTION -->
    <h3 style="font-size: 16px; font-weight: 700; color: #0f172a; margin-top: 20px; margin-bottom: 10px;">🔧 Step 5: Development Workflow & Ingestions</h3>
    <p style="font-size: 14.5px; color: #334155; line-height: 1.6;">
      To test the scrapers manually without waiting for scheduler loop updates, run these scripts:
    </p>
    <ul style="margin: 0; padding-left: 20px; font-size: 14px; color: #475569; line-height: 1.6; margin-bottom: 24px;">
      <li style="margin-bottom: 6px;"><strong>Run All Scrapers:</strong> <code>python refresh_jobs.py</code></li>
      <li style="margin-bottom: 6px;"><strong>Run India Specific Ingestions:</strong> <code>python ingest_india_fast.py</code></li>
      <li style="margin-bottom: 6px;"><strong>Perform Database Stale Cleanup:</strong> <code>python verify_jobs.py</code></li>
    </ul>

    <!-- PRODUCTION NOTES -->
    <div style="border: 1px solid #e0f2fe; background-color: #f0f9ff; border-radius: 12px; padding: 18px;">
      <strong style="color: #0369a1; font-size: 14px; display: block; margin-bottom: 6px;">⚠️ Production Deployment Notes</strong>
      <span style="font-size: 13.5px; color: #0284c7; line-height: 1.5; display: block;">
        For production, host the Next.js app on Vercel and the FastAPI backend on Render, Fly.io, or AWS. Ensure you configure Supabase PostgreSQL migrations using the scripts located in <code>supabase/migrations/</code>. Use cron scheduling services if you choose to deploy FastAPI to serverless environments where stateful background scheduling is restricted.
      </span>
    </div>
  </div>

  <!-- SECTION: ABOUT THE APP -->
  <div id="about-app" style="border: 1px solid #e2e8f0; border-radius: 16px; padding: 32px; margin-bottom: 32px; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);">
    <h2 style="font-size: 24px; font-weight: 800; color: #0f172a; margin-top: 0; margin-bottom: 24px; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px; display: flex; align-items: center; gap: 8px;">
      <span style="color: #4f46e5;">📱</span> 8. Detailed App Walkthrough
    </h2>

    <!-- SUBSECTION: 1. HOMEPAGE -->
    <div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; margin-bottom: 28px; background-color: #ffffff;">
      <h3 style="font-size: 18px; font-weight: 700; color: #4f46e5; margin-top: 0; margin-bottom: 8px;">1. Homepage Feed</h3>
      <p style="font-size: 14px; color: #475569; margin: 0 0 16px 0; line-height: 1.6;">
        <strong>Description:</strong> The command center of the job search experience. Displays aggregated cards containing salary, location, tech tags, and source verification.
      </p>
      
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px;">
        <div style="font-size: 13.5px; color: #334155; line-height: 1.5;">
          <strong>Internal Mechanics:</strong> Uses client-side sorting filters combined with cursor pagination. Feeds compile metadata dynamically and classify logos/backers.
        </div>
        <div style="font-size: 13.5px; color: #334155; line-height: 1.5;">
          <strong>User Flow:</strong> User enters landing page &rarr; Feed queries Supabase for active listings &rarr; UI updates state asynchronously using Framer Motion.
        </div>
      </div>
      
      <div style="border: 1px solid #e2e8f0; background-color: #faf5ff; padding: 12px; border-radius: 8px; font-size: 13px; color: #6b21a8; font-weight: 600; text-align: center; margin-bottom: 20px;">
        💡 Value to User: Instant access to a sorted list of developer jobs with no login needed.
      </div>

      <!-- SCREENSHOT PLACEHOLDER -->
      <div style="background-color: #f1f5f9; border: 2px dashed #cbd5e1; border-radius: 12px; height: 100px; display: flex; align-items: center; justify-content: center; font-size: 13.5px; color: #64748b; font-weight: 600; margin-bottom: 20px;">
        [ Add Homepage Screenshot Here ]
      </div>

      <!-- HTML DIAGRAM BLOCK -->
      <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 16px;">
        <div style="font-family: monospace; font-size: 11.5px; color: #475569; white-space: pre; line-height: 1.4; overflow-x: auto;">
┌────────────────────────────────────────────────────────────────────────┐
│                        HOMEPAGE COMPONENT                              │
├────────────────────┬───────────────────────────────────┬───────────────┤
│    Filter Panel    │            Job Cards Feed         │   Trending    │
│    - Domain list   │ - Title, Company, Backer Badge    │ - Key skills  │
│    - Experience    │ - Salary range, Location details  │ - Tech tags   │
│    - Remote/Onsite │ - Apply details panel interaction │ - Counts      │
└────────────────────┴───────────────────────────────────┴───────────────┘
        </div>
      </div>
    </div>

    <!-- SUBSECTION: 2. FILTERS -->
    <div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; margin-bottom: 28px; background-color: #ffffff;">
      <h3 style="font-size: 18px; font-weight: 700; color: #10b981; margin-top: 0; margin-bottom: 8px;">2. Filtering Panel</h3>
      <p style="font-size: 14px; color: #475569; margin: 0 0 16px 0; line-height: 1.6;">
        <strong>Description:</strong> Fine-grained search constraints supporting parameters such as remote status, location patterns, salary thresholds, and corporate attributes.
      </p>
      
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px;">
        <div style="font-size: 13.5px; color: #334155; line-height: 1.5;">
          <strong>Internal Mechanics:</strong> Uses a composite SQL where-clause constructor. Experience levels and domains are automatically matched using SQL text mappings.
        </div>
        <div style="font-size: 13.5px; color: #334155; line-height: 1.5;">
          <strong>User Flow:</strong> User clicks checkboxes &rarr; Parameters serialize into URL query string &rarr; API executes matched SQL filter requests.
        </div>
      </div>
      
      <div style="border: 1px solid #e2e8f0; background-color: #ecfdf5; padding: 12px; border-radius: 8px; font-size: 13px; color: #047857; font-weight: 600; text-align: center; margin-bottom: 20px;">
        💡 Value to User: Quickly filter out noise, showing only remote, high-paying jobs with visa support.
      </div>

      <!-- SCREENSHOT PLACEHOLDER -->
      <div style="background-color: #f1f5f9; border: 2px dashed #cbd5e1; border-radius: 12px; height: 100px; display: flex; align-items: center; justify-content: center; font-size: 13.5px; color: #64748b; font-weight: 600; margin-bottom: 20px;">
        [ Add Filters Screenshot Here ]
      </div>

      <!-- HTML DIAGRAM BLOCK -->
      <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 16px;">
        <div style="font-family: monospace; font-size: 11.5px; color: #475569; white-space: pre; line-height: 1.4; overflow-x: auto;">
┌────────────────────────────────────────────────────────┐
│                   FILTER PANEL SELECTION               │
├────────────────────────────────────────────────────────┤
│ [✔] Remote    [✔] Hybrid     [ ] Onsite                │
│ Salary Range: [ $120,000  ] to [ $250,000+ ]           │
│ Level: [x] Senior  [ ] Mid   [ ] Junior  [ ] Intern    │
│ Perks: [✔] Visa Sponsorship  [✔] Relocation Assistance │
└────────────────────────────────────────────────────────┘
        </div>
      </div>
    </div>

    <!-- SUBSECTION: 3. DASHBOARD -->
    <div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; margin-bottom: 28px; background-color: #ffffff;">
      <h3 style="font-size: 18px; font-weight: 700; color: #06b6d4; margin-top: 0; margin-bottom: 8px;">3. User Dashboard</h3>
      <p style="font-size: 14px; color: #475569; margin: 0 0 16px 0; line-height: 1.6;">
        <strong>Description:</strong> A personalized hub for registered users. Handles saved jobs, job applications, alert intervals, and AI settings.
      </p>
      
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px;">
        <div style="font-size: 13.5px; color: #334155; line-height: 1.5;">
          <strong>Internal Mechanics:</strong> Connects to user profiles via UUID. Integrates database tables for application state, tracking status changes.
        </div>
        <div style="font-size: 13.5px; color: #334155; line-height: 1.5;">
          <strong>User Flow:</strong> User clicks bookmark &rarr; Entry writes to saved_jobs table &rarr; Dashboard fetches bookmarks to display on next load.
        </div>
      </div>
      
      <div style="border: 1px solid #e2e8f0; background-color: #ecfeff; padding: 12px; border-radius: 8px; font-size: 13px; color: #0891b2; font-weight: 600; text-align: center; margin-bottom: 20px;">
        💡 Value to User: Keep track of application statuses and manage alerts in a single interface.
      </div>

      <!-- SCREENSHOT PLACEHOLDER -->
      <div style="background-color: #f1f5f9; border: 2px dashed #cbd5e1; border-radius: 12px; height: 100px; display: flex; align-items: center; justify-content: center; font-size: 13.5px; color: #64748b; font-weight: 600; margin-bottom: 20px;">
        [ Add Dashboard Screenshot Here ]
      </div>

      <!-- HTML DIAGRAM BLOCK -->
      <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 16px;">
        <div style="font-family: monospace; font-size: 11.5px; color: #475569; white-space: pre; line-height: 1.4; overflow-x: auto;">
┌────────────────────────────────────────────────────────┐
│                     USER DASHBOARD                     │
├────────────────────────────────────────────────────────┤
│ [ Saved Jobs (8) ]  [ Applications (3) ]  [ Alerts ]   │
│                                                        │
│  - Senior React Eng @ Stripe   ──► Status: Applied     │
│  - Python Developer @ Supabase ──► Status: Interview   │
│  - AI Researcher @ Groq        ──► Status: Offered     │
└────────────────────────────────────────────────────────┘
        </div>
      </div>
    </div>

    <!-- SUBSECTION: 4. AI RESUME -->
    <div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; background-color: #ffffff;">
      <h3 style="font-size: 18px; font-weight: 700; color: #7c3aed; margin-top: 0; margin-bottom: 8px;">4. AI Resume Matching</h3>
      <p style="font-size: 14px; color: #475569; margin: 0 0 16px 0; line-height: 1.6;">
        <strong>Description:</strong> Drag-and-drop resume scanner. Automatically matches technical skills, lists gaps, and scores matches against active jobs.
      </p>
      
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px;">
        <div style="font-size: 13.5px; color: #334155; line-height: 1.5;">
          <strong>Internal Mechanics:</strong> Uses PyPDF2 parsing combined with a Groq API model (Llama-3.3-70b). Employs semantic embedding scores.
        </div>
        <div style="font-size: 13.5px; color: #334155; line-height: 1.5;">
          <strong>User Flow:</strong> User uploads PDF &rarr; Backend extracts raw text &rarr; AI analyzes skills &rarr; Dashboard displays categorized matches.
        </div>
      </div>
      
      <div style="border: 1px solid #e2e8f0; background-color: #f5f3ff; padding: 12px; border-radius: 8px; font-size: 13px; color: #6d28d9; font-weight: 600; text-align: center; margin-bottom: 20px;">
        💡 Value to User: Instantly identify which jobs match your resume, highlighting gaps to address.
      </div>

      <!-- SCREENSHOT PLACEHOLDER -->
      <div style="background-color: #f1f5f9; border: 2px dashed #cbd5e1; border-radius: 12px; height: 100px; display: flex; align-items: center; justify-content: center; font-size: 13.5px; color: #64748b; font-weight: 600; margin-bottom: 20px;">
        [ Add AI Resume Screenshot Here ]
      </div>

      <!-- HTML DIAGRAM BLOCK -->
      <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 16px;">
        <div style="font-family: monospace; font-size: 11.5px; color: #475569; white-space: pre; line-height: 1.4; overflow-x: auto;">
┌────────────────────────────────────────────────────────┐
│                  AI RESUME SCANNER                     │
├────────────────────────────────────────────────────────┤
│ Match Score: [ 89% ] - Level Match: Junior/Mid         │
│                                                        │
│ ✔ Matching Skills: React, Node.js, Python, PostgreSQL  │
│ ✘ Missing Skills: Docker, Kubernetes, AWS, Redis       │
│ 🗣 Career Advisor: "Solid match for mid-level backend." │
└────────────────────────────────────────────────────────┘
        </div>
      </div>
    </div>
  </div>

  <!-- SECTION: REPOSITORY STRUCTURE -->
  <div id="repo-structure" style="border: 1px solid #e2e8f0; border-radius: 16px; padding: 32px; margin-bottom: 32px; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);">
    <h2 style="font-size: 24px; font-weight: 800; color: #0f172a; margin-top: 0; margin-bottom: 16px; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px; display: flex; align-items: center; gap: 8px;">
      <span style="color: #64748b;">📂</span> 9. Repository Structure Map
    </h2>
    <p style="font-size: 15px; color: #334155; line-height: 1.7; margin-bottom: 16px;">
      Review the layout of the folders and files below to understand the components and structure of the repository:
    </p>

    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; font-family: 'Fira Code', monospace; font-size: 13px; color: #334155; overflow-x: auto; line-height: 1.45;">
Liopleurodon/
├── backend/                  # FastAPI Application
│   ├── main.py               # API Gateway & Scheduler Initialization
│   ├── config.py             # Settings using Pydantic Settings
│   ├── database.py           # Supabase DB Admin and Public Clients
│   ├── refresh_jobs.py       # Scraper Ingestion Coordination
│   ├── requirements.txt      # Backend Python Dependencies
│   ├── routers/              # API Endpoint Routes
│   │   ├── ai.py             # AI Matches, CV Parsers, and Quality Scoring
│   │   ├── alerts.py         # Subscriptions & Alerts Configurations
│   │   ├── jobs.py           # Search, Filtering, and Pagination Routes
│   │   └── users.py          # Bookmarks and Applications State Mappings
│   ├── scrapers/             # Custom Extraction Scripts
│   │   ├── base.py           # Abstract Base Class for Ingestion
│   │   ├── india_startups.py # Custom Indian Startup Job Board Scraper
│   │   ├── web_scraper.py    # BeautifulSoup parsers & expired jobs logic
│   │   ├── yc_jobs.py        # Algolia-based Y-Combinator Crawler
│   │   └── adzuna.py         # Adzuna REST Aggregator Integration
│   └── services/             # Core Backend Processing
│       ├── ai_service.py     # Groq & OpenRouter REST Call Mapping
│       └── deduplication.py  # SHA-256 Hashing Algorithms
├── frontend/                 # Next.js Application
│   ├── src/
│   │   ├── app/              # Routes & Navigation Mappings
│   │   │   ├── layout.js     # Shared App Shell & Global Configs
│   │   │   ├── page.js       # Main Job Search Dashboard Landing
│   │   │   └── dashboard/    # User Dashboard (AI match, Saved bookmarks)
│   │   ├── components/       # Component Library
│   │   │   ├── JobFeed.jsx   # Grid view rendering for jobs
│   │   │   └── FilterPanel.css # Custom layout properties
│   │   ├── context/          # React Context State (AuthContext.js)
│   │   └── lib/              # Client API Wrapper Mappings
│   ├── package.json          # Node dependencies & commands
│   └── next.config.mjs       # Build instructions for client application
└── supabase/
    └── migrations/           # SQL Database Schemas
    </div>
  </div>

  <!-- SECTION: KEY FEATURES -->
  <div id="key-features" style="border: 1px solid #e2e8f0; border-radius: 16px; padding: 32px; margin-bottom: 32px; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);">
    <h2 style="font-size: 24px; font-weight: 800; color: #0f172a; margin-top: 0; margin-bottom: 16px; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px; display: flex; align-items: center; gap: 8px;">
      <span style="color: #f59e0b;">✨</span> 10. Key Platform Features
    </h2>
    
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px;">
      <div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px;">
        <strong style="color: #4f46e5; font-size: 15px; display: block; margin-bottom: 6px;">✨ Custom Ingestion Engine</strong>
        <span style="font-size: 13.5px; color: #475569; line-height: 1.5; display: block;">
          Runs beautiful soup and custom extraction routines on 10+ sites including Wellfound, HasJob, YC, MigrateMate, and Arc.dev.
        </span>
      </div>
      <div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px;">
        <strong style="color: #10b981; font-size: 15px; display: block; margin-bottom: 6px;">✨ Algorithmic Deduplication</strong>
        <span style="font-size: 13.5px; color: #475569; line-height: 1.5; display: block;">
          Utilizes structural SHA-256 metadata hashing. Ensures duplicate listings across platforms are consolidated cleanly.
        </span>
      </div>
      <div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px;">
        <strong style="color: #06b6d4; font-size: 15px; display: block; margin-bottom: 6px;">✨ AI Resume Reviewer</strong>
        <span style="font-size: 13.5px; color: #475569; line-height: 1.5; display: block;">
          Scans PDF and text resumes, returns structured JSON stats, matching levels, missing requirements, and match scoring.
        </span>
      </div>
      <div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px;">
        <strong style="color: #f59e0b; font-size: 15px; display: block; margin-bottom: 6px;">✨ Automatic Cleanups</strong>
        <span style="font-size: 13.5px; color: #475569; line-height: 1.5; display: block;">
          Active jobs older than 30 days are systematically flagged as inactive by background task processors.
        </span>
      </div>
    </div>
  </div>

  <!-- SECTION: SCALABILITY & FUTURE IMPROVEMENTS -->
  <div id="scalability" style="border: 1px solid #e2e8f0; border-radius: 16px; padding: 32px; margin-bottom: 32px; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);">
    <h2 style="font-size: 24px; font-weight: 800; color: #0f172a; margin-top: 0; margin-bottom: 16px; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px; display: flex; align-items: center; gap: 8px;">
      <span style="color: #0d9488;">📈</span> 11. Scalability & Future Roadmaps
    </h2>
    <p style="font-size: 15px; color: #334155; line-height: 1.7; margin-bottom: 20px;">
      While Liopleurodon is built to run on free infrastructure tiers, it is designed with production-grade scaling in mind. Our roadmap includes:
    </p>
    <ul style="margin: 0; padding-left: 20px; font-size: 14.5px; color: #475569; line-height: 1.7;">
      <li style="margin-bottom: 10px;">
        <strong>Vector Embeddings Scale:</strong> Add HNSW vector index files to PostgreSQL to speed up semantic matching as database entries exceed 50,000.
      </li>
      <li style="margin-bottom: 10px;">
        <strong>Scraper Parallelization:</strong> Migrate tasks from standard cron to Celery or Redis queues to execute scrapers in parallel without blocking FastAPI.
      </li>
      <li style="margin-bottom: 10px;">
        <strong>Automated Alerts:</strong> Add automated communication channels like Telegram, Slack, and email notifications for newly posted matched positions.
      </li>
      <li style="margin-bottom: 10px;">
        <strong>API Caching Layer:</strong> Use Redis to cache the landing page payload, reducing read queries to Supabase under heavy concurrent traffic.
      </li>
    </ul>
  </div>

  <!-- SECTION: WHY IT MATTERS -->
  <div id="why-it-matters" style="border: 1px solid #e2e8f0; border-radius: 16px; padding: 32px; margin-bottom: 32px; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);">
    <h2 style="font-size: 24px; font-weight: 800; color: #0f172a; margin-top: 0; margin-bottom: 16px; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px; display: flex; align-items: center; gap: 8px;">
      <span style="color: #6366f1;">🌱</span> 12. Why It Matters
    </h2>
    <p style="font-size: 15px; color: #334155; line-height: 1.7; margin-bottom: 16px;">
      When information is gatekept, job seekers suffer. By distributing this codebase, we aim to provide a template for open data access.
    </p>
    <blockquote style="margin: 20px 0; padding: 16px 20px; background-color: #f8fafc; border-left: 4px solid #4f46e5; border-radius: 0 12px 12px 0; font-style: italic; color: #475569; font-size: 14.5px; line-height: 1.6;">
      "Open source software is not just about writing code; it's about removing artificial barriers, aligning access to data, and giving developers the tools to discover their path forward on their own terms."
    </blockquote>
  </div>

  <!-- CLOSING SECTION -->
  <div style="text-align: center; padding: 40px 20px; background: linear-gradient(135deg, #ecfdf5 0%, #f5f3ff 100%); border-radius: 20px; border: 1px solid #e2e8f0;">
    <h3 style="font-size: 22px; font-weight: 800; color: #0f172a; margin-top: 0; margin-bottom: 8px;">Commitment to Open Source</h3>
    <p style="font-size: 14.5px; color: #475569; max-width: 600px; margin: 0 auto 20px auto; line-height: 1.6;">
      Liopleurodon is a real product, developed from the ground up, used daily by real developers, and committed to remaining <strong>100% free</strong> and community-driven.
    </p>
    <div style="font-size: 13px; color: #94a3b8; font-weight: 600;">
      Developed with ♥ by SESHASHAYANAN and the Open Source Community.
    </div>
  </div>

</div>
