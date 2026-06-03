'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/context/AuthContext';
import Navbar from '@/components/Navbar';
import JobCard from '@/components/JobCard';
import JobDetailPanel from '@/components/JobDetailPanel';
import { supabase } from '@/lib/supabase';
import { matchResumeWithPDF, matchJobsWithKeywords } from '@/lib/api';
import { Bookmark, Briefcase, Bell, FileText, Upload, Sparkles, X, CheckCircle, AlertCircle, Search, Star, User, Save, Phone, Link, MapPin, Building } from 'lucide-react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

const TABS = [
  { id: 'saved', label: 'Saved Jobs', icon: <Bookmark size={16} /> },
  { id: 'applied', label: 'Applications', icon: <Briefcase size={16} /> },
  { id: 'profile', label: 'Profile', icon: <User size={16} /> },
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
  const [keywords, setKeywords] = useState('');
  const [aiRecommendation, setAiRecommendation] = useState('');
  const [matching, setMatching] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [matchMode, setMatchMode] = useState('keywords'); // 'keywords', 'pdf' or 'text'
  const [totalAnalyzed, setTotalAnalyzed] = useState(0);
  const fileInputRef = useRef(null);

  // Profile state
  const [profileForm, setProfileForm] = useState({
    full_name: '', phone: '', linkedin_url: '', portfolio_url: '',
    location: '', current_company: '', cover_letter_default: '',
  });
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileLoaded, setProfileLoaded] = useState(false);
  const [resumeFile, setResumeFile] = useState(null);
  const resumeInputRef = useRef(null);

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
      } else if (activeTab === 'profile' && !profileLoaded) {
        try {
          const { getApplyProfile } = await import('@/lib/api');
          const res = await getApplyProfile();
          if (res.success && res.profile) {
            setProfileForm({
              full_name: res.profile.full_name || user?.user_metadata?.full_name || '',
              phone: res.profile.phone || '',
              linkedin_url: res.profile.linkedin_url || '',
              portfolio_url: res.profile.portfolio_url || '',
              location: res.profile.location || '',
              current_company: res.profile.current_company || '',
              cover_letter_default: res.profile.cover_letter_default || '',
            });
          } else {
            setProfileForm(prev => ({ ...prev, full_name: user?.user_metadata?.full_name || '' }));
          }
          setProfileLoaded(true);
        } catch (e) {
          console.warn('Profile load error:', e);
          setProfileForm(prev => ({ ...prev, full_name: user?.user_metadata?.full_name || '' }));
          setProfileLoaded(true);
        }
      }
    } catch (err) { console.error(err); }
    setLoading(false);
  };

  const handleProfileSave = async () => {
    setProfileSaving(true);
    try {
      const { updateApplyProfile } = await import('@/lib/api');
      const res = await updateApplyProfile(profileForm);
      if (res.success) {
        toast.success('Profile saved successfully!');
      } else {
        toast.error(res.error || 'Failed to save profile');
      }
    } catch (e) {
      toast.error('Failed to save profile');
    }
    setProfileSaving(false);
  };

  const handleResumeUpload = async () => {
    if (!resumeFile) return;
    try {
      const { uploadResume } = await import('@/lib/api');
      const res = await uploadResume(resumeFile);
      if (res.success) {
        toast.success(`Resume uploaded: ${res.file_name}`);
        setResumeFile(null);
      } else {
        toast.error(res.error || 'Upload failed');
      }
    } catch (e) {
      toast.error('Resume upload failed');
    }
  };

  // ─── PDF Upload Handlers ──────────────────────────────────
  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) { setPdfFile(file); setMatchedJobs([]); setParsedResume(null); setAiRecommendation(''); }
  };

  const handleDrop = (e) => {
    e.preventDefault(); setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file && (file.type === 'application/pdf' || file.name.endsWith('.pdf'))) {
      setPdfFile(file); setMatchedJobs([]); setParsedResume(null); setAiRecommendation('');
    } else { toast.error('Please upload a PDF file'); }
  };

  const handlePDFMatch = async () => {
    if (!pdfFile) { toast.error('Please upload a PDF resume'); return; }
    setMatching(true);
    try {
      const data = await matchResumeWithPDF(pdfFile, 20);
      if (data.error) {
        toast.error(data.error);
        setMatchedJobs([]);
      } else {
        setMatchedJobs(data.matched_jobs || []);
        setParsedResume(data.parsed_resume || null);
        setResumePreview(data.resume_preview || '');
        setTotalAnalyzed(data.total_jobs_analyzed || 0);
        if ((data.matched_jobs || []).length > 0) {
          toast.success(`Found ${data.matched_jobs.length} matching jobs out of ${data.total_jobs_analyzed || 0} analyzed!`);
        } else {
          toast.error('No matching jobs found. Try a different resume or check back later.');
        }
      }
    } catch (err) {
      console.error('AI match error:', err);
      toast.error('AI matching failed. Make sure the backend server is running.');
    }
    setMatching(false);
  };

  const handleTextMatch = async () => {
    if (!resumeText.trim()) { toast.error('Please paste your resume text'); return; }
    setMatching(true);
    setAiRecommendation('');
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

  const handleKeywordMatch = async () => {
    if (!keywords.trim()) { toast.error('Please enter some keywords'); return; }
    setMatching(true);
    setParsedResume(null);
    setAiRecommendation('');
    try {
      const keywordList = keywords.split(',').map(k => k.trim()).filter(Boolean);
      const data = await matchJobsWithKeywords({ keywords: keywordList, limit: 30 });
      if (data.error) {
        toast.error(data.error);
        setMatchedJobs([]);
      } else {
        setMatchedJobs(data.matched_jobs || []);
        setTotalAnalyzed(data.total_analyzed || 0);
        setAiRecommendation(data.ai_recommendation || '');
        toast.success(`Found ${data.matched_jobs?.length || 0} matching jobs!`);
      }
    } catch (err) {
      console.error(err);
      toast.error('AI matching failed');
    }
    setMatching(false);
  };

  if (authLoading) {
    return (<><Navbar onToggleFilters={() => {}} hideFilters /><div style={{ textAlign: 'center', padding: 80, color: 'var(--text-muted)' }}>Loading...</div></>);
  }

  return (
    <>
      <Navbar onToggleFilters={() => {}} hideFilters />
      <main style={{ maxWidth: 1200, margin: '0 auto', padding: 24 }}>
        <div style={{ marginBottom: 32 }}>
          <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 4 }}>Dashboard</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>Manage your job search in one place.</p>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid var(--border-color)', paddingBottom: 0, overflowX: 'auto', WebkitOverflowScrolling: 'touch', scrollbarWidth: 'none' }}>
          {TABS.map(tab => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
              display: 'flex', alignItems: 'center', gap: 6, padding: '10px 16px', fontSize: 14, fontWeight: 600,
              background: 'none', border: 'none', cursor: 'pointer', whiteSpace: 'nowrap', flexShrink: 0,
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
            ) : loading ? (
              <div style={{ color: 'var(--text-muted)', padding: 40, textAlign: 'center' }}>Loading applications...</div>
            ) : applications.filter(a => a.status && a.status !== 'failed').length === 0 ? (
              <div style={{ textAlign: 'center', padding: 60 }}><Briefcase size={48} style={{ color: 'var(--text-muted)', marginBottom: 16 }} /><h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>No successful applications yet</h3><p style={{ color: 'var(--text-muted)' }}>When you auto-apply to jobs, confirmed submissions will appear here.</p></div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {applications.filter(a => a.status && a.status !== 'failed').map((app) => (
                  <div key={app.id} className="card" style={{ padding: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 600 }}>{app.jobs?.title || 'Unknown Position'}</div>
                      <div style={{ fontSize: 13, color: 'var(--text-muted)', display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 2 }}>
                        <span>{app.jobs?.company_name || 'Unknown'}</span>
                        {app.apply_method && <span style={{ fontSize: 11, padding: '1px 6px', borderRadius: 4, background: 'rgba(124,58,237,0.1)', color: '#a78bfa' }}>{app.apply_method.replace('direct_', '⚡ ')}</span>}
                        {app.applied_at && <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{new Date(app.applied_at).toLocaleDateString()}</span>}
                      </div>
                    </div>
                    <span className={`badge ${app.status === 'offered' ? 'badge-success' : app.status === 'rejected' ? 'badge-error' : app.status === 'applied' ? 'badge-primary' : 'badge-secondary'}`}>{app.status}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Profile Tab */}
        {activeTab === 'profile' && (
          <div>
            {!user ? (
              <div style={{ textAlign: 'center', padding: 60 }}><div style={{ fontSize: 48, marginBottom: 16 }}>🔒</div><h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>Sign in required</h3><p style={{ color: 'var(--text-muted)' }}>Please sign in to manage your profile.</p></div>
            ) : (
              <div style={{ maxWidth: 700 }}>
                <div className="card" style={{ padding: 28, marginBottom: 24, background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.05), rgba(16, 185, 129, 0.05))' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
                    <div style={{ width: 48, height: 48, borderRadius: '50%', background: 'var(--gradient-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20, fontWeight: 700, color: '#fff' }}>
                      {(profileForm.full_name || user.email)?.[0]?.toUpperCase() || 'U'}
                    </div>
                    <div>
                      <h3 style={{ fontSize: 18, fontWeight: 800, marginBottom: 2 }}>Auto-Apply Profile</h3>
                      <p style={{ fontSize: 13, color: 'var(--text-muted)', margin: 0 }}>This data auto-fills and submits your applications hands-off when you click "Quick Apply" on any supported job (Lever, Greenhouse).</p>
                    </div>
                  </div>

                  {/* Email (read-only) */}
                  <div style={{ marginBottom: 18 }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 600, marginBottom: 6, color: 'var(--text-secondary)' }}>📧 Email (from your account)</label>
                    <input type="email" value={user.email || ''} disabled className="input" style={{ opacity: 0.6 }} />
                  </div>

                  {/* Full Name */}
                  <div style={{ marginBottom: 18 }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 600, marginBottom: 6, color: 'var(--text-secondary)' }}><User size={14} /> Full Name *</label>
                    <input type="text" value={profileForm.full_name} onChange={e => setProfileForm(p => ({ ...p, full_name: e.target.value }))} className="input" placeholder="Your full name" />
                  </div>

                  {/* Phone + LinkedIn in a row */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 18 }}>
                    <div>
                      <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 600, marginBottom: 6, color: 'var(--text-secondary)' }}><Phone size={14} /> Phone</label>
                      <input type="tel" value={profileForm.phone} onChange={e => setProfileForm(p => ({ ...p, phone: e.target.value }))} className="input" placeholder="e.g. 9876543210" />
                    </div>
                    <div>
                      <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 600, marginBottom: 6, color: 'var(--text-secondary)' }}><Link size={14} /> LinkedIn URL</label>
                      <input type="url" value={profileForm.linkedin_url} onChange={e => setProfileForm(p => ({ ...p, linkedin_url: e.target.value }))} className="input" placeholder="https://linkedin.com/in/..." />
                    </div>
                  </div>

                  {/* Portfolio + Current Company */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 18 }}>
                    <div>
                      <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 600, marginBottom: 6, color: 'var(--text-secondary)' }}>🔗 Portfolio / GitHub</label>
                      <input type="url" value={profileForm.portfolio_url} onChange={e => setProfileForm(p => ({ ...p, portfolio_url: e.target.value }))} className="input" placeholder="https://github.com/..." />
                    </div>
                    <div>
                      <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 600, marginBottom: 6, color: 'var(--text-secondary)' }}><Building size={14} /> Current Company</label>
                      <input type="text" value={profileForm.current_company} onChange={e => setProfileForm(p => ({ ...p, current_company: e.target.value }))} className="input" placeholder="e.g. Google" />
                    </div>
                  </div>

                  {/* Location */}
                  <div style={{ marginBottom: 18 }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 600, marginBottom: 6, color: 'var(--text-secondary)' }}><MapPin size={14} /> Location</label>
                    <input type="text" value={profileForm.location} onChange={e => setProfileForm(p => ({ ...p, location: e.target.value }))} className="input" placeholder="e.g. Chennai, India" />
                  </div>

                  {/* Default Cover Letter */}
                  <div style={{ marginBottom: 18 }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 600, marginBottom: 6, color: 'var(--text-secondary)' }}>📝 Default Cover Letter</label>
                    <textarea value={profileForm.cover_letter_default} onChange={e => setProfileForm(p => ({ ...p, cover_letter_default: e.target.value }))} className="input" placeholder="Write a default cover letter to send with applications..." style={{ minHeight: 100, resize: 'vertical', fontFamily: 'inherit' }} />
                  </div>

                  {/* Resume Upload */}
                  <div style={{ marginBottom: 24 }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 600, marginBottom: 6, color: 'var(--text-secondary)' }}><FileText size={14} /> Resume (PDF)</label>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <input ref={resumeInputRef} type="file" accept=".pdf,.doc,.docx" onChange={e => setResumeFile(e.target.files?.[0] || null)} className="input" style={{ flex: 1 }} />
                      {resumeFile && (
                        <button className="btn btn-secondary" onClick={handleResumeUpload} style={{ padding: '8px 16px', fontSize: 13, borderRadius: 8, whiteSpace: 'nowrap' }}>
                          <Upload size={14} /> Upload
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Save Button */}
                  <button className="btn btn-primary" onClick={handleProfileSave} disabled={profileSaving} style={{ width: '100%', padding: '14px 24px', fontSize: 15, borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                    {profileSaving ? (
                      <><span className="spin-icon" style={{ display: 'inline-block' }}>⏳</span> Saving...</>
                    ) : (
                      <><Save size={16} /> Save Profile</>
                    )}
                  </button>
                </div>
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
              <button onClick={() => setMatchMode('keywords')} style={{
                padding: '8px 20px', borderRadius: 10, fontSize: 13, fontWeight: 600, border: 'none', cursor: 'pointer',
                background: matchMode === 'keywords' ? 'var(--accent-primary)' : 'transparent',
                color: matchMode === 'keywords' ? '#fff' : 'var(--text-muted)',
              }}>⚡ Quick Match</button>
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

            {/* Keywords Match Mode */}
            {matchMode === 'keywords' && (
              <div className="card" style={{ padding: 24, marginBottom: 24, background: 'linear-gradient(135deg, rgba(52, 211, 153, 0.05), rgba(59, 130, 246, 0.05))' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                  <Search size={18} style={{ color: '#34d399' }} />
                  <h3 style={{ fontSize: 16, fontWeight: 700 }}>Quick Match — Keywords</h3>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>
                  Enter skills, titles, or technologies (comma separated) to find and rank the most relevant new jobs.
                </p>
                <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
                  <input 
                    type="text" 
                    value={keywords} 
                    onChange={(e) => setKeywords(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleKeywordMatch()}
                    placeholder="e.g. React, Node.js, Python, Remote..." 
                    className="input"
                    style={{ flex: '1 1 200px', minWidth: 0 }}
                  />
                  <button className="btn btn-primary" onClick={handleKeywordMatch} disabled={matching}
                    style={{ flex: '0 0 auto', width: '100%', maxWidth: 200 }}>
                    {matching ? 'Scoring...' : 'Match Jobs'}
                  </button>
                </div>
              </div>
            )}

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
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12, fontSize: 13 }}>
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

            {/* Match Results — Categorized by Tier */}
            {matchedJobs.length > 0 && (() => {
              const tiers = {
                perfect: { emoji: '🏆', label: 'Perfect Match', color: '#34d399', bg: 'rgba(16, 185, 129, 0.08)', border: 'rgba(16, 185, 129, 0.2)', jobs: [] },
                strong:  { emoji: '🔥', label: 'Strong Match', color: '#fbbf24', bg: 'rgba(245, 158, 11, 0.08)', border: 'rgba(245, 158, 11, 0.2)', jobs: [] },
                good:    { emoji: '👍', label: 'Good Match', color: '#60a5fa', bg: 'rgba(96, 165, 250, 0.08)', border: 'rgba(96, 165, 250, 0.2)', jobs: [] },
                weak:    { emoji: '💡', label: 'Worth Exploring', color: '#a78bfa', bg: 'rgba(167, 139, 250, 0.08)', border: 'rgba(167, 139, 250, 0.2)', jobs: [] },
              };
              matchedJobs.forEach(job => {
                const tier = job.match_tier || (job.match_score >= 80 ? 'perfect' : job.match_score >= 60 ? 'strong' : job.match_score >= 40 ? 'good' : 'weak');
                if (tiers[tier]) tiers[tier].jobs.push(job);
                else tiers.weak.jobs.push(job);
              });

              return (
                <div>
                  {/* Stats & AI Recommendation */}
                  {aiRecommendation && (
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                      className="card" style={{ padding: 16, marginBottom: 24, background: 'rgba(124, 58, 237, 0.05)', border: '1px solid rgba(124, 58, 237, 0.2)' }}>
                      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                        <div style={{ background: 'rgba(124, 58, 237, 0.1)', padding: 8, borderRadius: 8, color: '#a78bfa' }}>
                          <Sparkles size={20} />
                        </div>
                        <div>
                          <h4 style={{ fontSize: 14, fontWeight: 700, marginBottom: 4, color: 'var(--text-primary)' }}>AI Career Advisor</h4>
                          <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                            {aiRecommendation}
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* Stats Bar */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
                    <h3 style={{ fontSize: 18, fontWeight: 800 }}>
                      🎯 AI Match Results
                      {totalAnalyzed > 0 && <span style={{ fontSize: 13, fontWeight: 400, color: 'var(--text-muted)', marginLeft: 8 }}>({totalAnalyzed} jobs analyzed)</span>}
                    </h3>
                    <div style={{ display: 'flex', gap: 8 }}>
                      {Object.entries(tiers).map(([key, tier]) => tier.jobs.length > 0 && (
                        <span key={key} style={{
                          padding: '4px 10px', borderRadius: 20, fontSize: 12, fontWeight: 700,
                          background: tier.bg, color: tier.color, border: `1px solid ${tier.border}`,
                        }}>
                          {tier.emoji} {tier.jobs.length} {tier.label.split(' ')[0]}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Tier Sections */}
                  {Object.entries(tiers).map(([tierKey, tier]) => {
                    if (tier.jobs.length === 0) return null;
                    return (
                      <div key={tierKey} style={{ marginBottom: 32 }}>
                        {/* Tier Header */}
                        <div style={{
                          display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12,
                          padding: '10px 16px', borderRadius: 12,
                          background: tier.bg, border: `1px solid ${tier.border}`,
                        }}>
                          <span style={{ fontSize: 20 }}>{tier.emoji}</span>
                          <span style={{ fontSize: 15, fontWeight: 800, color: tier.color }}>{tier.label}</span>
                          <span style={{ fontSize: 12, color: 'var(--text-muted)', marginLeft: 4 }}>
                            ({tier.jobs.length} {tier.jobs.length === 1 ? 'job' : 'jobs'})
                          </span>
                          {tierKey === 'perfect' && <span style={{ fontSize: 11, color: tier.color, marginLeft: 'auto' }}>90-100% skill match</span>}
                          {tierKey === 'strong' && <span style={{ fontSize: 11, color: tier.color, marginLeft: 'auto' }}>60-89% skill match</span>}
                          {tierKey === 'good' && <span style={{ fontSize: 11, color: tier.color, marginLeft: 'auto' }}>40-59% skill match</span>}
                          {tierKey === 'weak' && <span style={{ fontSize: 11, color: tier.color, marginLeft: 'auto' }}>Partial match</span>}
                        </div>

                        {/* Jobs in this tier */}
                        <div className="job-grid">
                          {tier.jobs.map((job, i) => (
                            <div key={job.id || `${tierKey}-${i}`} style={{ position: 'relative' }}>
                              {/* Score Badge */}
                              <div style={{
                                position: 'absolute', top: 12, right: 12, zIndex: 5,
                                display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4,
                              }}>
                                <div style={{
                                  padding: '4px 10px', borderRadius: 10, fontSize: 13, fontWeight: 800,
                                  background: tier.bg, color: tier.color, border: `1px solid ${tier.border}`,
                                }}>
                                  {job.match_score}%
                                </div>
                                {job.level_match && (
                                  <div style={{
                                    padding: '2px 6px', borderRadius: 6, fontSize: 9, fontWeight: 700,
                                    background: 'rgba(16, 185, 129, 0.15)', color: '#34d399',
                                    border: '1px solid rgba(16, 185, 129, 0.3)',
                                  }}>✓ Level Match</div>
                                )}
                              </div>

                              <JobCard job={job} index={i} onViewDetails={(j) => setSelectedJob({
                                ...j,
                                _match_info: { score: j.match_score, reasoning: j.match_reasoning, matching: j.matching_skills, missing: j.missing_skills, tier: j.match_tier }
                              })} />

                              {/* Match Details Panel */}
                              <div style={{
                                padding: '10px 16px', fontSize: 12,
                                background: tier.bg, borderRadius: '0 0 16px 16px', marginTop: -16,
                                borderTop: `1px solid ${tier.border}`,
                              }}>
                                {job.match_reasoning && (
                                  <div style={{ color: 'var(--text-secondary)', marginBottom: 6 }}>{job.match_reasoning}</div>
                                )}
                                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                                  {/* Quality Rating */}
                                  {job.quality_rating && (
                                    <span style={{
                                      display: 'inline-flex', alignItems: 'center', gap: 3,
                                      padding: '2px 8px', borderRadius: 6, fontSize: 10, fontWeight: 700,
                                      background: 'rgba(251, 191, 36, 0.15)', color: '#f59e0b',
                                      border: '1px solid rgba(251, 191, 36, 0.3)',
                                    }}>
                                      <Star size={10} fill="currentColor" /> {job.quality_rating.stars}/5 Quality
                                    </span>
                                  )}
                                  
                                  {/* New Badge */}
                                  {job.is_new && (
                                    <span style={{
                                      display: 'inline-flex', alignItems: 'center', gap: 3,
                                      padding: '2px 8px', borderRadius: 6, fontSize: 10, fontWeight: 700,
                                      background: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6',
                                      border: '1px solid rgba(59, 130, 246, 0.3)',
                                    }}>
                                      ✨ New
                                    </span>
                                  )}

                                  {(job.matching_skills || []).map((s, si) => (
                                    <span key={`m-${si}`} style={{
                                      display: 'inline-flex', alignItems: 'center', gap: 3,
                                      padding: '2px 8px', borderRadius: 6, fontSize: 10, fontWeight: 600,
                                      background: 'rgba(16, 185, 129, 0.12)', color: '#34d399',
                                      border: '1px solid rgba(16, 185, 129, 0.25)',
                                    }}>
                                      <CheckCircle size={9} /> {s}
                                    </span>
                                  ))}
                                  {(job.matched_keywords || []).map((s, si) => (
                                    <span key={`mk-${si}`} style={{
                                      display: 'inline-flex', alignItems: 'center', gap: 3,
                                      padding: '2px 8px', borderRadius: 6, fontSize: 10, fontWeight: 600,
                                      background: 'rgba(16, 185, 129, 0.12)', color: '#34d399',
                                      border: '1px solid rgba(16, 185, 129, 0.25)',
                                    }}>
                                      <CheckCircle size={9} /> {s}
                                    </span>
                                  ))}
                                  {(job.missing_skills || []).map((s, si) => (
                                    <span key={`x-${si}`} style={{
                                      display: 'inline-flex', alignItems: 'center', gap: 3,
                                      padding: '2px 8px', borderRadius: 6, fontSize: 10, fontWeight: 600,
                                      background: 'rgba(239, 68, 68, 0.1)', color: '#f87171',
                                      border: '1px solid rgba(239, 68, 68, 0.2)',
                                    }}>
                                      <AlertCircle size={9} /> {s}
                                    </span>
                                  ))}
                                  {(job.matching_skills || []).length === 0 && (job.matched_keywords || []).length === 0 && (job.missing_skills || []).length === 0 && !job.quality_rating && (
                                    <span style={{ fontSize: 11, color: 'var(--text-muted)', fontStyle: 'italic' }}>
                                      Skills analysis pending
                                    </span>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              );
            })()}
          </div>
        )}

        {selectedJob && <JobDetailPanel job={selectedJob} onClose={() => setSelectedJob(null)} />}
      </main>
    </>
  );
}
