-- Liopleurodon — Migration 002: Add is_featured, last_seen_at columns
-- Run this in the Supabase SQL Editor

-- Add is_featured column for seed/featured jobs
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT false;

-- Add last_seen_at column for staleness tracking
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ;

-- Add index for featured jobs
CREATE INDEX IF NOT EXISTS idx_jobs_featured ON jobs(is_featured) WHERE is_featured = true;

-- Add index for last_seen_at (staleness queries)
CREATE INDEX IF NOT EXISTS idx_jobs_last_seen ON jobs(last_seen_at);
