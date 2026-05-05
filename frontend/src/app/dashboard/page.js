'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/context/AuthContext';
import Navbar from '@/components/Navbar';
import JobCard from '@/components/JobCard';
import JobDetailPanel from '@/components/JobDetailPanel';
import { supabase } from '@/lib/supabase';
import { matchResumeWithPDF } from '@/lib/api';
import { Bookmark, Briefcase, Bell, FileText, Upload, Sparkles, X, CheckCircle, AlertCircle } from 'lucide-react';
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

  // AI Matching state
  const [pdfFile, setPdfFile] = useState(null);
  const [resumeText, setResumeText] = useState('');
  const [matchedJobs, setMatchedJobs] = useState([]);
  const [parsedResume, setParsedResume] = useState(null);
  const [resumePreview, setResumePreview] = useState('');
  const [matching, setMatching] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [matchMode, setMatchMode] = useState('pdf'); // 'pdf' or 'text'
  const [totalAnalyzed, setTotalAnalyzed] = useState(0);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (user) { loadData(); }
    else { setLoading(false); setSavedJobs([]); setApplications([]); setAlerts([]); }
  }, [user, activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'saved') {
        const { data } = await supabase.from('saved_jobs').select('*, jobs(*)').eq('user_id', user.id).order('created_at', { ascending: false });
        setSavedJobs((data || []).map(d => d.jobs).filter(Boolean));
      } else if (activeTab === 'applied') {
        const { data } = await supabase.from('user_applications').select('*, jobs(*)').eq('user_id', user.id).order('applied_at', { ascending: false });
        setApplications(data || []);
      } else if (activeTab === 'alerts') {
        const { data } = await supabase.from('job_alerts').select('*').eq('user_id', user.id).order('created_at', { ascending: false });
        setAlerts(data || []);
      }
    } catch (err) { console.error(err); }
    setLoading(false);
  };

  // ─── PDF Upload Handlers ──────────────────────────────────
  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) { setPdfFile(file); setMatchedJobs([]); setParsedResume(null); }
  };

  const handleDrop = (e) => {
    e.preventDefault(); setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file && (file.type === 'application/pdf' || file.name.endsWith('.pdf'))) {
      setPdfFile(file); setMatchedJobs([]); setParsedResume(null);
    } else { toast.error('Please upload a PDF file'); }
  };

  const handlePDFMatch = async () => {
    if (!pdfFile) { toast.error('Please upload a PDF resume'); return; }
    setMatching(true);
    try {
      const data = await matchResumeWithPDF(pdfFile, 20);
      setMatchedJobs(data.matched_jobs || []);
      setParsedResume(data.parsed_resume || null);
      setResumePreview(data.resume_preview || '');
      setTotalAnalyzed(data.total_jobs_analyzed || 0);
      toast.success(`Found ${data.matched_jobs?.length || 0} matching jobs out of ${data.total_jobs_analyzed || 0} analyzed!`);
    } catch (err) {
      console.error(err);
      toast.error('AI matching failed. Please try again.');
    }
    setMatching(false);
  };

  const handleTextMatch = async () => {
    if (!resumeText.trim()) { toast.error('Please paste your resume text'); return; }
    setMatching(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'}/api/ai/match-jobs`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume_text: resumeText, limit: 20 }),
      });
      const data = await res.json();
      setMatchedJobs(data.matched_jobs || []);
      toast.success(`Found ${data.matched_jobs?.length || 0} matching jobs!`);
    } catch { toast.error('AI matching failed'); }
    setMatching(false);
  };

  if (authLoading) {
    return (<><Navbar onToggleFilters={() => {}} /><div style={{ textAlign: 'center', padding: 80, color: 'var(--text-muted)' }}>Loading...</div></>);
  }

  return (
    <>
      <Navbar onToggleFilters={() => {}} />
      <main style={{ maxWidth: 1200, margin: '0 auto', padding: 24 }}>
        <div style={{ marginBottom: 32 }}>
          <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 4 }}>Dashboard</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>Manage your job search in one place.</p>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid var(--border-color)', paddingBottom: 0 }}>
          {TABS.map(tab => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
              display: 'flex', alignItems: 'center', gap: 6, padding: '10px 16px', fontSize: 14, fontWeight: 600,
              background: 'none', border: 'none', cursor: 'pointer',
              color: activeTab === tab.id ? 'var(--accent-primary)' : 'var(--text-muted)',
              borderBottom: activeTab === tab.id ? '2px solid var(--accent-primary)' : '2px solid transparent',
              transition: 'all 0.2s', marginBottom: -1,
            }}>
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>

        {/* Saved Tab */}
        {activeTab === 'saved' && (
          <div>
            {!user ? (
              <div style={{ textAlign: 'center', padding: 60 }}><div style={{ fontSize: 48, marginBottom: 16 }}>🔒</div><h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>Sign in required</h3><p style={{ color: 'var(--text-muted)' }}>Please sign in to view your saved jobs.</p></div>
            ) : loading ? (
              <div style={{ color: 'var(--text-muted)', padding: 40, textAlign: 'center' }}>Loading saved jobs...</div>
            ) : savedJobs.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 60 }}><Bookmark size={48} style={{ color: 'var(--text-muted)', marginBottom: 16 }} /><h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>No saved jobs yet</h3><p style={{ color: 'var(--text-muted)' }}>Bookmark jobs from the feed to see them here.</p></div>
            ) : (
              <div className="job-grid">{savedJobs.map((job, i) => (<JobCard key={job.id || i} job={job} index={i} onViewDetails={setSelectedJob} savedJobs={savedJobs.map(j => j.id)} />))}</div>
            )}
          </div>
        )}

        {/* Applied Tab */}
        {activeTab === 'applied' && (
          <div>
            {!user ? (
              <div style={{ textAlign: 'center', padding: 60 }}><div style={{ fontSize: 48, marginBottom: 16 }}>🔒</div><h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>Sign in required</h3><p style={{ color: 'var(--text-muted)' }}>Please sign in to view your applications.</p></div>
            ) : applications.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 60 }}><Briefcase size={48} style={{ color: 'var(--text-muted)', marginBottom: 16 }} /><h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>No applications tracked</h3><p style={{ color: 'var(--text-muted)' }}>Applications you track will appear here.</p></div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {applications.map((app) => (
                  <div key={app.id} className="card" style={{ padding: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div><div style={{ fontWeight: 600 }}>{app.jobs?.title}</div><div style={{ fontSize: 13, color: 'var(--text-muted)' }}>{app.jobs?.company_name}</div></div>
                    <span className={`badge ${app.status === 'offered' ? 'badge-success' : app.status === 'rejected' ? 'badge-error' : 'badge-primary'}`}>{app.status}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Alerts Tab */}
        {activeTab === 'alerts' && (
          <div>
            {!user ? (
              <div style={{ textAlign: 'center', padding: 60 }}><div style={{ fontSize: 48, marginBottom: 16 }}>🔒</div><h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>Sign in required</h3><p style={{ color: 'var(--text-muted)' }}>Please sign in to view your job alerts.</p></div>
            ) : alerts.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 60 }}><Bell size={48} style={{ color: 'var(--text-muted)', marginBottom: 16 }} /><h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>No alerts set up</h3><p style={{ color: 'var(--text-muted)' }}>Create alerts to get notified about new matching jobs.</p></div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {alerts.map((alert) => (
                  <div key={alert.id} className="card" style={{ padding: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div><div style={{ fontWeight: 600 }}>{alert.name}</div><div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{alert.frequency} • {alert.is_active ? '🟢 Active' : '⏸️ Paused'}</div></div>
                    <button className="btn btn-ghost" onClick={async () => { await supabase.from('job_alerts').delete().eq('id', alert.id); setAlerts(prev => prev.filter(a => a.id !== alert.id)); toast.success('Alert deleted'); }} style={{ color: 'var(--error)', fontSize: 13 }}>Delete</button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* AI Matching Tab */}
        {activeTab === 'resume' && (
          <div>
            {/* Mode Toggle */}
            <div style={{ display: 'flex', gap: 4, marginBottom: 20, background: 'var(--bg-elevated)', borderRadius: 12, padding: 4, width: 'fit-content' }}>
              <button onClick={() => setMatchMode('pdf')} style={{
                padding: '8px 20px', borderRadius: 10, fontSize: 13, fontWeight: 600, border: 'none', cursor: 'pointer',
                background: matchMode === 'pdf' ? 'var(--accent-primary)' : 'transparent',
                color: matchMode === 'pdf' ? '#fff' : 'var(--text-muted)',
              }}>📄 Upload PDF</button>
              <button onClick={() => setMatchMode('text')} style={{
                padding: '8px 20px', borderRadius: 10, fontSize: 13, fontWeight: 600, border: 'none', cursor: 'pointer',
                background: matchMode === 'text' ? 'var(--accent-primary)' : 'transparent',
                color: matchMode === 'text' ? '#fff' : 'var(--text-muted)',
              }}>📝 Paste Text</button>
            </div>

            {/* PDF Upload Mode */}
            {matchMode === 'pdf' && (
              <div className="card" style={{ padding: 24, marginBottom: 24, background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.05), rgba(6, 182, 212, 0.05))' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                  <Sparkles size={18} style={{ color: 'var(--accent-primary)' }} />
                  <h3 style={{ fontSize: 16, fontWeight: 700 }}>AI Job Matching — PDF Resume</h3>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>
                  Upload your resume PDF and our AI (Groq + OpenRouter) will analyze it against all active jobs and find the best matches.
                </p>

                {/* Drag & Drop Zone */}
                <div
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  style={{
                    border: `2px dashed ${dragOver ? 'var(--accent-primary)' : 'var(--border-color)'}`,
                    borderRadius: 16, padding: 40, textAlign: 'center', cursor: 'pointer',
                    background: dragOver ? 'rgba(124, 58, 237, 0.08)' : 'var(--bg-elevated)',
                    transition: 'all 0.3s', marginBottom: 16,
                  }}
                >
                  <input ref={fileInputRef} type="file" accept=".pdf" onChange={handleFileSelect} style={{ display: 'none' }} />
                  {pdfFile ? (
                    <div>
                      <div style={{ fontSize: 40, marginBottom: 8 }}>📄</div>
                      <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--success)' }}>{pdfFile.name}</div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>{(pdfFile.size / 1024).toFixed(1)} KB</div>
                      <button onClick={(e) => { e.stopPropagation(); setPdfFile(null); setMatchedJobs([]); setParsedResume(null); }}
                        className="btn btn-ghost" style={{ marginTop: 8, fontSize: 12, color: 'var(--error)' }}>
                        <X size={14} /> Remove
                      </button>
                    </div>
                  ) : (
                    <div>
                      <Upload size={40} style={{ color: 'var(--text-muted)', marginBottom: 8 }} />
                      <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 4 }}>Drop your resume PDF here</div>
                      <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>or click to browse</div>
                    </div>
                  )}
                </div>

                <button className="btn btn-primary" onClick={handlePDFMatch} disabled={matching || !pdfFile}
                  style={{ width: '100%', padding: '14px 24px', fontSize: 15, borderRadius: 12 }}>
                  {matching ? (
                    <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span className="animate-float">🤖</span> Analyzing with AI...
                    </span>
                  ) : '🔍 Find Matching Jobs with AI'}
                </button>
              </div>
            )}

            {/* Text Paste Mode */}
            {matchMode === 'text' && (
              <div className="card" style={{ padding: 24, marginBottom: 24, background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.05), rgba(6, 182, 212, 0.05))' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                  <Sparkles size={18} style={{ color: 'var(--accent-primary)' }} />
                  <h3 style={{ fontSize: 16, fontWeight: 700 }}>AI Job Matching — Text</h3>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>
                  Paste your resume below and our AI will find the top 20 jobs that match your skills and experience.
                </p>
                <textarea value={resumeText} onChange={(e) => setResumeText(e.target.value)}
                  placeholder="Paste your resume text here..." className="input"
                  style={{ minHeight: 200, resize: 'vertical', marginBottom: 12, fontFamily: 'inherit' }} />
                <button className="btn btn-primary" onClick={handleTextMatch} disabled={matching} style={{ width: '100%' }}>
                  {matching ? 'Finding matches...' : '🔍 Find Matching Jobs'}
                </button>
              </div>
            )}

            {/* Parsed Resume Preview */}
            {parsedResume && Object.keys(parsedResume).length > 0 && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                className="card" style={{ padding: 20, marginBottom: 24 }}>
                <h4 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <FileText size={16} style={{ color: 'var(--accent-primary)' }} /> Parsed Resume Profile
                </h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, fontSize: 13 }}>
                  {parsedResume.name && <div><span style={{ color: 'var(--text-muted)' }}>Name:</span> <strong>{parsedResume.name}</strong></div>}
                  {parsedResume.experience_years > 0 && <div><span style={{ color: 'var(--text-muted)' }}>Experience:</span> <strong>{parsedResume.experience_years} years</strong></div>}
                  {parsedResume.experience_level && <div><span style={{ color: 'var(--text-muted)' }}>Level:</span> <strong>{parsedResume.experience_level}</strong></div>}
                  {parsedResume.email && <div><span style={{ color: 'var(--text-muted)' }}>Email:</span> <strong>{parsedResume.email}</strong></div>}
                </div>
                {parsedResume.skills?.length > 0 && (
                  <div style={{ marginTop: 12 }}>
                    <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Skills:</span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 4 }}>
                      {parsedResume.skills.map((s, i) => (
                        <span key={i} style={{ padding: '2px 8px', borderRadius: 6, fontSize: 11, background: 'rgba(124, 58, 237, 0.1)', color: '#a78bfa', border: '1px solid rgba(124, 58, 237, 0.2)' }}>{s}</span>
                      ))}
                    </div>
                  </div>
                )}
                {resumePreview && (
                  <div style={{ marginTop: 12, padding: 12, background: 'var(--bg-elevated)', borderRadius: 8, fontSize: 12, color: 'var(--text-muted)', maxHeight: 100, overflow: 'auto' }}>
                    {resumePreview.slice(0, 500)}...
                  </div>
                )}
              </motion.div>
            )}

            {/* Match Results */}
            {matchedJobs.length > 0 && (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 700 }}>
                    🎯 Top {matchedJobs.length} Matches {totalAnalyzed > 0 && <span style={{ fontSize: 13, fontWeight: 400, color: 'var(--text-muted)' }}>(from {totalAnalyzed} jobs)</span>}
                  </h3>
                </div>
                <div className="job-grid">
                  {matchedJobs.map((job, i) => (
                    <div key={job.id || i} style={{ position: 'relative' }}>
                      {/* Match Score Overlay */}
                      {job.match_score > 0 && (
                        <div style={{
                          position: 'absolute', top: 12, right: 12, zIndex: 5,
                          padding: '4px 10px', borderRadius: 10, fontSize: 13, fontWeight: 800,
                          background: job.match_score >= 80 ? 'rgba(16, 185, 129, 0.2)' : job.match_score >= 60 ? 'rgba(245, 158, 11, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                          color: job.match_score >= 80 ? '#34d399' : job.match_score >= 60 ? '#fbbf24' : '#f87171',
                          border: `1px solid ${job.match_score >= 80 ? 'rgba(16, 185, 129, 0.3)' : job.match_score >= 60 ? 'rgba(245, 158, 11, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                        }}>
                          {job.match_score}% match
                        </div>
                      )}
                      <JobCard job={job} index={i} onViewDetails={(j) => setSelectedJob({ ...j, _match_info: { score: j.match_score, reasoning: j.match_reasoning, matching: j.matching_skills, missing: j.missing_skills } })} />
                      {/* Match Details */}
                      {job.match_reasoning && (
                        <div style={{ padding: '8px 16px', borderTop: '1px solid var(--border-color)', fontSize: 12, color: 'var(--text-muted)', background: 'var(--bg-surface)', borderRadius: '0 0 16px 16px', marginTop: -16 }}>
                          <div style={{ marginBottom: 4 }}>{job.match_reasoning}</div>
                          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                            {(job.matching_skills || []).map((s, si) => (
                              <span key={si} style={{ display: 'inline-flex', alignItems: 'center', gap: 2, fontSize: 11, color: '#34d399' }}>
                                <CheckCircle size={10} /> {s}
                              </span>
                            ))}
                            {(job.missing_skills || []).map((s, si) => (
                              <span key={si} style={{ display: 'inline-flex', alignItems: 'center', gap: 2, fontSize: 11, color: '#f87171' }}>
                                <AlertCircle size={10} /> {s}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
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
