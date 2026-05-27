import axios from 'axios';

const API_BASE_URL = '';

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
  login: (data) => {
    // 1. Data ko Form Data format me convert kar rahe hain
    const formData = new URLSearchParams();
    
    // FastAPI specifically 'username' key dhoondhta hai form data me
    formData.append('username', data.email);
    formData.append('password', data.password);

    // 2. Custom header ke sath POST request bhej rahe hain
    return api.post('/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
  },
  
  // Register pehle ki tarah JSON hi rahega
  register: (data) => api.post('/register', data),
};

export const documentAPI = {
  fetchDocuments: (sessionId) => api.get('/documents', { params: { session_id: sessionId } }),
  uploadDocument: (formData) => api.post('/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  deleteDocument: (filename, sessionId) => api.delete(`/documents/${filename}`, { params: { session_id: sessionId } }),
  cleanupData: (sessionId) => api.delete('/cleanup', { params: { session_id: sessionId } }),
};

export const chatAPI = {
  search: (query, sessionId, documentSelector) => api.get('/search', { params: { query, session_id: sessionId, document_selector: documentSelector } }),
};

export default api;