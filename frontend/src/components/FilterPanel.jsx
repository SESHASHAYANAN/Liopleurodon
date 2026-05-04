'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useFilters } from '@/context/FilterContext';
import { X, RotateCcw, ChevronDown } from 'lucide-react';
import { useState } from 'react';

const EXPERIENCE_OPTIONS = ['intern', 'junior', 'mid', 'senior', 'lead', 'staff', 'principal'];
const JOB_TYPE_OPTIONS = ['full-time', 'part-time', 'contract', 'freelance', 'internship'];
const REMOTE_OPTIONS = ['remote', 'hybrid', 'onsite'];
const COMPANY_TYPES = [
  { value: '', label: 'All' },
  { value: 'big_tech', label: '🏢 Big Tech' },
  { value: 'vc_backed', label: '💰 VC-Backed' },
  { value: 'startup', label: '🚀 Startup' },
  { value: 'stealth', label: '🔒 Stealth' },
  { value: 'remote_first', label: '🌍 Remote-First' },
];
const VC_OPTIONS = ['YC', 'a16z', 'Sequoia', 'KP', 'Accel', 'GV', 'Lightspeed', 'Benchmark', 'Tiger Global', 'Bessemer'];
const TECH_OPTIONS = [
  'React', 'Next.js', 'Vue', 'Angular', 'TypeScript', 'JavaScript',
  'Python', 'Go', 'Rust', 'Java', 'C++', 'Ruby',
  'Node.js', 'Django', 'FastAPI', 'Spring',
  'AWS', 'GCP', 'Azure', 'Docker', 'Kubernetes',
  'PostgreSQL', 'MongoDB', 'Redis',
  'GraphQL', 'REST', 'gRPC',
  'TensorFlow', 'PyTorch', 'Machine Learning',
];
const POSTED_OPTIONS = [
  { value: '', label: 'Any time' },
  { value: '24h', label: 'Last 24 hours' },
  { value: 'week', label: 'Last week' },
  { value: 'month', label: 'Last month' },
];
const SOURCE_OPTIONS = ['JSearch', 'SerpApi', 'Adzuna', 'TheirStack', 'The Muse', 'Findwork', 'YC', 'Wellfound', 'LinkedIn'];

function FilterSection({ title, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: 16, marginBottom: 16 }}>
      <button onClick={() => setOpen(!open)} style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%',
        background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-primary)',
        fontSize: 13, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em',
        marginBottom: open ? 12 : 0, padding: 0,
      }}>
        {title}
        <ChevronDown size={14} style={{ transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}>
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function ChipSelect({ options, value, onChange, multi = false }) {
  const selected = multi ? (value || '').split(',').filter(Boolean) : [value];
  const toggle = (opt) => {
    if (multi) {
      const set = new Set(selected);
      set.has(opt) ? set.delete(opt) : set.add(opt);
      onChange([...set].join(','));
    } else {
      onChange(selected[0] === opt ? '' : opt);
    }
  };
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
      {options.map((opt) => {
        const label = typeof opt === 'object' ? opt.label : opt;
        const val = typeof opt === 'object' ? opt.value : opt;
        const isActive = selected.includes(val) || (val === '' && !value);
        return (
          <button key={val} onClick={() => toggle(val)} style={{
            padding: '5px 12px', borderRadius: 100, fontSize: 12, fontWeight: 500,
            border: '1px solid', cursor: 'pointer', transition: 'all 0.2s',
            background: isActive ? 'rgba(124, 58, 237, 0.15)' : 'transparent',
            borderColor: isActive ? 'var(--accent-primary)' : 'var(--border-color)',
            color: isActive ? '#a78bfa' : 'var(--text-secondary)',
          }}>
            {label}
          </button>
        );
      })}
    </div>
  );
}

export default function FilterPanel({ show, onClose }) {
  const { filters, updateFilter, resetFilters, activeFilterCount } = useFilters();

  return (
    <AnimatePresence>
      {show && (
        <motion.aside
          initial={{ x: -280, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: -280, opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          style={{
            background: 'var(--bg-surface)', border: '1px solid var(--border-color)',
            borderRadius: 16, padding: 20, overflowY: 'auto', maxHeight: 'calc(100vh - 96px)',
            position: 'sticky', top: 96,
          }}
        >
          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontWeight: 700, fontSize: 16 }}>Filters</span>
              {activeFilterCount > 0 && (
                <span className="badge badge-primary">{activeFilterCount}</span>
              )}
            </div>
            <div style={{ display: 'flex', gap: 4 }}>
              <button onClick={resetFilters} className="btn btn-ghost" style={{ padding: 6 }} title="Reset filters">
                <RotateCcw size={14} />
              </button>
              <button onClick={onClose} className="btn btn-ghost" style={{ padding: 6, display: 'none' }}>
                <X size={14} />
              </button>
            </div>
          </div>

          {/* Location */}
          <FilterSection title="Location">
            <input className="input" placeholder="City, country, or 'Remote'"
              value={filters.location} onChange={(e) => updateFilter('location', e.target.value)}
              style={{ fontSize: 13 }} />
          </FilterSection>

          {/* Remote Type */}
          <FilterSection title="Work Type">
            <ChipSelect options={REMOTE_OPTIONS} value={filters.remote_type} onChange={(v) => updateFilter('remote_type', v)} />
          </FilterSection>

          {/* Job Type */}
          <FilterSection title="Job Type">
            <ChipSelect options={JOB_TYPE_OPTIONS} value={filters.job_type} onChange={(v) => updateFilter('job_type', v)} />
          </FilterSection>

          {/* Experience Level */}
          <FilterSection title="Experience Level">
            <ChipSelect options={EXPERIENCE_OPTIONS} value={filters.experience_level} onChange={(v) => updateFilter('experience_level', v)} />
          </FilterSection>

          {/* Salary Range */}
          <FilterSection title="Salary Range" defaultOpen={false}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <input className="input" type="number" placeholder="Min" style={{ fontSize: 13 }}
                value={filters.salary_min || ''} onChange={(e) => updateFilter('salary_min', e.target.value ? Number(e.target.value) : null)} />
              <span style={{ color: 'var(--text-muted)' }}>—</span>
              <input className="input" type="number" placeholder="Max" style={{ fontSize: 13 }}
                value={filters.salary_max || ''} onChange={(e) => updateFilter('salary_max', e.target.value ? Number(e.target.value) : null)} />
            </div>
          </FilterSection>

          {/* Visa & Relocation */}
          <FilterSection title="Sponsorship">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer' }}>
                <input type="checkbox" checked={filters.visa_sponsorship === true}
                  onChange={(e) => updateFilter('visa_sponsorship', e.target.checked ? true : null)}
                  style={{ accentColor: 'var(--accent-primary)' }} />
                ✅ Visa Sponsorship
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer' }}>
                <input type="checkbox" checked={filters.relocation_support === true}
                  onChange={(e) => updateFilter('relocation_support', e.target.checked ? true : null)}
                  style={{ accentColor: 'var(--accent-primary)' }} />
                🏠 Relocation Support
              </label>
            </div>
          </FilterSection>

          {/* Company Type */}
          <FilterSection title="Company Type">
            <ChipSelect options={COMPANY_TYPES} value={filters.company_type} onChange={(v) => updateFilter('company_type', v)} />
          </FilterSection>

          {/* VC Backer */}
          <FilterSection title="VC Backer" defaultOpen={false}>
            <ChipSelect options={VC_OPTIONS} value={filters.vc_backer} onChange={(v) => updateFilter('vc_backer', v)} />
          </FilterSection>

          {/* Tech Stack */}
          <FilterSection title="Tech Stack" defaultOpen={false}>
            <ChipSelect options={TECH_OPTIONS} value={filters.tech_stack} onChange={(v) => updateFilter('tech_stack', v)} multi />
          </FilterSection>

          {/* Posted Date */}
          <FilterSection title="Posted Date">
            <ChipSelect options={POSTED_OPTIONS} value={filters.posted_within} onChange={(v) => updateFilter('posted_within', v)} />
          </FilterSection>

          {/* Source */}
          <FilterSection title="Source" defaultOpen={false}>
            <ChipSelect options={SOURCE_OPTIONS} value={filters.source} onChange={(v) => updateFilter('source', v)} />
          </FilterSection>
        </motion.aside>
      )}
    </AnimatePresence>
  );
}
