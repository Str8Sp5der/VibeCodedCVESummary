import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useCVEDetail, useSubscribeCVE } from '../hooks/useCVEs';
import Navbar from '../components/Navbar';
import PoCViewer from '../components/PoCViewer';
import useAuth from '../hooks/useAuth';

/**
 * CVE Detail page component
 */
export const CVEDetailPage = () => {
    const { cveId } = useParams();
    const navigate = useNavigate();
    const { isAuthenticated } = useAuth();

    const { data: cve, isLoading, error } = useCVEDetail(cveId);
    const subscribeMutation = useSubscribeCVE();
    const [subscribeSuccess, setSubscribeSuccess] = useState(false);

    const handleSubscribe = () => {
        if (!isAuthenticated) {
            navigate('/login');
            return;
        }

        subscribeMutation.mutate(cveId, {
            onSuccess: () => {
                setSubscribeSuccess(true);
                setTimeout(() => setSubscribeSuccess(false), 3000);
            },
        });
    };

    return (
        <div style={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
            <Navbar />

            <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '2rem' }}>
                {isLoading && <div style={{ textAlign: 'center', fontSize: '1.2rem' }}>⏳ Loading...</div>}

                {error && (
                    <div style={{
                        backgroundColor: '#f8d7da',
                        color: '#721c24',
                        padding: '1rem',
                        borderRadius: '4px',
                    }}>
                        Error: {error.message}
                    </div>
                )}

                {cve && !isLoading && (
                    <div>
                        {/* Header */}
                        <div style={{
                            backgroundColor: 'white',
                            padding: '2rem',
                            borderRadius: '8px',
                            marginBottom: '2rem',
                            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                        }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                                <div>
                                    <h1 style={{ margin: '0 0 1rem 0', color: '#007bff' }}>{cve.id}</h1>
                                    <p style={{ margin: '0.5rem 0', color: '#666' }}>
                                        Published: {new Date(cve.published_date).toLocaleDateString()}
                                    </p>
                                </div>

                                <div style={{ textAlign: 'right' }}>
                                    <div style={{
                                        fontSize: '2rem',
                                        fontWeight: 'bold',
                                        color: cve.cvss_score >= 9 ? '#dc3545' : cve.cvss_score >= 7 ? '#fd7e14' : cve.cvss_score >= 4 ? '#ffc107' : '#28a745',
                                        marginBottom: '0.5rem',
                                    }}>
                                        {cve.cvss_score?.toFixed(1) || 'N/A'}
                                    </div>
                                    <div style={{ fontSize: '0.9rem', color: '#999' }}>
                                        CVSS Score
                                        {cve.cvss_vector && <div>{cve.cvss_vector}</div>}
                                    </div>

                                    <button
                                        onClick={handleSubscribe}
                                        disabled={subscribeMutation.isPending}
                                        style={{
                                            marginTop: '1rem',
                                            padding: '0.75rem 1.5rem',
                                            backgroundColor: isAuthenticated ? '#28a745' : '#007bff',
                                            color: 'white',
                                            border: 'none',
                                            borderRadius: '4px',
                                            cursor: subscribeMutation.isPending ? 'wait' : 'pointer',
                                            opacity: subscribeMutation.isPending ? 0.7 : 1,
                                        }}
                                    >
                                        {subscribeMutation.isPending ? '...' : '🔔 Subscribe'}
                                    </button>

                                    {subscribeSuccess && (
                                        <div style={{
                                            marginTop: '0.5rem',
                                            color: '#28a745',
                                            fontSize: '0.9rem',
                                        }}>
                                            ✓ Subscribed!
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Description */}
                        <div style={{
                            backgroundColor: 'white',
                            padding: '2rem',
                            borderRadius: '8px',
                            marginBottom: '2rem',
                            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                        }}>
                            <h2 style={{ marginTop: 0 }}>Description</h2>
                            <p style={{ lineHeight: '1.6', color: '#333' }}>{cve.description}</p>
                        </div>

                        {/* CWE IDs */}
                        {cve.cwe_ids && cve.cwe_ids.length > 0 && (
                            <div style={{
                                backgroundColor: 'white',
                                padding: '2rem',
                                borderRadius: '8px',
                                marginBottom: '2rem',
                                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                            }}>
                                <h2 style={{ marginTop: 0 }}>CWE (Weakness Types)</h2>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {cve.cwe_ids.map((cwe) => (
                                        <span key={cwe} style={{
                                            backgroundColor: '#e7f3ff',
                                            border: '1px solid #007bff',
                                            padding: '0.5rem 1rem',
                                            borderRadius: '4px',
                                            fontSize: '0.9rem',
                                            color: '#007bff',
                                        }}>
                                            {cwe}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Vulnerable Products */}
                        {cve.vulnerable_products && cve.vulnerable_products.length > 0 && (
                            <div style={{
                                backgroundColor: 'white',
                                padding: '2rem',
                                borderRadius: '8px',
                                marginBottom: '2rem',
                                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                            }}>
                                <h2 style={{ marginTop: 0 }}>Vulnerable Products</h2>
                                <ul style={{ color: '#333' }}>
                                    {cve.vulnerable_products.slice(0, 10).map((product, idx) => (
                                        <li key={idx} style={{ marginBottom: '0.5rem' }}>{product}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Proof of Concept */}
                        {cve.has_poc && (
                            <div style={{
                                backgroundColor: 'white',
                                padding: '2rem',
                                borderRadius: '8px',
                                marginBottom: '2rem',
                                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                            }}>
                                <h2 style={{ marginTop: 0 }}>🛠️ Proof of Concept</h2>
                                {isAuthenticated ? (
                                    <>
                                        {cve.poc_code && <PoCViewer pocCode={cve.poc_code} pocLanguage={cve.poc_language} />}
                                        {cve.poc_source && (
                                            <p style={{ marginTop: '1rem', color: '#666' }}>
                                                Source: <a href={cve.poc_source} target="_blank" rel="noreferrer" style={{ color: '#007bff' }}>
                                                    {cve.poc_source}
                                                </a>
                                            </p>
                                        )}
                                    </>
                                ) : (
                                    <button
                                        onClick={() => navigate('/login')}
                                        style={{
                                            padding: '0.75rem 1.5rem',
                                            backgroundColor: '#007bff',
                                            color: 'white',
                                            border: 'none',
                                            borderRadius: '4px',
                                            cursor: 'pointer',
                                        }}
                                    >
                                        Login to view PoC
                                    </button>
                                )}
                            </div>
                        )}

                        {/* References */}
                        {cve.references && cve.references.length > 0 && (
                            <div style={{
                                backgroundColor: 'white',
                                padding: '2rem',
                                borderRadius: '8px',
                                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                            }}>
                                <h2 style={{ marginTop: 0 }}>References</h2>
                                <ul style={{ color: '#333' }}>
                                    {cve.references.map((ref, idx) => (
                                        <li key={idx} style={{ marginBottom: '0.5rem' }}>
                                            <a href={ref.url} target="_blank" rel="noreferrer" style={{ color: '#007bff' }}>
                                                {ref.url}
                                            </a>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                )}

                <button
                    onClick={() => navigate('/search')}
                    style={{
                        marginTop: '2rem',
                        padding: '0.75rem 1.5rem',
                        backgroundColor: '#6c757d',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                    }}
                >
                    ← Back to Search
                </button>
            </div>
        </div>
    );
};

export default CVEDetailPage;
