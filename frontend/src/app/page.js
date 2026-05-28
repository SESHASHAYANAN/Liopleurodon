'use client';

import { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import FilterPanel from '@/components/FilterPanel';
import JobFeed from '@/components/JobFeed';
import TrendingSidebar from '@/components/TrendingSidebar';

export default function Home() {
  const [showFilters, setShowFilters] = useState(true);

  useEffect(() => {
    if (window.innerWidth <= 768) {
      setShowFilters(false);
    }
  }, []);

  return (
    <>
      <Navbar onToggleFilters={() => setShowFilters(!showFilters)} showFilters={showFilters} />
      <main className="main-layout">
        {/* Left Sidebar — Filters (hidden on mobile via CSS, shown as overlay when toggled) */}
        <FilterPanel show={showFilters} onClose={() => setShowFilters(false)} />

        {/* Center — Job Feed */}
        <JobFeed />

        {/* Right Sidebar — Trending */}
        <TrendingSidebar />
      </main>
    </>
  );
}
