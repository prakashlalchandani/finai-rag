import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Automatically attach token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  login: (data) => api.post('/login', data),
  register: (data) => api.post('/register', data),
};

export const documentAPI = {
  fetchDocuments: (sessionId) => api.get('/documents', { params: { session_id: sessionId } }),
  uploadDocument: (formData) => api.post('/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  deleteDocument: (filename, sessionId) => api.delete(`/documents/${filename}`, { params: { session_id: sessionId } }),
};

export const chatAPI = {
  search: (query, sessionId, documentSelector) => api.get('/search', { params: { query, session_id: sessionId, document_selector: documentSelector } }),
};

export default api;