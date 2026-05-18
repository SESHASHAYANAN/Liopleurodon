export function formatSalary(min, max, currency = 'USD') {
  const fmt = (n) => {
    if (n >= 1000) return `${Math.round(n / 1000)}K`;
    return n?.toString() || '';
  };
  if (min && max) return `$${fmt(min)} – $${fmt(max)}`;
  if (min) return `$${fmt(min)}+`;
  if (max) return `Up to $${fmt(max)}`;
  return 'Competitive';
}

export function timeAgo(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now - date;
  const mins = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  const weeks = Math.floor(days / 7);
  if (mins < 60) return `${mins}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;
  if (weeks < 5) return `${weeks}w ago`;
  return date.toLocaleDateString();
}

export function getInitials(name) {
  if (!name) return '??';
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
}

export function slugify(text) {
  return text?.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '') || '';
}

export const EXPERIENCE_COLORS = {
  intern: '#8b5cf6',
  junior: '#06b6d4',
  mid: '#10b981',
  senior: '#f59e0b',
  lead: '#ef4444',
  staff: '#ec4899',
  principal: '#f97316',
};

export const SOURCE_ICONS = {
  JSearch: '🔍',
  SerpApi: '🌐',
  Adzuna: '📊',
  TheirStack: '🏗️',
  Apify: '🤖',
  'The Muse': '🎭',
  Findwork: '💼',
  YC: '🟧',
  Wellfound: '😇',
  LinkedIn: '🔗',
  Seed: '⭐',
  WebScraper: '🕷️',
  'YC-WATS': '🟧',
  'YC-Jobs': '🟧',
  Simplify: '📋',
  ArcDev: '🌐',
  'Web3-DS': '🔮',
  'Web3-Remote': '🔮',
  'Web3-OKX': '🔮',
  MigrateMate: '✈️',
  Arbeitnow: '🇪🇺',
};
