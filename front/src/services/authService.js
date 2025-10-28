import axios from 'axios';

const API_URL = process.env.VUE_APP_API_URL || 'http://localhost:8888';

export const authService = {
  async register(email, password) {
    try {
      const response = await axios.post(`${API_URL}/auth/register`, {
        email,
        password,
      });
      return response.data;
    } catch (error) {
      throw new Error(
        error.response?.data?.detail || 'Error during registration'
      );
    }
  },

  async login(email, password) {
    try {
      const response = await axios.post(`${API_URL}/auth/login`, {
        email,
        password,
      });
      const { access_token } = response.data;
      localStorage.setItem('devfriend_token', access_token);
      return access_token;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Error during login');
    }
  },

  async getCurrentUser() {
    const token = this.getToken();
    if (!token) {
      return null;
    }

    try {
      const response = await axios.get(`${API_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      return response.data;
    } catch (error) {
      this.logout();
      return null;
    }
  },

  logout() {
    localStorage.removeItem('devfriend_token');
    localStorage.removeItem('devfriend_user');
  },

  getToken() {
    return localStorage.getItem('devfriend_token');
  },

  isAuthenticated() {
    return !!this.getToken();
  },
};

