'use client';

import { motion } from 'framer-motion';
import { MapPin, Clock, Bookmark, BookmarkCheck, ExternalLink } from 'lucide-react';
import { formatSalary, timeAgo, getInitials, EXPERIENCE_COLORS, SOURCE_ICONS } from '@/lib/utils';
import { useAuth } from '@/context/AuthContext';
import toast from 'react-hot-toast';
import { useState } from 'react';

export default function JobCard({ job, index, onViewDetails, onSave, savedJobs = [] }) {
  const { user } = useAuth();
  const isSaved = savedJobs.includes(job.id);
  const [saving, setSaving] = useState(false);

  const handleSave = async (e) => {
    e.stopPropagation();
    if (!user) {
      toast.error('Sign in to save jobs');
      return;
    }
    setSaving(true);
    await onSave?.(job.id, !isSaved);
    setSaving(false);
  };

  const handleApply = (e) => {
    e.stopPropagation();
    if (job.apply_url) {
      window.open(job.apply_url, '_blank');
      toast.success('Opening application page...');
    }
  };

  const techTags = (job.tech_stack || []).slice(0, 5);
  const remainingTech = (job.tech_stack || []).length - 5;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      className="card"
      onClick={() => onViewDetails?.(job)}
      style={{ padding: 20, cursor: 'pointer', position: 'relative' }}
    >
      {/* Header Row */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
        {/* Company Logo */}
        {job.company_logo_url ? (
          <img src={job.company_logo_url} alt={job.company_name}
            style={{ width: 44, height: 44, borderRadius: 10, objectFit: 'contain', background: '#fff', padding: 4, flexShrink: 0 }}
            onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }}
          />
        ) : null}
        {(!job.company_logo_url) && (
          <div style={{
            width: 44, height: 44, borderRadius: 10, flexShrink: 0,
            background: 'var(--gradient-primary)', display: 'flex',
            alignItems: 'center', justifyContent: 'center',
            fontSize: 16, fontWeight: 700, color: '#fff',
          }}>
            {getInitials(job.company_name)}
          </div>
        )}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-secondary)' }}>
              {job.company_name}
            </span>
            {job.vc_backer && (
              <span className="badge badge-primary" style={{ fontSize: 10, padding: '2px 8px' }}>
                {job.vc_backer}
              </span>
            )}
            {job.is_stealth && (
              <span className="badge badge-stealth" style={{ fontSize: 10, padding: '2px 8px' }}>
                🔒 Stealth
              </span>
            )}
            {job.company_type === 'big_tech' && (
              <span className="badge badge-secondary" style={{ fontSize: 10, padding: '2px 8px' }}>
                🏢 Big Tech
              </span>
            )}
          </div>
          <h3 style={{ fontSize: 16, fontWeight: 700, lineHeight: 1.3, marginTop: 2 }}>
            {job.title}
          </h3>
        </div>
        {/* Save Button */}
        <button onClick={handleSave} style={{
          background: 'none', border: 'none', cursor: 'pointer', padding: 4, flexShrink: 0,
          color: isSaved ? 'var(--accent-primary)' : 'var(--text-muted)',
          transition: 'color 0.2s',
        }}>
          {isSaved ? <BookmarkCheck size={20} /> : <Bookmark size={20} />}
        </button>
      </div>

      {/* Location + Remote Badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10, flexWrap: 'wrap' }}>
        {job.location_city && (
          <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 13, color: 'var(--text-muted)' }}>
            <MapPin size={13} /> {job.location_city}{job.location_country ? `, ${job.location_country}` : ''}
          </span>
        )}
        {job.remote_type && (
          <span className={`badge ${job.remote_type === 'remote' ? 'badge-success' : job.remote_type === 'hybrid' ? 'badge-warning' : 'badge-secondary'}`}
            style={{ fontSize: 11, padding: '2px 8px' }}>
            {job.remote_type === 'remote' ? '🌍 Remote' : job.remote_type === 'hybrid' ? '🔀 Hybrid' : '📍 Onsite'}
          </span>
        )}
      </div>

      {/* Salary + Experience */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10, flexWrap: 'wrap' }}>
        <span style={{
          fontSize: 14, fontWeight: 600,
          color: (job.salary_min || job.salary_max) ? 'var(--success)' : 'var(--text-muted)',
        }}>
          {formatSalary(job.salary_min, job.salary_max, job.salary_currency)}
        </span>
        {job.experience_level && (
          <span className="badge" style={{
            fontSize: 11, padding: '2px 8px',
            background: `${EXPERIENCE_COLORS[job.experience_level] || '#64748b'}20`,
            color: EXPERIENCE_COLORS[job.experience_level] || '#94a3b8',
          }}>
            {job.experience_level.charAt(0).toUpperCase() + job.experience_level.slice(1)}
          </span>
        )}
        {job.job_type && (
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            {job.job_type}
          </span>
        )}
      </div>

      {/* Tech Stack Tags */}
      {techTags.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 10 }}>
          {techTags.map((tech) => (
            <span key={tech} style={{
              padding: '2px 8px', borderRadius: 6, fontSize: 11, fontWeight: 500,
              background: 'var(--bg-elevated)', color: 'var(--text-secondary)',
              border: '1px solid var(--border-color)',
            }}>
              {tech}
            </span>
          ))}
          {remainingTech > 0 && (
            <span style={{ fontSize: 11, color: 'var(--text-muted)', padding: '2px 4px' }}>
              +{remainingTech} more
            </span>
          )}
        </div>
      )}

      {/* Visa + Relocation Badges */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
        {job.visa_sponsorship && (
          <span className="badge badge-success" style={{ fontSize: 11, padding: '2px 8px' }}>✅ Visa</span>
        )}
        {job.relocation_support && (
          <span className="badge badge-success" style={{ fontSize: 11, padding: '2px 8px' }}>🏠 Relocation</span>
        )}
      </div>

      {/* Footer Row: Sources + Time + Actions */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        borderTop: '1px solid var(--border-color)', paddingTop: 12, marginTop: 4,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {/* Source icons */}
          <div style={{ display: 'flex', gap: 2 }}>
            {(job.source_platforms || []).map((src) => (
              <span key={src} title={src} style={{ fontSize: 14, cursor: 'default' }}>
                {SOURCE_ICONS[src] || '📋'}
              </span>
            ))}
          </div>
          <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: 'var(--text-muted)' }}>
            <Clock size={12} /> {timeAgo(job.posted_date)}
          </span>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          <button className="btn btn-secondary" onClick={(e) => { e.stopPropagation(); onViewDetails?.(job); }}
            style={{ padding: '5px 12px', fontSize: 12, borderRadius: 8 }}>
            Details
          </button>
          <button className="btn btn-primary" onClick={handleApply}
            style={{ padding: '5px 12px', fontSize: 12, borderRadius: 8 }}>
            <ExternalLink size={12} /> Apply
          </button>
        </div>
      </div>
    </motion.div>
  );
}
