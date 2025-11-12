import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a response interceptor for handling errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Handle specific error cases
      switch (error.response.status) {
        case 401:
          // Redirect to login or refresh token
          window.location.href = '/login';
          break;
        case 403:
          console.error('Permission denied');
          break;
        default:
          console.error('API Error:', error.response.data);
      }
    }
    return Promise.reject(error);
  }
);

export const fetchCourses = () => api.get('/api/courses/');
export const fetchTopic = (id) => api.get(`/api/topics/${id}/`);
export const markTopicCompleted = (id) => api.post(`/api/topics/${id}/mark_completed/`);
export const login = (phone) => api.post('/api/auth/login/', { phone });
export const logout = () => api.post('/api/auth/logout/');

export default api;