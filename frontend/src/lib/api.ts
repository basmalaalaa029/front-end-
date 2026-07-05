import axios from 'axios';
import { useAuthStore } from "@/features/auth/stores/auth-store";
import { rehydrateUserScopedStores } from "@/features/cv-editor/stores/rehydrate-user-stores";

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ✅ REQUEST INTERCEPTOR
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('✅ Token added to request');
    }
    return config;
  },
  (error) => {
    console.error('❌ Request error:', error);
    return Promise.reject(error);
  }
);

// ✅ RESPONSE INTERCEPTOR
api.interceptors.response.use(
  (response) => {
    console.log('✅ Response success:', response.status);
    return response;
  },
  (error) => {
    // إذا كان الخطأ 401 (Unauthorized)
    if (error.response && error.response.status === 401) {
      console.warn('⚠️ Token expired or invalid');
      
      // إذا لم نكن في صفحة تسجيل الدخول
      if (window.location.pathname !== '/login') {
        const { logout } = useAuthStore.getState();
        logout();
        rehydrateUserScopedStores();
        
        // روح للـ login page
        window.location.href = '/login';
      }
    }
    
    console.error('❌ Response error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export default api;