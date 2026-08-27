import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || '';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

function clearSessionAndGoToLogin() {
  localStorage.removeItem('token');
  localStorage.removeItem('role');
  localStorage.removeItem('trust_mode');
  window.dispatchEvent(new Event('tonertrack:session-expired'));
  // Hard navigation so any stuck dashboard state resets to the login screen
  if (!window.location.pathname.includes('login')) {
    const base = window.location.pathname.startsWith('/') ? '/' : '/';
    if (window.location.pathname !== '/' || window.location.hash) {
      window.location.assign('/');
    } else {
      window.location.reload();
    }
  }
}

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    const url = String(error?.config?.url || '');
    // Do not bounce login/register failures into a logout loop
    const isAuthForm =
      url.includes('/login') || url.includes('/register');
    if (status === 401 && !isAuthForm) {
      clearSessionAndGoToLogin();
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (username: string, password: string) =>
    api.post('/login', new URLSearchParams({ username, password }).toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),
  register: (username: string, email: string, password: string) =>
    api.post('/register', { username, email, password }),
  me: () => api.get('/me'),
};

export const trustAPI = {
  info: () => api.get('/trust/info'),
  status: () => api.get('/trust/status'),
  choose: (mode: 'manual_only' | 'agent_accepted') =>
    api.post('/trust/choice', { mode }),
};

export const printersAPI = {
  list: (skip = 0, limit = 100) => api.get(`/printers/?skip=${skip}&limit=${limit}`),
  add: (data: {
    name: string;
    ip_address?: string;
    location?: string;
    department?: string;
    connection_mode?: string;
    snmp_community?: string;
    toner_level?: number | null;
    notes?: string;
  }) => api.post('/printers/', data),
  update: (id: number, data: Record<string, unknown>) => api.patch(`/printers/${id}`, data),
  get: (id: number) => api.get(`/printers/${id}`),
  delete: (id: number) => api.delete(`/printers/${id}`),
  checks: (id: number, limit = 10) => api.get(`/printers/${id}/checks?limit=${limit}`),
};

export const agentAPI = {
  listTokens: () => api.get('/agent/tokens'),
  createToken: (name = 'default') => api.post('/agent/tokens', { name }),
  revokeToken: (id: number) => api.post(`/agent/tokens/${id}/revoke`),
  enableHelperDownload: (id: number) => api.post(`/agent/tokens/${id}/enable-helper-download`),
  quickSetup: () => api.post('/agent/quick-setup'),
  getPollConfig: () => api.get('/agent/poll-config'),
  setPollConfig: (poll_interval_seconds: number) =>
    api.put('/agent/poll-config', { poll_interval_seconds }),
  /** Download Windows starter; pass raw access key (shown once at setup). */
  downloadStarterBat: async (rawToken: string) => {
    const base = process.env.REACT_APP_API_URL || '';
    const res = await fetch(`${base}/agent/helper/starter.bat`, {
      headers: { 'X-Agent-Token': rawToken },
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(err || 'Download failed');
    }
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'Run-TonerTrack-Checker.bat';
    a.click();
    window.URL.revokeObjectURL(url);
  },
};

export const statsAPI = {
  visits: () => api.get('/stats/visits'),
};

export default api;
