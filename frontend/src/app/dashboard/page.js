'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import Navbar from '@/components/Navbar';
import JobCard from '@/components/JobCard';
import JobDetailPanel from '@/components/JobDetailPanel';
import { supabase } from '@/lib/supabase';
import { Bookmark, Briefcase, Bell, FileText, Upload, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

const TABS = [
  { id: 'saved', label: 'Saved Jobs', icon: <Bookmark size={16} /> },
  { id: 'applied', label: 'Applications', icon: <Briefcase size={16} /> },
  { id: 'alerts', label: 'Job Alerts', icon: <Bell size={16} /> },
  { id: 'resume', label: 'AI Matching', icon: <Sparkles size={16} /> },
];

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const [activeTab, setActiveTab] = useState('saved');
  const [savedJobs, setSavedJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedJob, setSelectedJob] = useState(null);
  const [resumeText, setResumeText] = useState('');
  const [matchedJobs, setMatchedJobs] = useState([]);
  const [matching, setMatching] = useState(false);

  useEffect(() => {
    if (!user) return;
    loadData();
  }, [user, activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'saved') {
        const { data } = await supabase
          .from('saved_jobs')
          .select('*, jobs(*)')
          .eq('user_id', user.id)
          .order('created_at', { ascending: false });
        setSavedJobs((data || []).map(d => d.jobs).filter(Boolean));
      } else if (activeTab === 'applied') {
        const { data } = await supabase
          .from('user_applications')
          .select('*, jobs(*)')
          .eq('user_id', user.id)
          .order('applied_at', { ascending: false });
        setApplications(data || []);
      } else if (activeTab === 'alerts') {
        const { data } = await supabase
          .from('job_alerts')
          .select('*')
          .eq('user_id', user.id)
          .order('created_at', { ascending: false });
        setAlerts(data || []);
      }
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const handleResumeMatch = async () => {
    if (!resumeText.trim()) {
      toast.error('Please paste your resume text');
      return;
    }
    setMatching(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/ai/match-jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume_text: resumeText, limit: 20 }),
      });
      const data = await res.json();
      setMatchedJobs(data.matched_jobs || []);
      toast.success(`Found ${data.matched_jobs?.length || 0} matching jobs!`);
    } catch {
      toast.error('AI matching failed');
    }
    setMatching(false);
  };

  if (authLoading) {
    return (
      <>
        <Navbar onToggleFilters={() => {}} />
        <div style={{ textAlign: 'center', padding: 80, color: 'var(--text-muted)' }}>Loading...</div>
      </>
    );
  }

  if (!user) {
    return (
      <>
        <Navbar onToggleFilters={() => {}} />
        <div style={{ textAlign: 'center', padding: 80 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🔒</div>
          <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Sign in required</h2>
          <p style={{ color: 'var(--text-muted)' }}>Please sign in to access your dashboard.</p>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar onToggleFilters={() => {}} />
      <main style={{ maxWidth: 1200, margin: '0 auto', padding: 24 }}>
        {/* Header */}
        <div style={{ marginBottom: 32 }}>
          <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 4 }}>Dashboard</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>Manage your job search in one place.</p>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid var(--border-color)', paddingBottom: 0 }}>
          {TABS.map(tab => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex', alignItems: 'center', gap: 6,
                padding: '10px 16px', fontSize: 14, fontWeight: 600,
                background: 'none', border: 'none', cursor: 'pointer',
                color: activeTab === tab.id ? 'var(--accent-primary)' : 'var(--text-muted)',
                borderBottom: activeTab === tab.id ? '2px solid var(--accent-primary)' : '2px solid transparent',
                transition: 'all 0.2s', marginBottom: -1,
              }}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === 'saved' && (
          <div>
            {loading ? (
              <div style={{ color: 'var(--text-muted)', padding: 40, textAlign: 'center' }}>Loading saved jobs...</div>
            ) : savedJobs.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 60 }}>
                <Bookmark size={48} style={{ color: 'var(--text-muted)', marginBottom: 16 }} />
                <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>No saved jobs yet</h3>
                <p style={{ color: 'var(--text-muted)' }}>Bookmark jobs from the feed to see them here.</p>
              </div>
            ) : (
              <div className="job-grid">
                {savedJobs.map((job, i) => (
                  <JobCard key={job.id || i} job={job} index={i} onViewDetails={setSelectedJob} savedJobs={savedJobs.map(j => j.id)} />
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'applied' && (
          <div>
            {applications.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 60 }}>
                <Briefcase size={48} style={{ color: 'var(--text-muted)', marginBottom: 16 }} />
                <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>No applications tracked</h3>
                <p style={{ color: 'var(--text-muted)' }}>Applications you track will appear here.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {applications.map((app) => (
                  <div key={app.id} className="card" style={{ padding: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div>
                      <div style={{ fontWeight: 600 }}>{app.jobs?.title}</div>
                      <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>{app.jobs?.company_name}</div>
                    </div>
                    <span className={`badge ${app.status === 'offered' ? 'badge-success' : app.status === 'rejected' ? 'badge-error' : 'badge-primary'}`}>
                      {app.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'alerts' && (
          <div>
            {alerts.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 60 }}>
                <Bell size={48} style={{ color: 'var(--text-muted)', marginBottom: 16 }} />
                <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>No alerts set up</h3>
                <p style={{ color: 'var(--text-muted)' }}>Create alerts to get notified about new matching jobs.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {alerts.map((alert) => (
                  <div key={alert.id} className="card" style={{ padding: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div>
                      <div style={{ fontWeight: 600 }}>{alert.name}</div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                        {alert.frequency} • {alert.is_active ? '🟢 Active' : '⏸️ Paused'}
                      </div>
                    </div>
                    <button className="btn btn-ghost" onClick={async () => {
                      await supabase.from('job_alerts').delete().eq('id', alert.id);
                      setAlerts(prev => prev.filter(a => a.id !== alert.id));
                      toast.success('Alert deleted');
                    }}
                      style={{ color: 'var(--error)', fontSize: 13 }}>Delete</button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'resume' && (
          <div>
            <div className="card" style={{
              padding: 24, marginBottom: 24,
              background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.05), rgba(6, 182, 212, 0.05))',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                <Sparkles size={18} style={{ color: 'var(--accent-primary)' }} />
                <h3 style={{ fontSize: 16, fontWeight: 700 }}>AI Job Matching</h3>
              </div>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>
                Paste your resume below and our AI will find the top 20 jobs that match your skills and experience.
              </p>
              <textarea
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                placeholder="Paste your resume text here..."
                className="input"
                style={{ minHeight: 200, resize: 'vertical', marginBottom: 12, fontFamily: 'inherit' }}
              />
              <button className="btn btn-primary" onClick={handleResumeMatch} disabled={matching}
                style={{ width: '100%' }}>
                {matching ? 'Finding matches...' : '🔍 Find Matching Jobs'}
              </button>
            </div>

            {matchedJobs.length > 0 && (
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 16 }}>
                  Top {matchedJobs.length} Matches
                </h3>
                <div className="job-grid">
                  {matchedJobs.map((job, i) => (
                    <JobCard key={job.id || i} job={job} index={i} onViewDetails={setSelectedJob} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {selectedJob && <JobDetailPanel job={selectedJob} onClose={() => setSelectedJob(null)} />}
      </main>
    </>
  );
}
