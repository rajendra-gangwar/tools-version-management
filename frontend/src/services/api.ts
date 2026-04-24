import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Component API
export const componentApi = {
  list: (params?: {
    category?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }) => api.get('/components', { params }),

  get: (id: string) => api.get(`/components/${id}`),

  create: (data: unknown) => api.post('/components', data),

  update: (id: string, data: unknown) => api.put(`/components/${id}`, data),

  delete: (id: string) => api.delete(`/components/${id}`),
};

// Environment API
export const environmentApi = {
  list: (params?: {
    environment_type?: string;
    is_active?: boolean;
    search?: string;
    limit?: number;
    offset?: number;
  }) => api.get('/environments', { params }),

  get: (id: string) => api.get(`/environments/${id}`),

  create: (data: unknown) => api.post('/environments', data),

  update: (id: string, data: unknown) => api.put(`/environments/${id}`, data),

  delete: (id: string) => api.delete(`/environments/${id}`),
};

// Mapping API
export const mappingApi = {
  list: (params?: {
    componentId?: string;
    environmentId?: string;
    healthStatus?: string;
    limit?: number;
    offset?: number;
  }) => api.get('/mappings', { params }),

  get: (id: string) => api.get(`/mappings/${id}`),

  create: (data: unknown) => api.post('/mappings', data),

  createBulk: (data: unknown) => api.post('/mappings/bulk', data),

  update: (id: string, data: unknown) => api.put(`/mappings/${id}`, data),

  delete: (id: string) => api.delete(`/mappings/${id}`),

  getMatrix: () => api.get('/mappings/matrix'),
};

// Health API
export const healthApi = {
  check: () => api.get('/health'),
  ready: () => api.get('/health/ready'),
};

// Category API
export const categoryApi = {
  list: (params?: {
    is_active?: boolean;
    search?: string;
    limit?: number;
    offset?: number;
  }) => api.get('/categories', { params }),

  get: (id: string) => api.get(`/categories/${id}`),

  getDefaults: () => api.get('/categories/defaults'),

  create: (data: unknown) => api.post('/categories', data),

  update: (id: string, data: unknown) => api.put(`/categories/${id}`, data),

  delete: (id: string) => api.delete(`/categories/${id}`),

  seedDefaults: () => api.post('/categories/seed-defaults'),
};
