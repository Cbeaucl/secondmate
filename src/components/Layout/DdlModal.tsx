import React, { useState, useEffect } from 'react';
import { X, Copy, Check, Loader2 } from 'lucide-react';
import Editor, { type OnMount } from '@monaco-editor/react';
import { api } from '../../services/api';
import styles from './DdlModal.module.css';

interface DdlModalProps {
    catalog: string;
    namespace: string;
    table: string;
    onClose: () => void;
}

export const DdlModal: React.FC<DdlModalProps> = ({ catalog, namespace, table, onClose }) => {
    const [ddl, setDdl] = useState<string>('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        const fetchDdl = async () => {
            setLoading(true);
            setError(null);
            try {
                const data = await api.getTableDdl(catalog, namespace, table);
                setDdl(data.ddl);
            } catch (err: unknown) {
                setError(err instanceof Error ? err.message : 'Failed to fetch DDL');
            } finally {
                setLoading(false);
            }
        };

        fetchDdl();
    }, [catalog, namespace, table]);

    const handleCopy = () => {
        navigator.clipboard.writeText(ddl);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleEditorDidMount: OnMount = (_editor, monaco) => {
        monaco.editor.setTheme('spark-dark');
    };

    return (
        <div className={styles.overlay}>
            <div className={styles.modal}>
                <div className={styles.header}>
                    <div className={styles.titleGroup}>
                        <h1>Table DDL</h1>
                        <span className={styles.tableName}>{catalog}.{namespace}.{table}</span>
                    </div>
                    <div className={styles.headerActions}>
                        <button
                            className={styles.copyButton}
                            onClick={handleCopy}
                            disabled={loading || !!error}
                            title="Copy DDL"
                        >
                            {copied ? <Check size={16} /> : <Copy size={16} />}
                            <span>{copied ? 'Copied' : 'Copy'}</span>
                        </button>
                        <button onClick={onClose} className={styles.closeButton}><X size={20} /></button>
                    </div>
                </div>

                <div className={styles.content}>
                    {loading ? (
                        <div className={styles.loader}>
                            <Loader2 size={32} className={styles.spinner} />
                            <p>Generating DDL...</p>
                        </div>
                    ) : error ? (
                        <div className={styles.error}>
                            <p><strong>Error:</strong> {error}</p>
                        </div>
                    ) : (
                        <div className={styles.editorWrapper}>
                            <Editor
                                height="100%"
                                defaultLanguage="sql"
                                value={ddl}
                                onMount={handleEditorDidMount}
                                options={{
                                    readOnly: true,
                                    minimap: { enabled: false },
                                    fontSize: 14,
                                    fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                                    scrollBeyondLastLine: false,
                                    automaticLayout: true,
                                    wordWrap: 'on',
                                    padding: { top: 16, bottom: 16 }
                                }}
                            />
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
