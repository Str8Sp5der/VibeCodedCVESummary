import axios from 'axios';

// Use relative path for API calls through nginx proxy (/api)
// Falls back to VITE_API_URL env var for development environments
const API_URL = import.meta.env.VITE_API_URL || '/api';

// Track if we're already redirecting to avoid double-redirects
let isRedirectingToLogin = false;

// Create axios instance
export const apiClient = axios.create({
    baseURL: API_URL,
    withCredentials: true,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor - add JWT token
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        // Add CSRF token if available
        const csrfToken = localStorage.getItem('csrf_token');
        if (csrfToken && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(config.method?.toUpperCase())) {
            config.headers['X-CSRF-Token'] = csrfToken;
        }

        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor - handle errors
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        // FIX: Handle 401 Unauthorized with single redirect
        if (error.response?.status === 401) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            
            // FIX: Prevent multiple redirects to login
            if (!isRedirectingToLogin) {
                isRedirectingToLogin = true;
                console.warn('Session expired. Redirecting to login...');
                window.location.href = '/login';
                
                // Reset flag after a delay to allow for new page load
                setTimeout(() => {
                    isRedirectingToLogin = false;
                }, 5000);
            }
        }

        // Handle 403 Forbidden
        if (error.response?.status === 403) {
            console.error('Access denied:', error.response.data?.detail || 'Forbidden');
            // Don't redirect - let component handle this
        }

        // Handle 429 Rate Limited
        if (error.response?.status === 429) {
            console.error('Rate limited. Please try again later.');
        }

        // Handle 422 Validation Error with details
        if (error.response?.status === 422) {
            console.error('Validation error:', error.response.data);
        }

        // Handle server errors
        if (error.response?.status >= 500) {
            console.error('Server error:', error.response.data?.detail || 'Server error');
        }

        return Promise.reject(error);
    }
);

export default apiClient;
