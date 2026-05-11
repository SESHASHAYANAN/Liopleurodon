const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

/**
 * Fetch from the backend API with automatic retry + exponential backoff.
 * Retries up to `maxRetries` times on network errors (Failed to fetch).
 */
async function fetchApi(endpoint, options = {}, maxRetries = 3) {
  const url = `${API_URL}${endpoint}`;
  let lastError;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json', ...options.headers },
        ...options,
      });
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      return res.json();
    } catch (err) {
      lastError = err;
      // Only retry on network errors, not HTTP errors (4xx/5xx already thrown above)
      const isNetworkError = err.message === 'Failed to fetch' ||
        err.message.includes('NetworkError') ||
        err.message.includes('ECONNREFUSED') ||
        err.name === 'TypeError';

      if (isNetworkError && attempt < maxRetries) {
        // Exponential backoff: 1s, 2s, 4s
        const delay = Math.pow(2, attempt) * 1000;
        console.warn(`[API] Retry ${attempt + 1}/${maxRetries} for ${endpoint} in ${delay}ms`);
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
      throw err;
    }
  }
  throw lastError;
}

export async function searchJobs(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== null && v !== undefined && v !== '') query.set(k, v);
  });
  return fetchApi(`/api/jobs?${query.toString()}`);
}

export async function getJob(id) {
  return fetchApi(`/api/jobs/${id}`);
}

export async function getSimilarJobs(id) {
  return fetchApi(`/api/jobs/${id}/similar`);
}

export async function getJobStats() {
  return fetchApi('/api/jobs/stats');
}

export async function triggerScrape(query = 'software engineer') {
  return fetchApi(`/api/scrape/trigger?query=${encodeURIComponent(query)}`, { method: 'POST' });
}

export async function getScrapeStatus() {
  return fetchApi('/api/scrape/status');
}

export async function getCompanies(params = {}) {
  const query = new URLSearchParams(params);
  return fetchApi(`/api/companies?${query.toString()}`);
}

export async function getCompany(slug) {
  return fetchApi(`/api/companies/${slug}`);
}

export async function summarizeJob(jobId) {
  return fetchApi(`/api/ai/summarize?job_id=${jobId}`, { method: 'POST' });
}

export async function getJobInsights(jobId) {
  return fetchApi(`/api/ai/insights/${jobId}`);
}

export async function matchResumeWithPDF(file, limit = 20) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('limit', limit.toString());

  const url = `${API_URL}/api/ai/match-resume-pdf`;
  let lastError;

  for (let attempt = 0; attempt <= 3; attempt++) {
    try {
      const res = await fetch(url, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      return res.json();
    } catch (err) {
      lastError = err;
      const isNetworkError = err.message === 'Failed to fetch' || err.name === 'TypeError';
      if (isNetworkError && attempt < 3) {
        const delay = Math.pow(2, attempt) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
      throw err;
    }
  }
  throw lastError;
}

export async function matchJobsWithKeywords(params) {
  return fetchApi('/api/ai/keyword-match', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}
