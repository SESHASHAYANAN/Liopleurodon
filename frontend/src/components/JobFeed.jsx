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
  const observerRef = useRef(null);
  const loadMoreRef = useRef(null);

  // Fetch jobs
  const fetchJobs = useCallback(async (pageNum = 1, append = false) => {
    if (pageNum === 1) setLoading(true);
    else setLoadingMore(true);

    try {
      const params = { ...filters, page: pageNum, per_page: 20 };
      // Clean empty params
      Object.keys(params).forEach(k => {
        if (params[k] === '' || params[k] === null || params[k] === undefined) delete params[k];
      });

      const data = await searchJobs(params);
      if (append) {
        setJobs(prev => [...prev, ...(data.jobs || [])]);
      } else {
        setJobs(data.jobs || []);
      }
      setTotalPages(data.total_pages || 1);
    } catch (err) {
      console.error('Job fetch error:', err);
      // If backend is down, show empty state
      if (!append) setJobs([]);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [filters]);

  // Fetch on filter change
  useEffect(() => {
    setPage(1);
    fetchJobs(1, false);
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

  return (
    <div>
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

      {/* Empty State */}
      {!loading && jobs.length === 0 && (
        <EmptyState onReset={resetFilters} />
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
