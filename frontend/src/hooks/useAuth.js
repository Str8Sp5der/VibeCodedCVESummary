import { useState, useCallback, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { authAPI } from '../api/endpoints';

/**
 * Hook to manage authentication state
 */
export const useAuth = () => {
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    // Fetch current user on mount
    useEffect(() => {
        const fetchUser = async () => {
            try {
                const token = localStorage.getItem('access_token');
                if (token) {
                    const response = await authAPI.getCurrentUser();
                    setUser(response.data);
                    setError(null);
                } else {
                    setUser(null);
                }
            } catch (error) {
                // FIX #1: Log and notify error instead of silent failure
                const errorMsg = error.response?.data?.detail || 'Failed to fetch user';
                console.error('Failed to fetch user:', errorMsg);
                
                // FIX #2: Only remove token on auth failure, not all errors
                if (error.response?.status === 401) {
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    setUser(null);
                    setError('Your session expired. Please log in again.');
                } else {
                    setError(errorMsg);
                    console.warn('User fetch failed but token retained. Retrying on next mount.');
                }
            } finally {
                setIsLoading(false);
            }
        };

        fetchUser();
    }, []);

    // Register mutation
    const registerMutation = useMutation({
        mutationFn: async (data) => {
            const response = await authAPI.register(data.email, data.password, data.fullName);
            return response.data;
        },
        onSuccess: (data) => {
            if (data.access_token) {
                localStorage.setItem('access_token', data.access_token);
                if (data.refresh_token) {
                    localStorage.setItem('refresh_token', data.refresh_token);
                }
                setUser(data.user);
                setError(null);
            }
        },
        onError: (error) => {
            const errorMsg = error.response?.data?.detail || 'Registration failed';
            console.error('Registration failed:', errorMsg);
            setError(errorMsg);
        },
    });

    // Login mutation
    const loginMutation = useMutation({
        mutationFn: async (data) => {
            const response = await authAPI.login(data.email, data.password);
            return response.data;
        },
        onSuccess: (data) => {
            if (data.access_token) {
                localStorage.setItem('access_token', data.access_token);
                if (data.refresh_token) {
                    localStorage.setItem('refresh_token', data.refresh_token);
                }
                setUser(data.user);
                setError(null);
            }
        },
        onError: (error) => {
            const errorMsg = error.response?.data?.detail || 'Login failed';
            console.error('Login failed:', errorMsg);
            setError(errorMsg);
        },
    });

    // Refresh token mutation
    const refreshTokenMutation = useMutation({
        mutationFn: async () => {
            const refreshToken = localStorage.getItem('refresh_token');
            if (!refreshToken) {
                throw new Error('No refresh token available');
            }
            const response = await authAPI.refreshToken(refreshToken);
            return response.data;
        },
        onSuccess: (data) => {
            if (data.access_token) {
                localStorage.setItem('access_token', data.access_token);
                setError(null);
            }
        },
        onError: (error) => {
            const errorMsg = error.response?.data?.detail || 'Token refresh failed';
            console.error('Token refresh failed:', errorMsg);
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            setUser(null);
            setError('Session expired. Please log in again.');
        },
    });

    // Logout mutation
    const logoutMutation = useMutation({
        mutationFn: async () => {
            const response = await authAPI.logout();
            return response.data;
        },
        onSuccess: () => {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            setUser(null);
            setError(null);
        },
        onError: (error) => {
            console.error('Logout error:', error);
            // Still clear local state even if logout request fails
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            setUser(null);
        },
    });

    const logout = useCallback(() => {
        logoutMutation.mutate();
    }, [logoutMutation]);

    const refreshToken = useCallback(() => {
        return refreshTokenMutation.mutate();
    }, [refreshTokenMutation]);

    return {
        user,
        isLoading,
        isAuthenticated: !!user,
        error,
        setError,
        register: registerMutation,
        login: loginMutation,
        logout,
        refreshToken,
        isRefreshing: refreshTokenMutation.isPending,
    };
};

export default useAuth;
