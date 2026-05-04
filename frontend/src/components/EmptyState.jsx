'use client';

import { motion } from 'framer-motion';
import { SearchX, RefreshCw } from 'lucide-react';

export default function EmptyState({ onReset }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        padding: 60, textAlign: 'center',
      }}
    >
      <motion.div
        animate={{ y: [0, -10, 0] }}
        transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
        style={{
          width: 120, height: 120, borderRadius: '50%',
          background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(6, 182, 212, 0.1))',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          marginBottom: 24, border: '2px dashed var(--border-color)',
        }}
      >
        <SearchX size={48} style={{ color: 'var(--text-muted)' }} />
      </motion.div>
      <h3 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>No jobs found</h3>
      <p style={{ fontSize: 14, color: 'var(--text-muted)', maxWidth: 320, marginBottom: 20, lineHeight: 1.6 }}>
        Try adjusting your filters or search terms. The deep sea holds many treasures — keep exploring!
      </p>
      {onReset && (
        <button className="btn btn-secondary" onClick={onReset}>
          <RefreshCw size={16} /> Reset Filters
        </button>
      )}
    </motion.div>
  );
}
