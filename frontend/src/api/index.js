import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

request.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      router.push('/login')
    }
    const msg = error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(msg))
  }
)

export default request

// ─── Auth ─────────────────────────────────────────────────────────────
export const authApi = {
  login: data => request.post('/auth/login', data),
  register: data => request.post('/auth/register', data),
  me: () => request.get('/auth/me'),
}

// ─── Projects ─────────────────────────────────────────────────────────
export const projectsApi = {
  list: params => request.get('/projects', { params }),
  stats: () => request.get('/projects/stats'),
  get: id => request.get(`/projects/${id}`),
  create: data => request.post('/projects', data),
  update: (id, data) => request.put(`/projects/${id}`, data),
  delete: id => request.delete(`/projects/${id}`),
}

// ─── Templates ────────────────────────────────────────────────────────
export const templatesApi = {
  categories: () => request.get('/templates/categories'),
  list: params => request.get('/templates', { params }),
  get: id => request.get(`/templates/${id}`),
  favorites: () => request.get('/templates/favorites'),
  toggleFavorite: id => request.post(`/templates/${id}/favorite`),
}

// ─── Generate ─────────────────────────────────────────────────────────
export const generateApi = {
  create: data => request.post('/generate', data),
  aiFill: data => request.post('/generate/ai-fill-variables', data),
  tasks: params => request.get('/generate/tasks', { params }),
  taskDetail: id => request.get(`/generate/tasks/${id}`),
  cancelTask: id => request.post(`/generate/tasks/${id}/cancel`),
  history: () => request.get('/generate/history'),
}

// ─── Characters ───────────────────────────────────────────────────────
export const charactersApi = {
  list: params => request.get('/characters', { params }),
  get: id => request.get(`/characters/${id}`),
  create: data => request.post('/characters', data),
  update: (id, data) => request.put(`/characters/${id}`, data),
  delete: id => request.delete(`/characters/${id}`),
}

// ─── Scenes ───────────────────────────────────────────────────────────
export const scenesApi = {
  list: params => request.get('/scenes', { params }),
  create: data => request.post('/scenes', data),
  update: (id, data) => request.put(`/scenes/${id}`, data),
  delete: id => request.delete(`/scenes/${id}`),
}

// ─── Shots ────────────────────────────────────────────────────────────
export const shotsApi = {
  listByProject: projectId => request.get(`/shots/project/${projectId}`),
  create: data => request.post('/shots', data),
  update: (id, data) => request.put(`/shots/${id}`, data),
  delete: id => request.delete(`/shots/${id}`),
}

// ─── Assets ───────────────────────────────────────────────────────────
export const assetsApi = {
  list: params => request.get('/assets', { params }),
  upload: (formData, params) => request.post('/assets/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    params,
  }),
  delete: id => request.delete(`/assets/${id}`),
}
