import { defineStore } from 'pinia';
import axios from 'axios';

// Set base API URL
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
axios.defaults.baseURL = API_URL;

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('hrms_token') || '',
    user: JSON.parse(localStorage.getItem('hrms_user') || 'null'),
    loading: false,
    error: null
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => ['SUPER_ADMIN', 'HR_MANAGER'].includes(state.user?.role),
    isHR: (state) => ['SUPER_ADMIN', 'HR_MANAGER', 'HR_OFFICER'].includes(state.user?.role),
    isAccountant: (state) => ['SUPER_ADMIN', 'ACCOUNTANT'].includes(state.user?.role),
    userRole: (state) => state.user?.role || 'GUEST',
    fullName: (state) => state.user?.full_name || 'User'
  },
  
  actions: {
    async login(username, password) {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.post('/auth/login', { username, password });
        const { token, ...userData } = response.data;
        
        this.token = token;
        this.user = userData;
        
        localStorage.setItem('hrms_token', token);
        localStorage.setItem('hrms_user', JSON.stringify(userData));
        
        // Setup bearer header
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        return true;
      } catch (err) {
        console.error('Login error:', err);
        this.error = err.response?.data?.detail || 'Invalid username or password';
        return false;
      } finally {
        this.loading = false;
      }
    },
    
    logout() {
      this.token = '';
      this.user = null;
      localStorage.removeItem('hrms_token');
      localStorage.removeItem('hrms_user');
      delete axios.defaults.headers.common['Authorization'];
    },
    
    initializeAuth() {
      if (this.token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`;
      }
    }
  }
});
