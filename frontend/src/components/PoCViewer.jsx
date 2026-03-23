import React, { useState } from 'react';
import DOMPurify from 'dompurify';

/**
 * Component to display PoC code with security warning
 */
export const PoCViewer = ({ pocCode, pocLanguage = 'bash' }) => {
    const [showCode, setShowCode] = useState(false);
    const [disclaimerAccepted, setDisclaimerAccepted] = useState(false);

    // Sanitize code to prevent XSS
    const sanitized = DOMPurify.sanitize(pocCode, {
        ALLOWED_TAGS: [],
        ALLOWED_ATTR: [],
    });

    const handleShowCode = () => {
        if (disclaimerAccepted) {
            setShowCode(true);
        }
    };

    const handleCopyCode = () => {
        navigator.clipboard.writeText(sanitized);
        alert('Code copied to clipboard');
    };

    return (
        <div className="poc-viewer">
            <div style={{
                backgroundColor: '#fff3cd',
                border: '1px solid #ffc107',
                borderRadius: '4px',
                padding: '12px',
                marginBottom: '12px',
                color: '#856404',
            }}>
                <strong>⚠️ Security Warning:</strong> This is exploit code. Use only in authorized environments for testing purposes only. Unauthorized access to computer systems is illegal.
            </div>

            {!showCode ? (
                <div>
                    <div style={{
                        marginBottom: '12px',
                        padding: '12px',
                        backgroundColor: '#f8f9fa',
                        borderRadius: '4px',
                    }}>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <input
                                type="checkbox"
                                checked={disclaimerAccepted}
                                onChange={(e) => setDisclaimerAccepted(e.target.checked)}
                            />
                            <span>I understand the risks and accept full responsibility for using this code</span>
                        </label>
                    </div>

                    <button
                        onClick={handleShowCode}
                        disabled={!disclaimerAccepted}
                        style={{
                            padding: '8px 16px',
                            backgroundColor: disclaimerAccepted ? '#dc3545' : '#ccc',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: disclaimerAccepted ? 'pointer' : 'not-allowed',
                        }}
                    >
                        Show Exploit Code
                    </button>
                </div>
            ) : (
                <div>
                    <div style={{
                        backgroundColor: '#282c34',
                        color: '#abb2bf',
                        padding: '12px',
                        borderRadius: '4px',
                        marginBottom: '12px',
                        maxHeight: '400px',
                        overflowY: 'auto',
                        fontFamily: 'monospace',
                        fontSize: '12px',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                    }}>
                        {sanitized}
                    </div>

                    <button
                        onClick={handleCopyCode}
                        style={{
                            padding: '8px 16px',
                            backgroundColor: '#28a745',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                        }}
                    >
                        Copy Code
                    </button>

                    <button
                        onClick={() => setShowCode(false)}
                        style={{
                            marginLeft: '8px',
                            padding: '8px 16px',
                            backgroundColor: '#6c757d',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                        }}
                    >
                        Hide Code
                    </button>
                </div>
            )}
        </div>
    );
};

export default PoCViewer;
