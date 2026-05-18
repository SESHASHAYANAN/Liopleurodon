'use client';

export default function SkeletonCard() {
  return (
    <div className="card" style={{ padding: 20 }}>
      <div style={{ display: 'flex', gap: 12, marginBottom: 14 }}>
        <div className="skeleton" style={{ width: 44, height: 44, borderRadius: 10, flexShrink: 0 }} />
        <div style={{ flex: 1 }}>
          <div className="skeleton" style={{ height: 14, width: '40%', marginBottom: 8 }} />
          <div className="skeleton" style={{ height: 18, width: '80%' }} />
        </div>
      </div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
        <div className="skeleton" style={{ height: 20, width: 100 }} />
        <div className="skeleton" style={{ height: 20, width: 70 }} />
      </div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <div className="skeleton" style={{ height: 16, width: 80 }} />
        <div className="skeleton" style={{ height: 16, width: 60 }} />
      </div>
      <div style={{ display: 'flex', gap: 4, marginBottom: 14 }}>
        {[1, 2, 3].map((i) => (
          <div key={i} className="skeleton" style={{ height: 22, width: 60 }} />
        ))}
      </div>
      <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: 12, display: 'flex', justifyContent: 'space-between' }}>
        <div className="skeleton" style={{ height: 14, width: 100 }} />
        <div style={{ display: 'flex', gap: 6 }}>
          <div className="skeleton" style={{ height: 28, width: 70 }} />
          <div className="skeleton" style={{ height: 28, width: 70 }} />
        </div>
      </div>
    </div>
  );
}
