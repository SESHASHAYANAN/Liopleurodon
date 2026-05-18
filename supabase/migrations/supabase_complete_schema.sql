-- ══════════════════════════════════════════════════════════════════════════
-- Liopleurodon — Complete Supabase Schema
-- Copy and paste this entire file into the Supabase SQL Editor and click Run
-- ══════════════════════════════════════════════════════════════════════════

-- ─── Enable Extensions ──────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS vector;

-- ─── Jobs Table (60+ fields) ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS jobs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  company_name TEXT NOT NULL,
  company_logo_url TEXT,
  company_size TEXT,
  company_industry TEXT,
  company_type TEXT,
  vc_backer TEXT,
  funding_stage TEXT,
  location_city TEXT,
  location_country TEXT,
  remote_type TEXT,
  visa_sponsorship BOOLEAN DEFAULT false,
  relocation_support BOOLEAN DEFAULT false,
  work_authorization TEXT,
  salary_min NUMERIC,
  salary_max NUMERIC,
  salary_currency TEXT DEFAULT 'USD',
  salary_period TEXT DEFAULT 'yearly',
  experience_level TEXT,
  years_experience_min INTEGER,
  years_experience_max INTEGER,
  job_type TEXT,
  description TEXT,
  responsibilities TEXT[],
  requirements TEXT[],
  benefits TEXT[],
  skills_required TEXT[],
  skills_preferred TEXT[],
  tech_stack TEXT[],
  apply_url TEXT,
  easy_apply BOOLEAN DEFAULT false,
  source_platforms TEXT[] NOT NULL DEFAULT '{}',
  posted_date TIMESTAMPTZ,
  expiry_date TIMESTAMPTZ,
  is_stealth BOOLEAN DEFAULT false,
  is_active BOOLEAN DEFAULT true,
  embedding vector(1536),
  dedup_hash TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- ─── Companies Table ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS companies (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  logo_url TEXT,
  description TEXT,
  industry TEXT,
  company_type TEXT,
  size TEXT,
  founded_year INTEGER,
  headquarters TEXT,
  website_url TEXT,
  careers_url TEXT,
  vc_backers TEXT[],
  funding_stage TEXT,
  total_funding TEXT,
  glassdoor_rating NUMERIC,
  is_stealth BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- ─── User Profiles (extends Supabase Auth) ──────────────────────────────
CREATE TABLE IF NOT EXISTS user_profiles (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  full_name TEXT,
  email TEXT,
  avatar_url TEXT,
  resume_url TEXT,
  resume_embedding vector(1536),
  preferences JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- ─── Saved Jobs ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS saved_jobs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
  job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, job_id)
);

-- ─── User Applications ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_applications (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
  job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
  status TEXT DEFAULT 'applied',
  applied_at TIMESTAMPTZ DEFAULT now(),
  notes TEXT,
  UNIQUE(user_id, job_id)
);

-- ─── Job Alerts ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS job_alerts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  filters JSONB NOT NULL,
  is_active BOOLEAN DEFAULT true,
  frequency TEXT DEFAULT 'daily',
  last_triggered_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);


-- ═════════════════════════════════════════════════════════════════════════
-- INDEXES
-- ═════════════════════════════════════════════════════════════════════════

CREATE INDEX IF NOT EXISTS idx_jobs_dedup_hash ON jobs(dedup_hash);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company_name);
CREATE INDEX IF NOT EXISTS idx_jobs_posted ON jobs(posted_date DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_active ON jobs(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_jobs_remote ON jobs(remote_type);
CREATE INDEX IF NOT EXISTS idx_jobs_experience ON jobs(experience_level);
CREATE INDEX IF NOT EXISTS idx_jobs_type ON jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_jobs_company_type ON jobs(company_type);
CREATE INDEX IF NOT EXISTS idx_companies_slug ON companies(slug);
CREATE INDEX IF NOT EXISTS idx_saved_jobs_user ON saved_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_applications_user ON user_applications(user_id);
CREATE INDEX IF NOT EXISTS idx_job_alerts_user ON job_alerts(user_id);


-- ═════════════════════════════════════════════════════════════════════════
-- FUNCTIONS
-- ═════════════════════════════════════════════════════════════════════════

-- ─── pgvector Similarity Search ─────────────────────────────────────────
CREATE OR REPLACE FUNCTION match_jobs(
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 10,
  exclude_id uuid DEFAULT NULL
)
RETURNS TABLE (
  id uuid,
  title text,
  company_name text,
  company_logo_url text,
  location_city text,
  remote_type text,
  salary_min numeric,
  salary_max numeric,
  experience_level text,
  apply_url text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    j.id,
    j.title,
    j.company_name,
    j.company_logo_url,
    j.location_city,
    j.remote_type,
    j.salary_min,
    j.salary_max,
    j.experience_level,
    j.apply_url,
    1 - (j.embedding <=> query_embedding) AS similarity
  FROM jobs j
  WHERE
    j.is_active = true
    AND j.embedding IS NOT NULL
    AND (exclude_id IS NULL OR j.id != exclude_id)
    AND 1 - (j.embedding <=> query_embedding) > match_threshold
  ORDER BY j.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- ─── Auto-create user profile on signup ─────────────────────────────────
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  INSERT INTO user_profiles (id, email, full_name)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email)
  );
  RETURN NEW;
END;
$$;

-- ─── Auto-update updated_at timestamp ───────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;


-- ═════════════════════════════════════════════════════════════════════════
-- TRIGGERS
-- ═════════════════════════════════════════════════════════════════════════

-- Auto-create user profile when a new user signs up
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- Auto-update timestamps
DROP TRIGGER IF EXISTS update_jobs_updated_at ON jobs;
CREATE TRIGGER update_jobs_updated_at
  BEFORE UPDATE ON jobs
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS update_companies_updated_at ON companies;
CREATE TRIGGER update_companies_updated_at
  BEFORE UPDATE ON companies
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles;
CREATE TRIGGER update_user_profiles_updated_at
  BEFORE UPDATE ON user_profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ═════════════════════════════════════════════════════════════════════════
-- ROW LEVEL SECURITY (RLS)
-- ═════════════════════════════════════════════════════════════════════════

ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_alerts ENABLE ROW LEVEL SECURITY;

-- ─── Jobs Policies ──────────────────────────────────────────────────────
-- Anyone can read jobs
CREATE POLICY "Jobs are publicly readable"
  ON jobs FOR SELECT
  USING (true);

-- Service role can insert/update jobs (the backend uses service_role key)
CREATE POLICY "Service role can insert jobs"
  ON jobs FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Service role can update jobs"
  ON jobs FOR UPDATE
  USING (true);

CREATE POLICY "Service role can delete jobs"
  ON jobs FOR DELETE
  USING (true);

-- ─── Companies Policies ─────────────────────────────────────────────────
CREATE POLICY "Companies are publicly readable"
  ON companies FOR SELECT
  USING (true);

CREATE POLICY "Service role can insert companies"
  ON companies FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Service role can update companies"
  ON companies FOR UPDATE
  USING (true);

-- ─── User Profiles Policies ─────────────────────────────────────────────
CREATE POLICY "Users can view own profile"
  ON user_profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON user_profiles FOR UPDATE
  USING (auth.uid() = id);

-- Allow the trigger function (SECURITY DEFINER) to insert profiles
CREATE POLICY "Service role can insert profiles"
  ON user_profiles FOR INSERT
  WITH CHECK (true);

-- ─── Saved Jobs Policies ────────────────────────────────────────────────
CREATE POLICY "Users can view own saved jobs"
  ON saved_jobs FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own saved jobs"
  ON saved_jobs FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own saved jobs"
  ON saved_jobs FOR DELETE
  USING (auth.uid() = user_id);

-- ─── User Applications Policies ─────────────────────────────────────────
CREATE POLICY "Users can view own applications"
  ON user_applications FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own applications"
  ON user_applications FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own applications"
  ON user_applications FOR UPDATE
  USING (auth.uid() = user_id);

-- ─── Job Alerts Policies ────────────────────────────────────────────────
CREATE POLICY "Users can view own alerts"
  ON job_alerts FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own alerts"
  ON job_alerts FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own alerts"
  ON job_alerts FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own alerts"
  ON job_alerts FOR DELETE
  USING (auth.uid() = user_id);


-- ═════════════════════════════════════════════════════════════════════════
-- DONE! Your database is now ready.
-- Next steps:
--   1. Start the backend:  cd backend && uvicorn main:app --reload
--   2. Start the frontend: cd frontend && npm run dev
--   3. Trigger a scrape:   POST http://localhost:8000/api/scrape/trigger
-- ═════════════════════════════════════════════════════════════════════════
