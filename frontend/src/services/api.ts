import axios from 'axios';

// Same origin when FE is served by API; override with REACT_APP_API_URL if split
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
};

export default api;
