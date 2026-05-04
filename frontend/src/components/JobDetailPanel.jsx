'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { X, ExternalLink, MapPin, Clock, Building2, DollarSign, Briefcase, Shield, Plane, Sparkles } from 'lucide-react';
import { formatSalary, timeAgo, getInitials, EXPERIENCE_COLORS, SOURCE_ICONS } from '@/lib/utils';
import { useState, useEffect } from 'react';
import { summarizeJob, getSimilarJobs } from '@/lib/api';
import ReactMarkdown from 'react-markdown';
import toast from 'react-hot-toast';

export default function JobDetailPanel({ job, onClose }) {
  const [aiSummary, setAiSummary] = useState('');
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [similar, setSimilar] = useState([]);

  useEffect(() => {
    if (job?.id) {
      getSimilarJobs(job.id).then(d => setSimilar(d.similar_jobs || [])).catch(() => {});
    }
  }, [job?.id]);

  const handleSummarize = async () => {
    if (!job?.id) return;
    setLoadingSummary(true);
    try {
      const data = await summarizeJob(job.id);
      setAiSummary(data.summary || 'Unable to generate summary.');
    } catch {
      setAiSummary('AI summary unavailable.');
    }
    setLoadingSummary(false);
  };

  if (!job) return null;

  return (
    <AnimatePresence>
      <motion.div className="fade-overlay" onClick={onClose}
        style={{ position: 'fixed', inset: 0, zIndex: 60, background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)' }}
      >
        <motion.div className="slide-panel" onClick={(e) => e.stopPropagation()}
          style={{
            position: 'fixed', right: 0, top: 0, bottom: 0, width: 560, maxWidth: '100vw',
            background: 'var(--bg-surface)', borderLeft: '1px solid var(--border-color)',
            display: 'flex', flexDirection: 'column', zIndex: 61,
          }}
        >
          {/* Header */}
          <div style={{
            padding: '20px 24px', borderBottom: '1px solid var(--border-color)',
            display: 'flex', alignItems: 'flex-start', gap: 12,
          }}>
            {job.company_logo_url ? (
              <img src={job.company_logo_url} alt="" style={{ width: 48, height: 48, borderRadius: 10, background: '#fff', padding: 4, objectFit: 'contain' }} />
            ) : (
              <div style={{ width: 48, height: 48, borderRadius: 10, background: 'var(--gradient-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, fontWeight: 700, color: '#fff', flexShrink: 0 }}>
                {getInitials(job.company_name)}
              </div>
            )}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>{job.company_name}</span>
                {job.vc_backer && <span className="badge badge-primary" style={{ fontSize: 10 }}>{job.vc_backer}</span>}
                {job.is_stealth && <span className="badge badge-stealth" style={{ fontSize: 10 }}>🔒 Stealth</span>}
              </div>
              <h2 style={{ fontSize: 20, fontWeight: 700, marginTop: 4 }}>{job.title}</h2>
            </div>
            <button onClick={onClose} className="btn btn-ghost" style={{ padding: 6, flexShrink: 0 }}>
              <X size={20} />
            </button>
          </div>

          {/* Body */}
          <div style={{ flex: 1, overflowY: 'auto', padding: 24 }}>
            {/* Meta Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 24 }}>
              <MetaItem icon={<MapPin size={15} />} label="Location" value={`${job.location_city || ''}${job.location_country ? `, ${job.location_country}` : ''}` || 'Not specified'} />
              <MetaItem icon={<Briefcase size={15} />} label="Type" value={job.job_type || 'Not specified'} />
              <MetaItem icon={<DollarSign size={15} />} label="Salary" value={formatSalary(job.salary_min, job.salary_max, job.salary_currency)} highlight />
              <MetaItem icon={<Building2 size={15} />} label="Experience" value={job.experience_level || 'Not specified'} />
              <MetaItem icon={<Shield size={15} />} label="Visa" value={job.visa_sponsorship ? '✅ Sponsored' : '❌ Not specified'} />
              <MetaItem icon={<Plane size={15} />} label="Relocation" value={job.relocation_support ? '✅ Supported' : '❌ Not specified'} />
            </div>

            {/* Remote Badge */}
            {job.remote_type && (
              <div style={{ marginBottom: 20 }}>
                <span className={`badge ${job.remote_type === 'remote' ? 'badge-success' : 'badge-warning'}`}>
                  {job.remote_type === 'remote' ? '🌍 Remote' : job.remote_type === 'hybrid' ? '🔀 Hybrid' : '📍 Onsite'}
                </span>
              </div>
            )}

            {/* AI Summary */}
            <div style={{ marginBottom: 24, padding: 16, background: 'var(--bg-elevated)', borderRadius: 12, border: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                <span style={{ fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Sparkles size={14} style={{ color: 'var(--accent-primary)' }} /> AI Summary
                </span>
                {!aiSummary && (
                  <button className="btn btn-primary" onClick={handleSummarize} disabled={loadingSummary}
                    style={{ padding: '4px 12px', fontSize: 12, borderRadius: 8 }}>
                    {loadingSummary ? 'Generating...' : 'Generate'}
                  </button>
                )}
              </div>
              {aiSummary ? (
                <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                  <ReactMarkdown>{aiSummary}</ReactMarkdown>
                </div>
              ) : (
                <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                  Click generate to get an AI-powered summary of this job.
                </p>
              )}
            </div>

            {/* Full Description */}
            {job.description && (
              <Section title="Description">
                <div style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                  <ReactMarkdown>{job.description}</ReactMarkdown>
                </div>
              </Section>
            )}

            {/* Requirements */}
            {job.requirements?.length > 0 && (
              <Section title="Requirements">
                <ul style={{ paddingLeft: 20, fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                  {job.requirements.map((r, i) => <li key={i}>{r}</li>)}
                </ul>
              </Section>
            )}

            {/* Responsibilities */}
            {job.responsibilities?.length > 0 && (
              <Section title="Responsibilities">
                <ul style={{ paddingLeft: 20, fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                  {job.responsibilities.map((r, i) => <li key={i}>{r}</li>)}
                </ul>
              </Section>
            )}

            {/* Benefits */}
            {job.benefits?.length > 0 && (
              <Section title="Benefits">
                <ul style={{ paddingLeft: 20, fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                  {job.benefits.map((b, i) => <li key={i}>{b}</li>)}
                </ul>
              </Section>
            )}

            {/* Tech Stack */}
            {job.tech_stack?.length > 0 && (
              <Section title="Tech Stack">
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {job.tech_stack.map((t) => (
                    <span key={t} style={{
                      padding: '4px 12px', borderRadius: 8, fontSize: 12, fontWeight: 500,
                      background: 'var(--bg-primary)', color: 'var(--text-secondary)',
                      border: '1px solid var(--border-color)',
                    }}>{t}</span>
                  ))}
                </div>
              </Section>
            )}

            {/* Sources */}
            <Section title="Found On">
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {(job.source_platforms || []).map((src) => (
                  <span key={src} className="badge badge-secondary" style={{ fontSize: 11 }}>
                    {SOURCE_ICONS[src] || '📋'} {src}
                  </span>
                ))}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8 }}>
                <Clock size={12} style={{ display: 'inline', verticalAlign: 'middle' }} /> Posted {timeAgo(job.posted_date)}
              </div>
            </Section>

            {/* Similar Jobs */}
            {similar.length > 0 && (
              <Section title="Similar Jobs">
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {similar.slice(0, 5).map((sj) => (
                    <div key={sj.id} style={{
                      padding: 12, borderRadius: 10, background: 'var(--bg-elevated)',
                      border: '1px solid var(--border-color)', cursor: 'pointer',
                    }}>
                      <div style={{ fontSize: 14, fontWeight: 600 }}>{sj.title}</div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{sj.company_name}</div>
                    </div>
                  ))}
                </div>
              </Section>
            )}
          </div>

          {/* Pinned Apply CTA */}
          <div style={{
            padding: '16px 24px', borderTop: '1px solid var(--border-color)',
            background: 'var(--bg-surface)',
          }}>
            <button className="btn btn-primary" onClick={() => {
              if (job.apply_url) window.open(job.apply_url, '_blank');
              toast.success('Opening application page...');
            }}
              style={{ width: '100%', padding: '12px 24px', fontSize: 15, borderRadius: 12 }}>
              <ExternalLink size={18} /> Apply Now
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: 24 }}>
      <h4 style={{ fontSize: 14, fontWeight: 700, marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
        {title}
      </h4>
      {children}
    </div>
  );
}

function MetaItem({ icon, label, value, highlight }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 8, padding: 10,
      background: 'var(--bg-elevated)', borderRadius: 10,
    }}>
      <span style={{ color: 'var(--accent-primary)' }}>{icon}</span>
      <div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{label}</div>
        <div style={{ fontSize: 13, fontWeight: 600, color: highlight ? 'var(--success)' : 'var(--text-primary)' }}>
          {value}
        </div>
      </div>
    </div>
  );
}
