import axios from 'axios';

const configuredApiUrl = process.env.REACT_APP_API_URL || 'http://localhost:5000';
const normalizedApiUrl = configuredApiUrl.replace(/\/api\/?$/, '');

// Create axios instance with base configuration
const api = axios.create({
  baseURL: normalizedApiUrl,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      console.error('API Error:', error.response.data);
    } else if (error.request) {
      console.error('Network Error:', error.request);
    } else {
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default api;

