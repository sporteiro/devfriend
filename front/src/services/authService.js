import axios from 'axios';

const API_URL = process.env.VUE_APP_API_URL || 'http://localhost:8888';

// Create axios instance with default configuration
const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Helper function to extract user-friendly error message
const extractErrorMessage = (data, status) => {
  if (data && typeof data === 'object') {
    // FastAPI typically returns errors in 'detail' field
    if (data.detail) {
      if (Array.isArray(data.detail)) {
        // Extract messages from validation errors
        return data.detail.map(item => {
          if (typeof item === 'string') return item;
          if (item.msg) return item.msg;
          if (item.message) return item.message;
          return 'Validation error';
        }).join(', ');
      }
      return String(data.detail);
    } else if (data.message) {
      return data.message;
    } else if (data.error) {
      return data.error;
    }
  } else if (typeof data === 'string') {
    return data;
  }

  // Default messages based on status code
  switch (status) {
    case 400:
      return 'Invalid request. Please check your input.';
    case 401:
      return 'Authentication required. Please log in.';
    case 403:
      return 'You do not have permission to perform this action.';
    case 404:
      return 'Resource not found.';
    case 409:
      return 'This resource already exists.';
    case 422:
      return 'Validation error. Please check your input.';
    case 429:
      return 'Too many requests. Please try again later.';
    case 500:
    case 502:
    case 503:
    case 504:
      return 'Server error. Please try again later.';
    default:
      return 'An unexpected error occurred. Please try again.';
  }
};

// Response interceptor for handling API errors consistently
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      // Network error or server not reachable
      return Promise.reject(new Error('Network error. Please check your internet connection and try again.'));
    }

    const { status, data } = error.response;
    const errorMessage = extractErrorMessage(data, status);

    return Promise.reject(new Error(errorMessage));
  }
);

export const authService = {
  async register(email, password) {
    const response = await api.post('/auth/register', {
      email,
      password,
    });
    return response.data;
  },

  async login(email, password) {
    const response = await api.post('/auth/login', {
      email,
      password,
    });

    // Extract token from response
    const { access_token } = response.data;

    // Store token in localStorage
    localStorage.setItem('devfriend_token', access_token);

    // Set authorization header for future requests
    this.setAuthHeader(access_token);

    return access_token;
  },

  async getCurrentUser() {
    const token = this.getToken();

    if (!token) {
      return null;
    }

    try {
      const response = await api.get('/auth/me');

      // Optionally store user data in localStorage
      if (response.data) {
        localStorage.setItem('devfriend_user', JSON.stringify(response.data));
      }

      return response.data;
    } catch (error) {
      // If token is invalid or expired, log out user
      this.logout();
      return null;
    }
  },

  logout() {
    // Clear all auth-related data from localStorage
    localStorage.removeItem('devfriend_token');
    localStorage.removeItem('devfriend_user');

    // Remove authorization header
    this.setAuthHeader(null);
  },

  getToken() {
    return localStorage.getItem('devfriend_token');
  },

  isAuthenticated() {
    return !!this.getToken();
  },

  // Add method to set authorization header globally
  setAuthHeader(token) {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete api.defaults.headers.common['Authorization'];
    }
  },

  // Initialize auth header on app startup
  initializeAuthHeader() {
    const token = this.getToken();
    if (token) {
      this.setAuthHeader(token);
    }
  },
};

// Initialize auth header when module is loaded
authService.initializeAuthHeader();

export default authService;
