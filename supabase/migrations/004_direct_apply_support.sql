-- ══════════════════════════════════════════════════════════════════════════
-- Liopleurodon — Migration 004: Direct Apply Support
-- Adds user profile fields, direct-apply job metadata, and application tracking
-- ══════════════════════════════════════════════════════════════════════════

-- ─── Enrich user profiles for direct apply ──────────────────────────────
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS phone TEXT;
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS linkedin_url TEXT;
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS portfolio_url TEXT;
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS cover_letter_default TEXT;
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS location TEXT;
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS current_company TEXT;

-- ─── Add direct-apply support flags to jobs ─────────────────────────────
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS direct_apply_supported BOOLEAN DEFAULT false;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS direct_apply_ats TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS ats_job_id TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS ats_board_token TEXT;

-- ─── Enrich user_applications for direct apply tracking ─────────────────
ALTER TABLE user_applications ADD COLUMN IF NOT EXISTS apply_method TEXT DEFAULT 'external';
ALTER TABLE user_applications ADD COLUMN IF NOT EXISTS ats_response JSONB;
ALTER TABLE user_applications ADD COLUMN IF NOT EXISTS resume_used TEXT;
ALTER TABLE user_applications ADD COLUMN IF NOT EXISTS cover_letter_used TEXT;
ALTER TABLE user_applications ADD COLUMN IF NOT EXISTS submission_steps JSONB DEFAULT '[]';

-- ─── Resume storage table ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_resumes (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
  file_name TEXT NOT NULL,
  file_url TEXT NOT NULL,
  file_size INTEGER,
  is_default BOOLEAN DEFAULT false,
  uploaded_at TIMESTAMPTZ DEFAULT now()
);

-- ─── Indexes ────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_jobs_direct_apply ON jobs(direct_apply_supported)
  WHERE direct_apply_supported = true;
CREATE INDEX IF NOT EXISTS idx_user_resumes_user ON user_resumes(user_id);

-- ─── RLS for user_resumes ───────────────────────────────────────────────
ALTER TABLE user_resumes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own resumes"
  ON user_resumes FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own resumes"
  ON user_resumes FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own resumes"
  ON user_resumes FOR DELETE
  USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage resumes"
  ON user_resumes FOR ALL
  USING (true);
