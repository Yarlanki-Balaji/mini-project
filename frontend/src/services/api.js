import axios from 'axios'

export const API_BASE = 'http://localhost:8000'
const http = axios.create({ baseURL: API_BASE })

export const detectCategory = (idea) =>
  http.get('/api/detect-category', { params: { idea } }).then((r) => r.data)

export const getCustomerInsight = (category) =>
  http.get('/api/customer', { params: { category } }).then((r) => r.data)

export const strategyStreamUrl = (idea) =>
  `${API_BASE}/api/strategy/stream?idea=${encodeURIComponent(idea)}`
