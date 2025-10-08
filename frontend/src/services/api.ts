import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'https://print-track-backend.onrender.com';
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
  register: (username: string, password: string) =>
    api.post('/register', { username, password }),
};

export const printersAPI = {
  scan: (subnet: string) => api.post('/printers/scan', { subnet }),
  add: (data: { ip: string; model?: string; connection_mode?: string; snmp_community?: string }) =>
    api.post('/printers/add', data),
  list: (skip = 0, limit = 100) => api.get(`/printers/?skip=${skip}&limit=${limit}`),
  status: (id: number) => api.get(`/printers/${id}/status`),
  delete: (id: number) => api.delete(`/printers/${id}`),
};

export default api;