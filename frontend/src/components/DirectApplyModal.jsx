'use client';
import { motion, AnimatePresence } from 'framer-motion';
import { X, CheckCircle2, Loader2, AlertTriangle, ExternalLink, Zap, Eye, UserCircle, Send, Shield, ArrowRight } from 'lucide-react';
import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '@/context/AuthContext';
import { getApplyForm, submitDirectApply, getApplyProfile } from '@/lib/api';
import { getInitials } from '@/lib/utils';
import toast from 'react-hot-toast';

/**
 * DirectApplyModal — API-Only Flow
 *
 * Supported ATS (Greenhouse, Lever):
 *   → Submits via official ATS APIs with real-time step tracking
 *   → Uses profile data from the database
 *
 * Unsupported / Aggregator jobs:
 *   → Shows "Apply Externally" with the direct link
 *   → No browser automation — clean, honest UX
 */

const SUPPORTED_ATS = ['greenhouse', 'lever'];
const STEP_COLORS = { completed: '#10b981', in_progress: '#7c3aed', error: '#ef4444', pending: '#64748b', waiting: '#f59e0b' };

export default function DirectApplyModal({ job, onClose }) {
  const { user } = useAuth();
  const [phase, setPhase] = useState('loading'); // loading | ready | applying | success | error | unsupported
  const [steps, setSteps] = useState([]);
  const [result, setResult] = useState(null);
  const [providerName, setProviderName] = useState('');
  const [profileData, setProfileData] = useState(null);
  const [isSupported, setIsSupported] = useState(false);
  const [profileIncomplete, setProfileIncomplete] = useState(false);
  const stepsEndRef = useRef(null);

  const detectedAts = (job?.direct_apply_ats || '').toLowerCase();
  const isAggregator = job?.apply_url?.toLowerCase().includes('adzuna') || 
                        job?.apply_url?.toLowerCase().includes('indeed.com/rc') ||
                        job?.apply_url?.toLowerCase().includes('jooble');

  // Auto-scroll steps panel
  useEffect(() => {
    stepsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [steps]);

  const addStep = useCallback((label, detail, status = 'in_progress') => {
    setSteps(prev => {
      const existing = prev.findIndex(s => s.label === label);
      if (existing >= 0) {
        const updated = [...prev];
        updated[existing] = { ...updated[existing], detail, status };
        return updated;
      }
      return [...prev, { label, detail, status }];
    });
  }, []);

  // Load profile on mount
  useEffect(() => {
    if (!job?.id) return;
    (async () => {
      try {
        // Check if ATS is supported
        const atsSupported = SUPPORTED_ATS.some(ats => detectedAts.includes(ats));
        setIsSupported(atsSupported);

        const formData = await getApplyForm(job.id);
        setProviderName(formData.provider_name || detectedAts || 'Unknown');

        let savedProfile = {};
        try {
          const profileRes = await getApplyProfile();
          if (profileRes.success && profileRes.profile) savedProfile = profileRes.profile;
        } catch (e) {
          console.warn('[DirectApply] Profile fetch error:', e);
        }

        const profile = {
          full_name: savedProfile.full_name || formData.prefill?.name || user?.user_metadata?.full_name || '',
          email: savedProfile.email || formData.prefill?.email || user?.email || '',
          phone: savedProfile.phone || formData.prefill?.phone || '',
          linkedin_url: savedProfile.linkedin_url || formData.prefill?.linkedin_url || '',
          portfolio_url: savedProfile.portfolio_url || formData.prefill?.portfolio_url || '',
          cover_letter: savedProfile.cover_letter_default || formData.prefill?.cover_letter || '',
          resume_url: savedProfile.resume_url || formData.prefill?.resume_url || '',
          resume_filename: savedProfile.resume_filename || formData.prefill?.resume_filename || '',
          location: savedProfile.location || formData.prefill?.location || '',
          current_company: savedProfile.current_company || formData.prefill?.org || '',
        };

        setProfileData(profile);
        if (!profile.full_name || !profile.email) setProfileIncomplete(true);
        setSteps([{ label: 'Profile loaded', detail: profile.email || 'No email — update profile', status: profile.email ? 'completed' : 'error' }]);
        setPhase(atsSupported ? 'ready' : 'unsupported');
      } catch {
        setProfileData({
          full_name: user?.user_metadata?.full_name || '', email: user?.email || '',
          phone: '', linkedin_url: '', portfolio_url: '', cover_letter: '',
          resume_url: '', resume_filename: '', location: '', current_company: '',
        });
        if (!user?.user_metadata?.full_name) setProfileIncomplete(true);
        setPhase(SUPPORTED_ATS.some(ats => detectedAts.includes(ats)) ? 'ready' : 'unsupported');
      }
    })();
  }, [job?.id]);

  // ─── Submit via ATS API ────────────────────────────────────
  const submitViaApi = async () => {
    if (!user) { toast.error('Sign in to apply'); return; }
    if (!profileData?.email || !profileData?.full_name) {
      toast.error('Complete your profile first (Dashboard → Profile tab)');
      return;
    }

    setPhase('applying');
    const pData = profileData;

    addStep('Preparing application', `${pData.full_name} • ${pData.email}`, 'in_progress');
    await new Promise(r => setTimeout(r, 600));
    addStep('Preparing application', `${pData.full_name} • ${pData.email}`, 'completed');

    if (pData.resume_url) {
      addStep('Resume attached', pData.resume_filename || 'resume.pdf', 'completed');
    }

    const provider = providerName || detectedAts;
    addStep(`Submitting to ${provider}`, 'Sending via official ATS API...', 'in_progress');

    try {
      const fd = new FormData();
      fd.append('full_name', pData.full_name || '');
      fd.append('email', pData.email || '');
      if (pData.phone) fd.append('phone', pData.phone);
      if (pData.linkedin_url) fd.append('linkedin_url', pData.linkedin_url);
      if (pData.portfolio_url) fd.append('portfolio_url', pData.portfolio_url);
      if (pData.current_company) fd.append('current_company', pData.current_company);
      if (pData.cover_letter) fd.append('cover_letter', pData.cover_letter);
      if (pData.resume_url) {
        fd.append('resume_url', pData.resume_url);
        fd.append('resume_filename', pData.resume_filename || 'resume.pdf');
      }
      if (pData.location) fd.append('location', pData.location);

      const res = await submitDirectApply(job.id, fd);
      setResult(res);

      if (res.success) {
        addStep(`Submitting to ${provider}`, 'Application submitted!', 'completed');
        addStep('Confirmed', res.message || `Submitted to ${provider}`, 'completed');
        setPhase('success');
        toast.success('Application submitted!');
      } else {
        addStep(`Submitting to ${provider}`, res.message || 'Submission failed', 'error');
        setResult(res);
        setPhase('error');
        toast.error(res.message || 'Submission failed');
      }
    } catch (err) {
      addStep(`Submitting to ${provider}`, err.message, 'error');
      setResult({ success: false, message: err.message });
      setPhase('error');
      toast.error('Submission failed');
    }
  };

  if (!job) return null;
  const cn = job.company_name || 'Unknown';

  return (
    <AnimatePresence>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        onClick={onClose} className="da-overlay">
        <motion.div initial={{ opacity: 0, scale: 0.94, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.94, y: 20 }} transition={{ type: 'spring', damping: 28, stiffness: 350 }}
          onClick={e => e.stopPropagation()} className="da-container"
          style={{ maxWidth: isSupported ? 720 : 520, height: 'auto', maxHeight: '85vh' }}>

          {/* Header */}
          <div className="da-header">
            <div className="da-header-logo">
              {job.company_logo_url ? <img src={job.company_logo_url} alt="" /> : <span>{getInitials(cn)}</span>}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div className="da-header-title">{job.title}</div>
              <div className="da-header-sub">
                <span>{cn}</span>
                {isSupported && <span className="da-ats-badge" style={{ background: 'rgba(16,185,129,0.15)', color: '#10b981', borderColor: 'rgba(16,185,129,0.3)' }}>✓ {providerName || detectedAts} API</span>}
                {!isSupported && detectedAts && <span className="da-ats-badge">{detectedAts}</span>}
                {isAggregator && <span className="da-ats-badge" style={{ background: 'rgba(245,158,11,0.15)', color: '#f59e0b' }}>🔗 Aggregator</span>}
              </div>
            </div>
            <button onClick={onClose} className="btn btn-ghost" style={{ padding: 4 }}><X size={18} /></button>
          </div>

          {/* Body */}
          <div style={{ display: 'flex', overflow: 'hidden', flex: 1, minHeight: 0 }}>

            {/* ─── UNSUPPORTED ATS — External Apply ─────────── */}
            {phase === 'unsupported' && (
              <div style={{ flex: 1, padding: 32, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', gap: 16 }}>
                <div style={{
                  width: 72, height: 72, borderRadius: 18,
                  background: 'linear-gradient(135deg, rgba(245,158,11,0.12), rgba(249,115,22,0.12))',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  border: '1px solid rgba(245,158,11,0.25)',
                }}>
                  <ExternalLink size={32} style={{ color: '#f59e0b' }} />
                </div>
                <h3 style={{ fontSize: 17, fontWeight: 800, color: 'var(--text-primary)' }}>Apply Externally</h3>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', maxWidth: 380, lineHeight: 1.7 }}>
                  This job uses <strong>{detectedAts || 'an unsupported platform'}</strong>
                  {isAggregator ? ' (via an aggregator)' : ''} which doesn't support API-based applications.
                  Click below to apply directly on the company's career page.
                </p>
                <button className="da-auto-apply-btn-large" onClick={() => window.open(job.apply_url, '_blank')}
                  style={{ background: 'linear-gradient(135deg, #f59e0b, #f97316)', maxWidth: 300, marginTop: 8 }}>
                  <ExternalLink size={15} /> Open Application Page
                </button>
                <p style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>
                  Only Greenhouse & Lever support in-app apply via their official APIs.
                </p>
              </div>
            )}

            {/* ─── LOADING ─────────────────────────────────── */}
            {phase === 'loading' && (
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 40, gap: 12 }}>
                <Loader2 size={28} className="spin-icon" style={{ color: 'var(--accent-primary)' }} />
                <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>Loading profile & checking ATS support...</p>
              </div>
            )}

            {/* ─── SUPPORTED ATS — Ready / Applying / Done ── */}
            {isSupported && phase !== 'loading' && phase !== 'unsupported' && (
              <>
                {/* Left: Info / Status Panel */}
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: 28 }}>

                  {phase === 'ready' && (
                    <div style={{ textAlign: 'center' }}>
                      <div style={{
                        width: 72, height: 72, borderRadius: 18, margin: '0 auto 16px',
                        background: 'linear-gradient(135deg, rgba(124,58,237,0.12), rgba(6,182,212,0.12))',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        border: '1px solid rgba(124,58,237,0.2)',
                      }}>
                        <Send size={30} style={{ color: '#7c3aed' }} />
                      </div>
                      <h3 style={{ fontSize: 17, fontWeight: 800, marginBottom: 6, color: 'var(--text-primary)' }}>
                        Submit via {providerName || detectedAts} API
                      </h3>
                      <p style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.6, marginBottom: 16 }}>
                        Your application will be submitted directly through the official {providerName || detectedAts} API — fast, reliable, and data-synced.
                      </p>

                      <div style={{
                        background: 'var(--bg-elevated)', borderRadius: 12, padding: 16, textAlign: 'left',
                        border: '1px solid var(--border-color)', marginBottom: 16,
                      }}>
                        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 5 }}>
                          <UserCircle size={13} /> Your Profile
                        </div>
                        {[
                          ['Name', profileData?.full_name],
                          ['Email', profileData?.email],
                          ['Phone', profileData?.phone],
                          ['LinkedIn', profileData?.linkedin_url],
                          ['Location', profileData?.location],
                          ['Resume', profileData?.resume_filename],
                        ].filter(([, v]) => v).map(([k, v], i) => (
                          <div key={i} style={{ display: 'flex', gap: 8, fontSize: 12, marginBottom: 4, color: 'var(--text-secondary)' }}>
                            <span style={{ fontWeight: 600, minWidth: 65, color: 'var(--text-muted)' }}>{k}</span>
                            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{v}</span>
                          </div>
                        ))}
                      </div>

                      {profileIncomplete && (
                        <div style={{ padding: '10px 14px', background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: 10, marginBottom: 16 }}>
                          <p style={{ fontSize: 11, color: '#f59e0b', margin: 0, fontWeight: 600 }}>
                            ⚠ Complete your profile (Dashboard → Profile) before applying.
                          </p>
                        </div>
                      )}

                      <button className="da-auto-apply-btn-large" onClick={submitViaApi} disabled={profileIncomplete}>
                        <Zap size={15} /> Submit Application
                      </button>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4, marginTop: 10, fontSize: 10, color: 'var(--text-muted)' }}>
                        <Shield size={10} /> Submitted via official {providerName || detectedAts} API • No browser automation
                      </div>
                    </div>
                  )}

                  {phase === 'applying' && (
                    <div style={{ textAlign: 'center' }}>
                      <div style={{
                        width: 64, height: 64, borderRadius: '50%', margin: '0 auto 16px',
                        background: 'conic-gradient(#7c3aed 0deg, #06b6d4 120deg, #10b981 240deg, #7c3aed 360deg)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        animation: 'spin 3s linear infinite', padding: 3,
                      }}>
                        <div style={{
                          width: '100%', height: '100%', borderRadius: '50%',
                          background: 'var(--bg-surface)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                        }}>
                          <Send size={22} style={{ color: '#7c3aed' }} />
                        </div>
                      </div>
                      <h3 style={{ fontSize: 16, fontWeight: 700, color: '#a78bfa' }}>Submitting...</h3>
                      <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Sending to {providerName} via API</p>
                    </div>
                  )}

                  {phase === 'success' && (
                    <div style={{ textAlign: 'center' }}>
                      <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', damping: 10, stiffness: 200 }} style={{ marginBottom: 16 }}>
                        <CheckCircle2 size={56} style={{ color: '#10b981' }} />
                      </motion.div>
                      <h3 style={{ fontSize: 18, fontWeight: 800, color: '#10b981', marginBottom: 6 }}>Application Submitted!</h3>
                      <p style={{ fontSize: 13, color: 'var(--text-muted)', maxWidth: 350, margin: '0 auto', lineHeight: 1.6 }}>
                        {result?.message || `Submitted to ${providerName} via official API.`}
                      </p>
                    </div>
                  )}

                  {phase === 'error' && (
                    <div style={{ textAlign: 'center' }}>
                      <AlertTriangle size={48} style={{ color: '#ef4444', marginBottom: 12 }} />
                      <h3 style={{ fontSize: 16, fontWeight: 700, color: '#ef4444', marginBottom: 6 }}>Submission Failed</h3>
                      <p style={{ fontSize: 13, color: 'var(--text-muted)', maxWidth: 350, margin: '0 auto 16px' }}>
                        {result?.message || 'Something went wrong.'}
                      </p>
                      <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
                        <button className="btn btn-secondary" onClick={() => { setPhase('ready'); setSteps(s => s.filter(x => x.label === 'Profile loaded')); }}
                          style={{ fontSize: 12, padding: '8px 16px', borderRadius: 8 }}>Retry</button>
                        <button className="btn btn-secondary" onClick={() => window.open(job.apply_url, '_blank')}
                          style={{ fontSize: 12, padding: '8px 16px', borderRadius: 8 }}>
                          <ExternalLink size={12} /> Apply Manually
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Right: Progress Panel */}
                <div className="da-progress-panel" style={{ width: 260 }}>
                  <div className="da-progress-title">
                    <Eye size={14} /> Submission Progress
                  </div>

                  <div className="da-steps-list">
                    {steps.map((s, i) => (
                      <motion.div key={`${s.label}-${i}`} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.04 }}
                        className="da-step" style={{ borderLeftColor: STEP_COLORS[s.status] || '#64748b' }}>
                        <span className="da-step-icon" style={{ color: STEP_COLORS[s.status] }}>
                          {s.status === 'completed' && <CheckCircle2 size={13} />}
                          {s.status === 'in_progress' && <Loader2 size={13} className="spin-icon" />}
                          {s.status === 'error' && <AlertTriangle size={13} />}
                          {s.status === 'waiting' && <span style={{ width: 13, height: 13, borderRadius: '50%', border: '2px solid #f59e0b', display: 'inline-block' }} />}
                        </span>
                        <div style={{ flex: 1 }}>
                          <div className="da-step-label" style={{ color: STEP_COLORS[s.status] }}>{s.label}</div>
                          {s.detail && <div className="da-step-detail">{s.detail}</div>}
                        </div>
                      </motion.div>
                    ))}
                    <div ref={stepsEndRef} />
                  </div>

                  <div className="da-progress-footer">
                    <Shield size={10} /> Official {providerName} API • Real-time sync
                  </div>
                </div>
              </>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
