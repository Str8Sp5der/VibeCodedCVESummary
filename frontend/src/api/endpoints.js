import apiClient from './client';

// CVE endpoints
export const cveAPI = {
    // Search CVEs
    searchCVEs: (params) => {
        return apiClient.get('/api/cves', { params });
    },

    // Get CVE detail
    getCVEDetail: (cveId) => {
        return apiClient.get(`/api/cves/${cveId}`);
    },

    // Get PoC code for CVE
    getCVEPoC: (cveId) => {
        return apiClient.get(`/api/cves/${cveId}/poc`);
    },

    // Subscribe to CVE alerts
    subscribeCVE: (cveId) => {
        return apiClient.post('/api/subscriptions', { cve_id: cveId });
    },

    // Unsubscribe from CVE alerts
    unsubscribeCVE: (cveId) => {
        return apiClient.delete(`/api/subscriptions/${cveId}`);
    },

    // Get user subscriptions
    getSubscriptions: () => {
        return apiClient.get('/api/subscriptions');
    },
};

// Auth endpoints
export const authAPI = {
    // Register new user
    register: (email, password, fullName) => {
        return apiClient.post('/auth/register', {
            email,
            password,
            full_name: fullName,
        });
    },

    // Login
    login: (email, password) => {
        return apiClient.post('/auth/login', {
            email,
            password,
        });
    },

    // Refresh token - FIX: SEND REFRESH TOKEN IN BODY
    refreshToken: (refreshToken) => {
        return apiClient.post('/auth/refresh', {
            refresh_token: refreshToken,
        });
    },

    // Logout
    logout: () => {
        return apiClient.post('/auth/logout');
    },

    // Get current user - FIX: CALL /auth/me NOT /api/users/me
    getCurrentUser: () => {
        return apiClient.get('/auth/me');
    },
};

// Admin endpoints
export const adminAPI = {
    // Get audit logs
    getAuditLogs: (params) => {
        return apiClient.get('/admin/audit-logs', { params });
    },

    // Get sync status
    getSyncStatus: () => {
        return apiClient.get('/admin/sync-status');
    },

    // Trigger manual sync
    triggerSync: () => {
        return apiClient.post('/admin/sync/trigger');
    },
};

export default {
    cveAPI,
    authAPI,
    adminAPI,
};
