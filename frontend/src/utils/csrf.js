// CSRF Token utilities
export const fetchCSRFToken = async () => {
    try {
        // FIX: Use relative path instead of hardcoded localhost
        const response = await fetch('/api/csrf-token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        const data = await response.json();
        if (data.csrf_token) {
            localStorage.setItem('csrf_token', data.csrf_token);
            return data.csrf_token;
        }
    } catch (error) {
        console.error('Failed to fetch CSRF token:', error);
    }
    return null;
};

export const getCSRFToken = () => {
    return localStorage.getItem('csrf_token');
};

// Initialize CSRF token on app load
export const initializeCSRF = () => {
    if (!getCSRFToken()) {
        fetchCSRFToken();
    }
};
