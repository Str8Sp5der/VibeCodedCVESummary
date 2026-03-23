import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useCVEs } from '../hooks/useCVEs';
import Navbar from '../components/Navbar';

/**
 * CVE Search page component
 */
export const CVESearchPage = () => {
    const [searchParams, setSearchParams] = useSearchParams();
    const navigate = useNavigate();

    const [query, setQuery] = useState(searchParams.get('q') || '');
    const [severity, setSeverity] = useState(searchParams.get('severity') || '');
    const [page, setPage] = useState(parseInt(searchParams.get('page'), 10) || 1);

    const { data, isLoading, error } = useCVEs(query, severity, page);

    useEffect(() => {
        const params = new URLSearchParams();
        if (query) params.set('q', query);
        if (severity) params.set('severity', severity);
        if (page > 1) params.set('page', page);
        setSearchParams(params);
    }, [query, severity, page, setSearchParams]);

    const handleSearch = (e) => {
        e.preventDefault();
        setPage(1);
    };

    return (
        <div style={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
            <Navbar />

            <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem' }}>
                {/* Search Form */}
                <form onSubmit={handleSearch} style={{
                    backgroundColor: 'white',
                    padding: '2rem',
                    borderRadius: '8px',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                    marginBottom: '2rem',
                }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: '1rem', marginBottom: '1rem' }}>
                        <input
                            type="text"
                            placeholder="Search CVE ID or description..."
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            style={{
                                padding: '0.75rem',
                                border: '1px solid #ddd',
                                borderRadius: '4px',
                                fontSize: '1rem',
                            }}
                        />

                        <select
                            value={severity}
                            onChange={(e) => setSeverity(e.target.value)}
                            style={{
                                padding: '0.75rem',
                                border: '1px solid #ddd',
                                borderRadius: '4px',
                                fontSize: '1rem',
                            }}
                        >
                            <option value="">All Severities</option>
                            <option value="CRITICAL">🔴 CRITICAL</option>
                            <option value="HIGH">🟠 HIGH</option>
                            <option value="MEDIUM">🟡 MEDIUM</option>
                            <option value="LOW">🟢 LOW</option>
                        </select>

                        <button
                            type="submit"
                            style={{
                                padding: '0.75rem 1.5rem',
                                backgroundColor: '#007bff',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '1rem',
                            }}
                        >
                            Search
                        </button>
                    </div>
                </form>

                {/* Results */}
                {isLoading && <div style={{ textAlign: 'center', fontSize: '1.2rem' }}>⏳ Loading...</div>}

                {error && (
                    <div style={{
                        backgroundColor: '#f8d7da',
                        color: '#721c24',
                        padding: '1rem',
                        borderRadius: '4px',
                        marginBottom: '1rem',
                    }}>
                        Error loading CVEs: {error.message}
                    </div>
                )}

                {data && !isLoading && (
                    <div>
                        <div style={{ marginBottom: '1rem', color: '#666' }}>
                            Found {data.total} CVE{data.total !== 1 ? 's' : ''} (Page {page} of {data.total_pages})
                        </div>

                        <div style={{ display: 'grid', gap: '1rem' }}>
                            {data.items.map((cve) => (
                                <div
                                    key={cve.id}
                                    onClick={() => navigate(`/cves/${cve.id}`)}
                                    style={{
                                        backgroundColor: 'white',
                                        padding: '1.5rem',
                                        borderRadius: '8px',
                                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                        cursor: 'pointer',
                                        transition: 'transform 0.2s, boxShadow 0.2s',
                                    }}
                                    onMouseEnter={(e) => {
                                        e.currentTarget.style.transform = 'translateY(-4px)';
                                        e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
                                    }}
                                    onMouseLeave={(e) => {
                                        e.currentTarget.style.transform = 'translateY(0)';
                                        e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                                    }}
                                >
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                                        <div style={{ flex: 1 }}>
                                            <h3 style={{ margin: '0 0 0.5rem 0', color: '#007bff' }}>{cve.id}</h3>
                                            <p style={{ margin: '0.5rem 0', color: '#666', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                                                {cve.description}
                                            </p>
                                            <div style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#999' }}>
                                                Published: {new Date(cve.published_date).toLocaleDateString()}
                                                {cve.has_poc && ' • 🛠️ Has PoC'}
                                            </div>
                                        </div>

                                        <div style={{ textAlign: 'right', marginLeft: '1rem' }}>
                                            <div style={{
                                                fontSize: '1.5rem',
                                                fontWeight: 'bold',
                                                color: cve.cvss_score >= 9 ? '#dc3545' : cve.cvss_score >= 7 ? '#fd7e14' : cve.cvss_score >= 4 ? '#ffc107' : '#28a745',
                                            }}>
                                                {cve.cvss_score?.toFixed(1) || 'N/A'}
                                            </div>
                                            <div style={{ fontSize: '0.8rem', color: '#999' }}>CVSS</div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Pagination */}
                        <div style={{ marginTop: '2rem', display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
                            <button
                                onClick={() => setPage(Math.max(1, page - 1))}
                                disabled={page === 1}
                                style={{
                                    padding: '0.75rem 1.5rem',
                                    backgroundColor: page === 1 ? '#ccc' : '#007bff',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    cursor: page === 1 ? 'not-allowed' : 'pointer',
                                }}
                            >
                                Previous
                            </button>

                            <button
                                onClick={() => setPage(Math.min(data.total_pages, page + 1))}
                                disabled={page === data.total_pages}
                                style={{
                                    padding: '0.75rem 1.5rem',
                                    backgroundColor: page === data.total_pages ? '#ccc' : '#007bff',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    cursor: page === data.total_pages ? 'not-allowed' : 'pointer',
                                }}
                            >
                                Next
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default CVESearchPage;
