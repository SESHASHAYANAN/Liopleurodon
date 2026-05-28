-- ══════════════════════════════════════════════════════════════════════════
-- Migration 003: Add ats_detected column to jobs table
-- Stores the Applicant Tracking System used for each job listing
-- ══════════════════════════════════════════════════════════════════════════

ALTER TABLE jobs ADD COLUMN IF NOT EXISTS ats_detected TEXT DEFAULT 'Unknown ATS';

-- Index for filtering by ATS
CREATE INDEX IF NOT EXISTS idx_jobs_ats_detected ON jobs(ats_detected);
