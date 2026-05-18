'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { X, Building2, MapPin, DollarSign, Shield, Plane, Users, Briefcase, ExternalLink } from 'lucide-react';
import { formatSalary, getInitials } from '@/lib/utils';

export default function JobDetailsModal({ job, onClose }) {
  if (!job) return null;

  const companyName = job.company_name || 'Unknown Company';

  const handleApply = () => {
    if (job.apply_url) window.open(job.apply_url, '_blank', 'noopener,noreferrer');
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0, zIndex: 100,
          background: 'rgba(0, 0, 0, 0.7)',
          backdropFilter: 'blur(8px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          padding: 20,
        }}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.92, y: 30 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.92, y: 30 }}
          transition={{ type: 'spring', damping: 28, stiffness: 350 }}
          onClick={(e) => e.stopPropagation()}
          style={{
            width: '100%', maxWidth: 620,
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-color)',
            borderRadius: 20,
            display: 'flex', flexDirection: 'column',
            overflow: 'hidden',
            boxShadow: '0 25px 60px rgba(0, 0, 0, 0.5), 0 0 80px rgba(139, 92, 246, 0.08)',
            maxHeight: '90vh',
          }}
        >
          {/* ── Header ── */}
          <div style={{
            padding: '20px 24px', borderBottom: '1px solid var(--border-color)',
            display: 'flex', alignItems: 'center', gap: 14, background: 'var(--bg-elevated)',
          }}>
            {job.company_logo_url ? (
              <img src={job.company_logo_url} alt=""
                style={{ width: 48, height: 48, borderRadius: 12, background: '#fff', padding: 4, objectFit: 'contain' }} />
            ) : (
              <div style={{
                width: 48, height: 48, borderRadius: 12, background: 'var(--gradient-primary)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 18, fontWeight: 700, color: '#fff', flexShrink: 0,
              }}>
                {getInitials(companyName)}
              </div>
            )}
            <div style={{ flex: 1, minWidth: 0 }}>
              <h3 style={{ fontSize: 18, fontWeight: 700 }}>{job.title}</h3>
              <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>{companyName}</span>
            </div>
            <button onClick={onClose} className="btn btn-ghost" style={{ padding: 6, flexShrink: 0 }}>
              <X size={20} />
            </button>
          </div>

          {/* ── Body ── */}
          <div style={{ flex: 1, overflowY: 'auto', padding: 24, display: 'flex', flexDirection: 'column', gap: 20 }}>

            {/* Company Details */}
            <DetailSection title="Company Details" icon={<Building2 size={16} />}>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                <InfoChip label="Company" value={companyName} />
                {job.company_type && (
                  <InfoChip label="Type" value={
                    job.company_type === 'big_tech' ? 'Big Tech' :
                    job.company_type === 'vc_backed' ? 'VC-Backed Startup' :
                    job.company_type === 'stealth' ? '🔒 Stealth Mode' :
                    job.company_type.charAt(0).toUpperCase() + job.company_type.slice(1)
                  } />
                )}
                {job.vc_backer && <InfoChip label="Backed By" value={job.vc_backer} highlight />}
                {job.ats_detected && <InfoChip label="ATS Platform" value={job.ats_detected} />}
                {job.location_city && (
                  <InfoChip label="Location" value={`${job.location_city}${job.location_country ? `, ${job.location_country}` : ''}`} />
                )}
                {job.remote_type && (
                  <InfoChip label="Work Mode" value={
                    job.remote_type === 'remote' ? '🌍 Remote' :
                    job.remote_type === 'hybrid' ? '🔀 Hybrid' : '📍 Onsite'
                  } />
                )}
              </div>
            </DetailSection>

            {/* Job Role */}
            <DetailSection title="Job Role" icon={<Briefcase size={16} />}>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                <InfoChip label="Title" value={job.title} />
                {job.experience_level && (
                  <InfoChip label="Experience" value={job.experience_level.charAt(0).toUpperCase() + job.experience_level.slice(1)} />
                )}
                {job.job_type && <InfoChip label="Employment" value={job.job_type} />}
                {job.tech_stack?.length > 0 && (
                  <div style={{ width: '100%', marginTop: 4 }}>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>Tech Stack</span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {job.tech_stack.map((t) => (
                        <span key={t} style={{
                          padding: '4px 12px', borderRadius: 8, fontSize: 12, fontWeight: 500,
                          background: 'var(--bg-primary)', color: 'var(--text-secondary)',
                          border: '1px solid var(--border-color)',
                        }}>{t}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </DetailSection>

            {/* Salary & Compensation */}
            <DetailSection title="Salary & Compensation" icon={<DollarSign size={16} />}>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                <InfoChip label="Salary Range"
                  value={formatSalary(job.salary_min, job.salary_max, job.salary_currency)}
                  highlight={!!(job.salary_min || job.salary_max)} />
                {job.salary_currency && <InfoChip label="Currency" value={job.salary_currency} />}
                {job.salary_period && <InfoChip label="Period" value={job.salary_period.charAt(0).toUpperCase() + job.salary_period.slice(1)} />}
              </div>
            </DetailSection>

            {/* Visa Sponsorship */}
            <DetailSection title="Visa Sponsorship" icon={<Shield size={16} />}>
              <div style={{
                padding: '12px 16px', borderRadius: 12,
                background: job.visa_sponsorship ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.06)',
                border: `1px solid ${job.visa_sponsorship ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.15)'}`,
                display: 'flex', alignItems: 'center', gap: 10,
              }}>
                <span style={{ fontSize: 22 }}>{job.visa_sponsorship ? '✅' : '❌'}</span>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: job.visa_sponsorship ? 'var(--success)' : 'var(--text-secondary)' }}>
                    {job.visa_sponsorship ? 'Visa Sponsorship Available' : 'No Visa Sponsorship'}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    {job.visa_sponsorship ? 'This employer offers work visa sponsorship for eligible candidates.' : 'This position does not include visa sponsorship at this time.'}
                  </div>
                </div>
              </div>
            </DetailSection>

            {/* About the Job Role */}
            <DetailSection title="About the Job Role" icon={<Briefcase size={16} />}>
              <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>
                {job.description || 'No description provided.'}
              </p>
              {job.requirements?.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Requirements</span>
                  <ul style={{ paddingLeft: 20, marginTop: 6, fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                    {job.requirements.map((r, i) => <li key={i}>{r}</li>)}
                  </ul>
                </div>
              )}
              {job.responsibilities?.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Responsibilities</span>
                  <ul style={{ paddingLeft: 20, marginTop: 6, fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                    {job.responsibilities.map((r, i) => <li key={i}>{r}</li>)}
                  </ul>
                </div>
              )}
            </DetailSection>

            {/* Total Number of Employees */}
            <DetailSection title="Total Number of Employees" icon={<Users size={16} />}>
              <div style={{
                padding: '12px 16px', borderRadius: 12,
                background: 'rgba(99, 102, 241, 0.06)',
                border: '1px solid rgba(99, 102, 241, 0.15)',
                display: 'flex', alignItems: 'center', gap: 10,
              }}>
                <Users size={24} style={{ color: '#818cf8' }} />
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
                    {job.employee_count || estimateEmployees(job.company_type)}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Estimated company size</div>
                </div>
              </div>
            </DetailSection>

            {/* Relocation Support */}
            <DetailSection title="Relocation Support" icon={<Plane size={16} />}>
              <div style={{
                padding: '12px 16px', borderRadius: 12,
                background: job.relocation_support ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.06)',
                border: `1px solid ${job.relocation_support ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.15)'}`,
                display: 'flex', alignItems: 'center', gap: 10,
              }}>
                <span style={{ fontSize: 22 }}>{job.relocation_support ? '✅' : '❌'}</span>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: job.relocation_support ? 'var(--success)' : 'var(--text-secondary)' }}>
                    {job.relocation_support ? 'Relocation Assistance Offered' : 'No Relocation Support'}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    {job.relocation_support ? 'The company provides relocation packages for eligible hires.' : 'Relocation support is not available for this role.'}
                  </div>
                </div>
              </div>
            </DetailSection>
          </div>

          {/* ── Footer CTA ── */}
          <div style={{ padding: '16px 24px', borderTop: '1px solid var(--border-color)', background: 'var(--bg-surface)' }}>
            <button className="btn btn-primary" onClick={handleApply}
              style={{ width: '100%', padding: '12px 24px', fontSize: 15, borderRadius: 12 }}>
              <ExternalLink size={18} /> Apply Now
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

/* ── Helper: estimate employees from company type ── */
function estimateEmployees(type) {
  switch (type) {
    case 'big_tech': return '10,000+ employees';
    case 'vc_backed': return '50 – 500 employees';
    case 'stealth': return '1 – 50 employees';
    default: return '10 – 200 employees';
  }
}

/* ── Section wrapper ── */
function DetailSection({ title, icon, children }) {
  return (
    <div style={{
      padding: 18, borderRadius: 14,
      background: 'var(--bg-elevated)', border: '1px solid var(--border-color)',
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14,
        fontSize: 13, fontWeight: 700, textTransform: 'uppercase',
        letterSpacing: '0.05em', color: 'var(--text-muted)',
      }}>
        <span style={{ color: 'var(--accent-primary)' }}>{icon}</span> {title}
      </div>
      {children}
    </div>
  );
}

/* ── Info chip ── */
function InfoChip({ label, value, highlight }) {
  return (
    <div style={{
      padding: '8px 14px', borderRadius: 10,
      background: 'var(--bg-primary)', border: '1px solid var(--border-color)',
      minWidth: 120, flex: '1 1 auto',
    }}>
      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>{label}</div>
      <div style={{ fontSize: 13, fontWeight: 600, color: highlight ? 'var(--success)' : 'var(--text-primary)' }}>
        {value}
      </div>
    </div>
  );
}
