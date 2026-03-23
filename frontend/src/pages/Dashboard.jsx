import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useSubscriptions } from '../hooks/useCVEs';
import useAuth from '../hooks/useAuth';
import Navbar from '../components/Navbar';
import PrivateRoute from '../components/PrivateRoute';

/**
 * User Dashboard component
 */
export const Dashboard = () => {
    const navigate = useNavigate();
    const { user } = useAuth();
    const { data: subscriptions, isLoading } = useSubscriptions();

    return (
        <PrivateRoute>
            <div style={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
                <Navbar />

                <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '2rem' }}>
                    <h1>📊 My Dashboard</h1>

                    {/* User Info */}
                    <div style={{
                        backgroundColor: 'white',
                        padding: '1.5rem',
                        borderRadius: '8px',
                        marginBottom: '2rem',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                    }}>
                        <h2 style={{ marginTop: 0 }}>Welcome, {user?.full_name || user?.email}!</h2>
                        <p>Email: {user?.email}</p>
                        <p>Role: {user?.role}</p>
                        <p>Member since: {new Date(user?.created_at).toLocaleDateString()}</p>
                    </div>

                    {/* CVE Subscriptions */}
                    <div>
                        <h2>🔔 My CVE Subscriptions ({subscriptions?.total || 0})</h2>

                        {isLoading && <div>Loading subscriptions...</div>}

                        {subscriptions && subscriptions.items.length > 0 ? (
                            <div style={{ display: 'grid', gap: '1rem' }}>
                                {subscriptions.items.map((cve) => (
                                    <div
                                        key={cve.id}
                                        onClick={() => navigate(`/cves/${cve.id}`)}
                                        style={{
                                            backgroundColor: 'white',
                                            padding: '1.5rem',
                                            borderRadius: '8px',
                                            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                            cursor: 'pointer',
                                            transition: 'transform 0.2s',
                                        }}
                                        onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
                                        onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
                                    >
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                                            <div>
                                                <h3 style={{ margin: '0 0 0.5rem 0', color: '#007bff' }}>{cve.id}</h3>
                                                <p style={{ margin: '0.5rem 0', color: '#666' }}>
                                                    {cve.description}
                                                </p>
                                            </div>
                                            <div style={{ textAlign: 'right', marginLeft: '1rem' }}>
                                                <div style={{
                                                    fontSize: '1.5rem',
                                                    fontWeight: 'bold',
                                                    color: cve.cvss_score >= 9 ? '#dc3545' : '#fd7e14',
                                                }}>
                                                    {cve.cvss_score?.toFixed(1) || 'N/A'}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div style={{
                                backgroundColor: 'white',
                                padding: '2rem',
                                borderRadius: '8px',
                                textAlign: 'center',
                                color: '#999',
                            }}>
                                <p>No subscriptions yet. <button onClick={() => navigate('/search')} style={{
                                    backgroundColor: 'transparent',
                                    border: 'none',
                                    color: '#007bff',
                                    cursor: 'pointer',
                                    textDecoration: 'underline',
                                }}>
                                    Search CVEs
                                </button> to get started.</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </PrivateRoute>
    );
};

export default Dashboard;
