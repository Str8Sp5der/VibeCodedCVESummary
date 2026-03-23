import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuth from '../hooks/useAuth';

/**
 * Navbar component
 */
export const Navbar = () => {
    const { user, isAuthenticated, logout } = useAuth();
    const navigate = useNavigate();
    const [showDropdown, setShowDropdown] = useState(false);

    return (
        <nav style={{
            backgroundColor: '#1a1a1a',
            color: 'white',
            padding: '1rem 2rem',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
        }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', cursor: 'pointer' }} onClick={() => navigate('/search')}>
                🔐 CVE Database
            </div>

            <div style={{ flex: 1, marginLeft: '2rem' }}>
                <input
                    type="text"
                    placeholder="Search CVE..."
                    style={{
                        width: '300px',
                        padding: '0.75rem',
                        borderRadius: '4px',
                        border: 'none',
                        backgroundColor: '#333',
                        color: 'white',
                    }}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                            navigate(`/search?q=${e.target.value}`);
                        }
                    }}
                />
            </div>

            <div style={{ position: 'relative' }}>
                {isAuthenticated ? (
                    <div>
                        <button
                            onClick={() => setShowDropdown(!showDropdown)}
                            style={{
                                backgroundColor: 'transparent',
                                border: 'none',
                                color: 'white',
                                cursor: 'pointer',
                                fontSize: '1rem',
                            }}
                        >
                            {user?.email} ▼
                        </button>

                        {showDropdown && (
                            <div style={{
                                position: 'absolute',
                                top: '100%',
                                right: 0,
                                backgroundColor: '#333',
                                borderRadius: '4px',
                                boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
                                minWidth: '150px',
                                zIndex: 1000,
                            }}>
                                <button onClick={() => navigate('/dashboard')} style={{
                                    display: 'block',
                                    width: '100%',
                                    padding: '0.75rem',
                                    backgroundColor: 'transparent',
                                    border: 'none',
                                    color: 'white',
                                    cursor: 'pointer',
                                    textAlign: 'left',
                                }}>
                                    📊 Dashboard
                                </button>
                                <button onClick={logout} style={{
                                    display: 'block',
                                    width: '100%',
                                    padding: '0.75rem',
                                    backgroundColor: 'transparent',
                                    border: 'none',
                                    color: '#ff6b6b',
                                    cursor: 'pointer',
                                    textAlign: 'left',
                                }}>
                                    Logout
                                </button>
                            </div>
                        )}
                    </div>
                ) : (
                    <div>
                        <button onClick={() => navigate('/login')} style={{
                            marginRight: '1rem',
                            padding: '0.75rem 1.5rem',
                            backgroundColor: '#007bff',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                        }}>
                            Login
                        </button>
                        <button onClick={() => navigate('/register')} style={{
                            padding: '0.75rem 1.5rem',
                            backgroundColor: '#28a745',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                        }}>
                            Register
                        </button>
                    </div>
                )}
            </div>
        </nav>
    );
};

export default Navbar;
