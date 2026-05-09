'use client';

import { createContext, useContext, useState, useCallback } from 'react';

const FilterContext = createContext({});

const defaultFilters = {
  q: '',
  location: '',
  remote_type: '',
  experience_level: '',
  job_type: '',
  salary_min: null,
  salary_max: null,
  visa_sponsorship: null,
  relocation_support: null,
  company_type: '',
  vc_backer: '',
  tech_stack: '',
  source: '',
  posted_within: '',
  sort_by: 'created_at',
  sort_order: 'desc',
};

export function FilterProvider({ children }) {
  const [filters, setFilters] = useState(defaultFilters);

  const updateFilter = useCallback((key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  const updateFilters = useCallback((newFilters) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters(defaultFilters);
  }, []);

  const activeFilterCount = Object.entries(filters).filter(([key, val]) => {
    if (['sort_by', 'sort_order'].includes(key)) return false;
    return val !== '' && val !== null && val !== undefined;
  }).length;

  return (
    <FilterContext.Provider value={{ filters, updateFilter, updateFilters, resetFilters, activeFilterCount }}>
      {children}
    </FilterContext.Provider>
  );
}

export const useFilters = () => useContext(FilterContext);
