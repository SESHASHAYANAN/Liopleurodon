'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, SlidersHorizontal, X, User, LogOut } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useFilters } from '@/context/FilterContext';
import AuthModal from './AuthModal';

export default function Navbar({ onToggleFilters, showFilters }) {
  const { user, signOut } = useAuth();
  const { filters, updateFilter } = useFilters();
  const [searchValue, setSearchValue] = useState(filters.q || '');
  const [showAuth, setShowAuth] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleSearch = (e) => {
    e.preventDefault();
    updateFilter('q', searchValue);
  };

  return (
    <>
      <nav style={{
        position: 'sticky', top: 0, zIndex: 50,
        background: 'rgba(10, 10, 15, 0.85)', backdropFilter: 'blur(20px)',
        borderBottom: '1px solid var(--border-color)',
        padding: '0 24px', height: 72,
        display: 'flex', alignItems: 'center', gap: 16,
      }}>
        {/* Logo */}
        <a href="/" style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none', flexShrink: 0 }}>
          <div style={{
            width: 40, height: 40, borderRadius: 12,
            background: 'var(--gradient-primary)', display: 'flex',
            alignItems: 'center', justifyContent: 'center', fontSize: 22,
          }}>
            🦕
          </div>
          <span style={{
            fontSize: 20, fontWeight: 800, letterSpacing: '-0.02em',
            background: 'var(--gradient-primary)', WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            Liopleurodon
          </span>
        </a>

        {/* Search Bar */}
        <form onSubmit={handleSearch} style={{ flex: 1, maxWidth: 600, margin: '0 auto' }}>
          <div style={{ position: 'relative' }}>
            <Search size={18} style={{
              position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)',
              color: 'var(--text-muted)',
            }} />
            <input
              type="text"
              placeholder="Search jobs, companies, skills..."
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              className="input"
              style={{ paddingLeft: 44, borderRadius: 100, height: 44, fontSize: 14 }}
            />
            {searchValue && (
              <button type="button" onClick={() => { setSearchValue(''); updateFilter('q', ''); }}
                style={{
                  position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)',
                }}
              >
                <X size={16} />
              </button>
            )}
          </div>
        </form>

        {/* Right Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
          <button
            className="btn btn-ghost"
            onClick={onToggleFilters}
            style={{ position: 'relative', padding: '8px 12px' }}
          >
            <SlidersHorizontal size={18} />
            <span style={{ fontSize: 13 }}>Filters</span>
          </button>

          {user ? (
            <div style={{ position: 'relative' }}>
              <button className="btn btn-ghost" onClick={() => setShowUserMenu(!showUserMenu)}
                style={{ padding: '6px 10px', borderRadius: 100 }}
              >
                <div style={{
                  width: 32, height: 32, borderRadius: '50%',
                  background: 'var(--gradient-primary)', display: 'flex',
                  alignItems: 'center', justifyContent: 'center', fontSize: 14, fontWeight: 700,
                }}>
                  {user.email?.[0]?.toUpperCase() || 'U'}
                </div>
              </button>
              <AnimatePresence>
                {showUserMenu && (
                  <motion.div
                    initial={{ opacity: 0, y: -8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    style={{
                      position: 'absolute', right: 0, top: '100%', marginTop: 8,
                      background: 'var(--bg-surface)', border: '1px solid var(--border-color)',
                      borderRadius: 12, padding: 8, minWidth: 200,
                      boxShadow: 'var(--shadow-card)',
                    }}
                  >
                    <div style={{ padding: '8px 12px', color: 'var(--text-muted)', fontSize: 13 }}>
                      {user.email}
                    </div>
                    <hr style={{ border: 'none', borderTop: '1px solid var(--border-color)', margin: '4px 0' }} />
                    <a href="/dashboard" className="btn btn-ghost"
                      style={{ width: '100%', justifyContent: 'flex-start', borderRadius: 8 }}
                    >
                      <User size={16} /> Dashboard
                    </a>
                    <button className="btn btn-ghost" onClick={() => { signOut(); setShowUserMenu(false); }}
                      style={{ width: '100%', justifyContent: 'flex-start', borderRadius: 8, color: 'var(--error)' }}
                    >
                      <LogOut size={16} /> Sign Out
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ) : (
            <button className="btn btn-primary" onClick={() => setShowAuth(true)}
              style={{ padding: '8px 20px', borderRadius: 100, fontSize: 13 }}
            >
              Sign In
            </button>
          )}
        </div>
      </nav>

      <AnimatePresence>
        {showAuth && <AuthModal onClose={() => setShowAuth(false)} />}
      </AnimatePresence>
    </>
  );
}
