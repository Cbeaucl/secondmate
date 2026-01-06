// Workspace.tsx
import React, { useState, useRef } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { SqlEditor } from '../Editor/SqlEditor';
import { DataGrid } from '../Results/DataGrid';
import { SteamboatLoader } from '../SteamboatLoader';
import { Play } from 'lucide-react';
import styles from './Workspace.module.css';
import { api, type QueryResult } from '../../services/api';

export const Workspace: React.FC = () => {
    const [query, setQuery] = useState('-- Write your SparkSQL here\nSELECT * FROM user.sales.transactions LIMIT 100;');
    const [result, setResult] = useState<QueryResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [hasRun, setHasRun] = useState(false);

    const handleRunQuery = async () => {
        if (!query.trim()) return;
        setLoading(true);
        setHasRun(true);
        setResult(null);
        try {
            const data = await api.executeQuery(query);
            setResult(data);
        } catch (err) {
            setResult({ error: err instanceof Error ? err.message : 'An error occurred' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.workspace}>
            <div className={styles.toolbar}>
                <button
                    className={`${styles.runButton} ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                    onClick={handleRunQuery}
                    disabled={loading}
                >
                    <Play size={14} fill="currentColor" />
                    <span>{loading ? 'Running...' : 'Run'}</span>
                </button>
                <div className={styles.divider} />
                <span className={styles.tabTitle}>Query 1.sql</span>
            </div>

            <div className={styles.content}>
                <PanelGroup direction="vertical">
                    <Panel defaultSize={50} minSize={20}>
                        <SqlEditor
                            initialValue={query}
                            onChange={(val) => setQuery(val || '')}
                            onRunQuery={handleRunQuery}
                        />
                    </Panel>
                    <PanelResizeHandle className={styles.resizeHandle} />
                    <Panel defaultSize={50} minSize={20}>
                        <div className={styles.resultsArea}>
                            <div className={styles.resultsHeader}>
                                <span>Query Results</span>
                                {result?.data && (
                                    <span className={styles.meta}>
                                        {result.data.length} rows retrieved
                                    </span>
                                )}
                            </div>

                            {!hasRun && (
                                <div className={styles.emptyState}>
                                    <div className={styles.emptyStateHeader}>
                                        🫡Welcome Aboard Matey!
                                    </div>
                                    <div className={styles.emptyStateMain}>
                                        Welcome To Secondmate! Get started by entering your query above.
                                    </div>
                                </div>
                            )}

                            {loading && (
                                <SteamboatLoader />
                            )}

                            {hasRun && !loading && result?.error && (
                                <div className="p-4 text-red-600 bg-red-50 border-l-4 border-red-500 m-4">
                                    <h3 className="font-bold">Error</h3>
                                    <p>{result.error}</p>
                                </div>
                            )}

                            {hasRun && !loading && result?.data && result.schema && (
                                <DataGrid columns={result.schema} data={result.data} />
                            )}
                        </div>
                    </Panel>
                </PanelGroup>
            </div>
        </div>
    );
};
