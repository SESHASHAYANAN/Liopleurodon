'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { getCompany } from '@/lib/api';
import Navbar from '@/components/Navbar';
import JobCard from '@/components/JobCard';
import JobDetailPanel from '@/components/JobDetailPanel';
import SkeletonCard from '@/components/SkeletonCard';
import { Building2, Globe, Users, DollarSign, MapPin, ExternalLink } from 'lucide-react';

export default function CompanyPage() {
  const params = useParams();
  const [company, setCompany] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedJob, setSelectedJob] = useState(null);

  useEffect(() => {
    if (params.slug) {
      getCompany(params.slug)
        .then((data) => {
          setCompany(data.company);
          setJobs(data.jobs || []);
        })
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [params.slug]);

  return (
    <>
      <Navbar onToggleFilters={() => {}} />
      <main style={{ maxWidth: 1200, margin: '0 auto', padding: 24 }}>
        {loading ? (
          <div>
            <div className="skeleton" style={{ height: 200, marginBottom: 24, borderRadius: 16 }} />
            <div className="job-grid">
              {[1, 2, 3, 4].map(i => <SkeletonCard key={i} />)}
            </div>
          </div>
        ) : company ? (
          <>
            {/* Company Header */}
            <div className="card" style={{ padding: 32, marginBottom: 24, display: 'flex', gap: 24, alignItems: 'center', flexWrap: 'wrap' }}>
              <div style={{
                width: 80, height: 80, borderRadius: 16,
                background: 'var(--gradient-primary)', display: 'flex',
                alignItems: 'center', justifyContent: 'center',
                fontSize: 32, fontWeight: 700, color: '#fff', flexShrink: 0,
              }}>
                {company.logo_url ? (
                  <img src={company.logo_url} alt="" style={{ width: 80, height: 80, borderRadius: 16, objectFit: 'contain' }} />
                ) : company.name?.[0]}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  <h1 style={{ fontSize: 28, fontWeight: 800 }}>{company.name}</h1>
                  {company.vc_backers?.map(vc => (
                    <span key={vc} className="badge badge-primary">{vc}</span>
                  ))}
                </div>
                <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginTop: 8, maxWidth: 600 }}>
                  {company.description || 'No description available.'}
                </p>
                <div style={{ display: 'flex', gap: 16, marginTop: 12, flexWrap: 'wrap' }}>
                  {company.headquarters && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 13, color: 'var(--text-muted)' }}>
                      <MapPin size={14} /> {company.headquarters}
                    </span>
                  )}
                  {company.size && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 13, color: 'var(--text-muted)' }}>
                      <Users size={14} /> {company.size}
                    </span>
                  )}
                  {company.funding_stage && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 13, color: 'var(--text-muted)' }}>
                      <DollarSign size={14} /> {company.funding_stage}
                    </span>
                  )}
                  {company.website_url && (
                    <a href={company.website_url} target="_blank" rel="noopener noreferrer"
                      style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 13, color: 'var(--accent-primary)', textDecoration: 'none' }}>
                      <Globe size={14} /> Website
                    </a>
                  )}
                </div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 36, fontWeight: 800, color: 'var(--accent-primary)' }}>{jobs.length}</div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>Active Jobs</div>
              </div>
            </div>

            {/* Jobs */}
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>
              Open Positions ({jobs.length})
            </h2>
            <div className="job-grid">
              {jobs.map((job, i) => (
                <JobCard key={job.id || i} job={job} index={i} onViewDetails={setSelectedJob} />
              ))}
            </div>
          </>
        ) : (
          <div style={{ textAlign: 'center', padding: 60 }}>
            <h2 style={{ fontSize: 20 }}>Company not found</h2>
          </div>
        )}

        {selectedJob && <JobDetailPanel job={selectedJob} onClose={() => setSelectedJob(null)} />}
      </main>
    </>
  );
}
