import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { cveAPI } from '../api/endpoints';

/**
 * Hook to search and fetch CVEs
 */
export const useCVEs = (query = '', severity = '', page = 1) => {
    return useQuery({
        queryKey: ['cves', query, severity, page],
        queryFn: async () => {
            const response = await cveAPI.searchCVEs({
                q: query,
                severity: severity || undefined,
                page,
                limit: 50,
            });
            return response.data;
        },
        staleTime: 5 * 60 * 1000, // 5 minutes
        enabled: query.length > 0 || severity !== '',
        retry: 1,
    });
};

/**
 * Hook to fetch CVE detail
 */
export const useCVEDetail = (cveId) => {
    return useQuery({
        queryKey: ['cve', cveId],
        queryFn: async () => {
            if (!cveId) return null;
            const response = await cveAPI.getCVEDetail(cveId);
            return response.data;
        },
        enabled: !!cveId,
        staleTime: 10 * 60 * 1000, // 10 minutes
    });
};

/**
 * Hook to fetch PoC code for CVE
 */
export const useCVEPoC = (cveId) => {
    return useQuery({
        queryKey: ['cve-poc', cveId],
        queryFn: async () => {
            if (!cveId) return null;
            const response = await cveAPI.getCVEPoC(cveId);
            return response.data;
        },
        enabled: !!cveId,
        staleTime: 30 * 60 * 1000, // 30 minutes
    });
};

/**
 * Hook to subscribe to CVE alerts
 */
export const useSubscribeCVE = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (cveId) => {
            const response = await cveAPI.subscribeCVE(cveId);
            return response.data;
        },
        onSuccess: () => {
            // Invalidate subscriptions cache
            queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
        },
        onError: (error) => {
            console.error('Failed to subscribe:', error);
        },
    });
};

/**
 * Hook to unsubscribe from CVE alerts
 */
export const useUnsubscribeCVE = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (cveId) => {
            const response = await cveAPI.unsubscribeCVE(cveId);
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
        },
        onError: (error) => {
            console.error('Failed to unsubscribe:', error);
        },
    });
};

/**
 * Hook to fetch user subscriptions
 */
export const useSubscriptions = () => {
    return useQuery({
        queryKey: ['subscriptions'],
        queryFn: async () => {
            const response = await cveAPI.getSubscriptions();
            return response.data;
        },
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
};
