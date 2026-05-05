'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, Building2, Lock, Globe, Zap } from 'lucide-react';
import { getJobStats } from '@/lib/api';
import { useFilters } from '@/context/FilterContext';

export default function TrendingSidebar() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const { updateFilter } = useFilters();

  useEffect(() => {
    let cancelled = false;
    let retryTimer;

    const fetchStats = (attempt = 0) => {
      getJobStats()
        .then(data => {
          if (!cancelled) {
            setStats(data);
            setLoading(false);
          }
        })
        .catch(() => {
          if (!cancelled && attempt < 4) {
            // Retry with escalating delays: 2s, 4s, 8s, 15s
            const delay = [2000, 4000, 8000, 15000][attempt] || 15000;
            retryTimer = setTimeout(() => fetchStats(attempt + 1), delay);
          } else if (!cancelled) {
            setStats(null);
            setLoading(false);
          }
        });
    };

    fetchStats();
    return () => { cancelled = true; clearTimeout(retryTimer); };
  }, []);

  const statItems = [
    { icon: <Zap size={16} />, label: 'Total Jobs', value: stats?.total_jobs || 0, color: 'var(--accent-primary)' },
    { icon: <Globe size={16} />, label: 'Remote Jobs', value: stats?.remote_jobs || 0, color: 'var(--success)' },
    { icon: <TrendingUp size={16} />, label: 'VC-Backed', value: stats?.vc_backed_jobs || 0, color: 'var(--accent-secondary)' },
    { icon: <Lock size={16} />, label: 'Stealth', value: stats?.stealth_jobs || 0, color: 'var(--text-muted)' },
    { icon: <Building2 size={16} />, label: 'Big Tech', value: stats?.big_tech_jobs || 0, color: 'var(--warning)' },
    { icon: <span style={{fontSize: 14}}>✅</span>, label: 'Visa Sponsor', value: stats?.visa_jobs || 0, color: 'var(--success)' },
    { icon: <span style={{fontSize: 14}}>🏠</span>, label: 'Relocation', value: stats?.relo_jobs || 0, color: 'var(--accent-primary)' },
  ];

  const trendingCompanies = [
    { name: 'OpenAI', badge: 'YC', jobs: 42 },
    { name: 'Stripe', badge: 'Sequoia', jobs: 38 },
    { name: 'Vercel', badge: 'Accel', jobs: 29 },
    { name: 'Supabase', badge: 'YC', jobs: 24 },
    { name: 'Figma', badge: 'a16z', jobs: 21 },
    { name: 'Linear', badge: 'Sequoia', jobs: 18 },
    { name: 'Notion', badge: 'Accel', jobs: 16 },
    { name: 'Railway', badge: 'YC', jobs: 12 },
  ];

  return (
    <aside style={{
      position: 'sticky', top: 96,
      display: 'flex', flexDirection: 'column', gap: 16,
      maxHeight: 'calc(100vh - 96px)', overflowY: 'auto',
    }}>
      {/* Stats Card */}
      <div className="card" style={{ padding: 20 }}>
        <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
          📊 Platform Stats
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {statItems.map((item) => (
            <motion.div key={item.label}
              whileHover={{ x: 4 }}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '8px 12px', borderRadius: 10, background: 'var(--bg-elevated)',
                cursor: 'default',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ color: item.color }}>{item.icon}</span>
                <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{item.label}</span>
              </div>
              <span style={{ fontSize: 15, fontWeight: 700, color: item.color }}>
                {loading ? '—' : item.value.toLocaleString()}
              </span>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Trending Companies */}
      <div className="card" style={{ padding: 20 }}>
        <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
          🔥 Trending Companies
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {trendingCompanies.map((company, i) => (
            <motion.div key={company.name}
              onClick={() => updateFilter('q', company.name)}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              whileHover={{ x: 4 }}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '8px 12px', borderRadius: 10, cursor: 'pointer',
                transition: 'background 0.2s',
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-elevated)'}
              onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{
                  width: 28, height: 28, borderRadius: 8,
                  background: 'var(--gradient-primary)', display: 'flex',
                  alignItems: 'center', justifyContent: 'center',
                  fontSize: 12, fontWeight: 700, color: '#fff',
                }}>
                  {company.name[0]}
                </span>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>{company.name}</div>
                  <span className="badge badge-primary" style={{ fontSize: 9, padding: '1px 6px' }}>
                    {company.badge}
                  </span>
                </div>
              </div>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                {company.jobs} jobs
              </span>
            </motion.div>
          ))}
        </div>
      </div>

      {/* CTA */}
      <div className="card" style={{
        padding: 20, textAlign: 'center',
        background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(6, 182, 212, 0.1))',
        border: '1px solid rgba(124, 58, 237, 0.2)',
      }}>
        <div style={{ fontSize: 28, marginBottom: 8 }}>🦕</div>
        <h4 style={{ fontSize: 14, fontWeight: 700, marginBottom: 4 }}>Liopleurodon AI</h4>
        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12, lineHeight: 1.5 }}>
          Upload your resume and let AI find your perfect match.
        </p>
        <a href="/dashboard" className="btn btn-primary" style={{ width: '100%', fontSize: 13, borderRadius: 10, textDecoration: 'none' }}>
          Try AI Matching
        </a>
      </div>
    </aside>
  );
}
