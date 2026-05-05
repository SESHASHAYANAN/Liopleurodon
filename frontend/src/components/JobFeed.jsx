'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useFilters } from '@/context/FilterContext';
import { useAuth } from '@/context/AuthContext';
import { searchJobs } from '@/lib/api';
import { supabase } from '@/lib/supabase';
import JobCard from './JobCard';
import SkeletonCard from './SkeletonCard';
import EmptyState from './EmptyState';
import JobDetailPanel from './JobDetailPanel';
import toast from 'react-hot-toast';

const MAX_AUTO_RETRIES = 4;
const AUTO_RETRY_DELAYS = [2000, 4000, 8000, 15000]; // escalating delays

export default function JobFeed() {
  const { filters, resetFilters } = useFilters();
  const { user } = useAuth();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedJob, setSelectedJob] = useState(null);
  const [savedJobs, setSavedJobs] = useState([]);
  const [connectionError, setConnectionError] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const observerRef = useRef(null);
  const loadMoreRef = useRef(null);
  const retryTimerRef = useRef(null);
  const isMounted = useRef(true);

  // Cleanup on unmount
  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
      if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
    };
  }, []);

  // Fetch jobs
  const fetchJobs = useCallback(async (pageNum = 1, append = false, autoRetryAttempt = 0) => {
    if (pageNum === 1) setLoading(true);
    else setLoadingMore(true);

    try {
      const params = { ...filters, page: pageNum, per_page: 20 };
      // Clean empty params
      Object.keys(params).forEach(k => {
        if (params[k] === '' || params[k] === null || params[k] === undefined) delete params[k];
      });

      const data = await searchJobs(params);

      if (!isMounted.current) return;

      if (append) {
        setJobs(prev => [...prev, ...(data.jobs || [])]);
      } else {
        setJobs(data.jobs || []);
      }
      setTotalPages(data.total_pages || 1);
      setConnectionError(false);
      setRetryCount(0);
    } catch (err) {
      console.error('Job fetch error:', err);

      if (!isMounted.current) return;

      const isNetworkError = err.message === 'Failed to fetch' ||
        err.message.includes('NetworkError') ||
        err.name === 'TypeError';

      if (isNetworkError && autoRetryAttempt < MAX_AUTO_RETRIES) {
        // Auto-retry with escalating delays
        const delay = AUTO_RETRY_DELAYS[autoRetryAttempt] || 15000;
        setConnectionError(true);
        setRetryCount(autoRetryAttempt + 1);
        console.warn(`[JobFeed] Auto-retry ${autoRetryAttempt + 1}/${MAX_AUTO_RETRIES} in ${delay}ms`);

        retryTimerRef.current = setTimeout(() => {
          if (isMounted.current) {
            fetchJobs(pageNum, append, autoRetryAttempt + 1);
          }
        }, delay);
        return; // Don't set loading to false yet — keep showing skeleton
      }

      // All retries exhausted or non-network error
      setConnectionError(isNetworkError);
      if (!append) setJobs([]);
    } finally {
      if (isMounted.current) {
        setLoading(false);
        setLoadingMore(false);
      }
    }
  }, [filters]);

  // Fetch on filter change
  useEffect(() => {
    // Clear any pending retries when filters change
    if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
    setRetryCount(0);
    setConnectionError(false);
    setPage(1);
    fetchJobs(1, false, 0);
  }, [fetchJobs]);

  // Load saved jobs
  useEffect(() => {
    if (user) {
      supabase
        .from('saved_jobs')
        .select('job_id')
        .eq('user_id', user.id)
        .then(({ data }) => {
          setSavedJobs((data || []).map(d => d.job_id));
        });
    }
  }, [user]);

  // Infinite scroll observer
  useEffect(() => {
    if (observerRef.current) observerRef.current.disconnect();

    observerRef.current = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !loadingMore && page < totalPages) {
          const nextPage = page + 1;
          setPage(nextPage);
          fetchJobs(nextPage, true);
        }
      },
      { threshold: 0.1 }
    );

    if (loadMoreRef.current) {
      observerRef.current.observe(loadMoreRef.current);
    }

    return () => observerRef.current?.disconnect();
  }, [page, totalPages, loadingMore, fetchJobs]);

  // Save/unsave job
  const handleSave = async (jobId, save) => {
    if (!user) return;
    try {
      if (save) {
        await supabase.from('saved_jobs').insert({ user_id: user.id, job_id: jobId });
        setSavedJobs(prev => [...prev, jobId]);
        toast.success('Job saved!');
      } else {
        await supabase.from('saved_jobs').delete().eq('user_id', user.id).eq('job_id', jobId);
        setSavedJobs(prev => prev.filter(id => id !== jobId));
        toast.success('Job removed from saved.');
      }
    } catch {
      toast.error('Failed to update saved jobs.');
    }
  };

  // Manual retry handler
  const handleManualRetry = () => {
    if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
    setRetryCount(0);
    setConnectionError(false);
    setLoading(true);
    fetchJobs(1, false, 0);
  };

  return (
    <div>
      {/* Connection retry banner */}
      {connectionError && loading && (
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
          padding: '10px 16px', marginBottom: 12, borderRadius: 10,
          background: 'rgba(251, 191, 36, 0.1)', border: '1px solid rgba(251, 191, 36, 0.25)',
          fontSize: 13, color: 'var(--warning, #fbbf24)',
        }}>
          <span style={{
            width: 8, height: 8, borderRadius: '50%',
            background: 'var(--warning, #fbbf24)',
            animation: 'pulse 1.5s ease-in-out infinite',
          }} />
          Connecting to server… (attempt {retryCount}/{MAX_AUTO_RETRIES})
        </div>
      )}

      {/* Results Header */}
      {!loading && (
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          marginBottom: 16, padding: '0 4px',
        }}>
          <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
            {jobs.length > 0 ? `Showing ${jobs.length} jobs` : 'No results'}
          </span>
        </div>
      )}

      {/* Loading Skeletons */}
      {loading && (
        <div className="job-grid">
          {[...Array(6)].map((_, i) => <SkeletonCard key={i} />)}
        </div>
      )}

      {/* Empty State — with retry button if connection error */}
      {!loading && jobs.length === 0 && (
        connectionError ? (
          <div style={{
            textAlign: 'center', padding: '60px 20px',
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16,
          }}>
            <div style={{ fontSize: 48, opacity: 0.6 }}>🔌</div>
            <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>
              Backend server unreachable
            </h3>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', maxWidth: 360, lineHeight: 1.6 }}>
              Could not connect to the API server. Make sure the backend is running
              on <code style={{ fontSize: 12, background: 'var(--bg-elevated)', padding: '2px 6px', borderRadius: 4 }}>http://127.0.0.1:8000</code>
            </p>
            <button
              onClick={handleManualRetry}
              className="btn btn-primary"
              style={{ marginTop: 8, padding: '10px 28px', borderRadius: 10, fontSize: 14, cursor: 'pointer' }}
            >
              🔄 Retry Connection
            </button>
          </div>
        ) : (
          <EmptyState onReset={resetFilters} />
        )
      )}

      {/* Job Grid */}
      {!loading && jobs.length > 0 && (
        <div className="job-grid">
          {jobs.map((job, i) => (
            <JobCard
              key={job.id || i}
              job={job}
              index={i}
              onViewDetails={setSelectedJob}
              onSave={handleSave}
              savedJobs={savedJobs}
            />
          ))}
        </div>
      )}

      {/* Load More Trigger */}
      {page < totalPages && (
        <div ref={loadMoreRef} style={{ padding: 20, textAlign: 'center' }}>
          {loadingMore && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: 8 }}>
              {[1, 2, 3].map(i => (
                <div key={i} style={{
                  width: 8, height: 8, borderRadius: '50%',
                  background: 'var(--accent-primary)',
                  animation: `pulse 1s ease-in-out ${i * 0.15}s infinite`,
                }} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Detail Panel */}
      {selectedJob && (
        <JobDetailPanel job={selectedJob} onClose={() => setSelectedJob(null)} />
      )}
    </div>
  );
}
