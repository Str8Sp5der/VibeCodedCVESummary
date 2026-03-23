import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';

import CVESearchPage from './pages/CVESearchPage';
import CVEDetailPage from './pages/CVEDetailPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import Dashboard from './pages/Dashboard';
import PrivateRoute from './components/PrivateRoute';
import { initializeCSRF } from './utils/csrf';

// Initialize CSRF token
initializeCSRF();

// Create React Query client
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            retry: 1,
            refetchOnWindowFocus: false,
        },
    },
});

function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <BrowserRouter>
                <Routes>
                    {/* Public routes */}
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/register" element={<RegisterPage />} />
                    <Route path="/search" element={<CVESearchPage />} />
                    <Route path="/cves/:cveId" element={<CVEDetailPage />} />

                    {/* Protected routes */}
                    <Route path="/dashboard" element={<Dashboard />} />

                    {/* Redirect root to search */}
                    <Route path="/" element={<Navigate to="/search" replace />} />

                    {/* 404 catch-all */}
                    <Route path="*" element={<Navigate to="/search" replace />} />
                </Routes>
            </BrowserRouter>
        </QueryClientProvider>
    );
}

export default App;
