'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect, Suspense } from 'react';
import { useFilters } from '@/context/FilterContext';
import Navbar from '@/components/Navbar';
import FilterPanel from '@/components/FilterPanel';
import JobFeed from '@/components/JobFeed';
import { useState } from 'react';

function SearchContent() {
  const searchParams = useSearchParams();
  const { updateFilters } = useFilters();
  const [showFilters, setShowFilters] = useState(true);

  // Sync URL params to filter state
  useEffect(() => {
    const params = {};
    for (const [key, value] of searchParams.entries()) {
      if (value === 'true') params[key] = true;
      else if (value === 'false') params[key] = false;
      else params[key] = value;
    }
    if (Object.keys(params).length > 0) {
      updateFilters(params);
    }
  }, [searchParams, updateFilters]);

  return (
    <>
      <Navbar onToggleFilters={() => setShowFilters(!showFilters)} showFilters={showFilters} />
      <main style={{ display: 'grid', gridTemplateColumns: showFilters ? '280px 1fr' : '1fr', gap: 24, maxWidth: 1400, margin: '0 auto', padding: 24 }}>
        <FilterPanel show={showFilters} onClose={() => setShowFilters(false)} />
        <JobFeed />
      </main>
    </>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>Loading search...</div>}>
      <SearchContent />
    </Suspense>
  );
}
