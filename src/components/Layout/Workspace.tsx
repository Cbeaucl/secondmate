// Workspace.tsx
import React, { useState, useRef } from 'react';
import { Panel, PanelGroup, PanelResizeHandle, type ImperativePanelHandle } from 'react-resizable-panels';
import { SqlEditor } from '../Editor/SqlEditor';
import { DataGrid } from '../Results/DataGrid';
import { JsonView } from '../Results/JsonView';
import { SteamboatLoader } from '../SteamboatLoader';
import { Play, Table, FileJson, History } from 'lucide-react';
import styles from './Workspace.module.css';
import { api, type QueryResult } from '../../services/api';
import { useQueryHistory } from '../../hooks/useQueryHistory';
import { QueryHistory } from '../History/QueryHistory';

export const Workspace: React.FC = () => {
    const [query, setQuery] = useState('-- Write your SparkSQL here\nSELECT * FROM user.sales.transactions LIMIT 100;');
    const [result, setResult] = useState<QueryResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [hasRun, setHasRun] = useState(false);
    const [viewMode, setViewMode] = useState<'table' | 'json'>('table');
    const [isHistoryOpen, setIsHistoryOpen] = useState(false);

    const historyPanelRef = useRef<ImperativePanelHandle>(null);
    const { history, addEntry, clearHistory } = useQueryHistory();

    const handleRunQuery = async () => {
        if (!query.trim()) return;
        setLoading(true);
        setHasRun(true);
        setResult(null);

        // Add to history
        addEntry(query);

        try {
            const data = await api.executeQuery(query);
            setResult(data);
        } catch (err) {
            setResult({ error: err instanceof Error ? err.message : 'An error occurred' });
        } finally {
            setLoading(false);
        }
    };

    const toggleHistory = () => {
        const panel = historyPanelRef.current;
        if (panel) {
            if (panel.isCollapsed()) {
                panel.expand();
            } else {
                panel.collapse();
            }
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

                <button
                    className={`${styles.historyToggleButton} ${isHistoryOpen ? styles.historyToggleButtonActive : ''}`}
                    onClick={toggleHistory}
                    title="Toggle Query History"
                >
                    <History size={14} />
                    <span>History</span>
                </button>
            </div>

            <div className={styles.content}>
                <PanelGroup direction="horizontal">
                    <Panel minSize={30}>
                        <PanelGroup direction="vertical">
                            <Panel defaultSize={50} minSize={20}>
                                <SqlEditor
                                    value={query}
                                    onChange={(val) => setQuery(val || '')}
                                    onRunQuery={handleRunQuery}
                                />
                            </Panel>
                            <PanelResizeHandle className={styles.resizeHandle} />
                            <Panel defaultSize={50} minSize={20}>
                                <div className={styles.resultsArea}>
                                    <div className={styles.resultsHeader}>
                                        <div className={styles.headerLeft}>
                                            <span>Query Results</span>
                                            {result?.data && (
                                                <div className={styles.viewToggle}>
                                                    <button
                                                        className={`${styles.toggleButton} ${viewMode === 'table' ? styles.toggleButtonActive : ''}`}
                                                        onClick={() => setViewMode('table')}
                                                        title="Table View"
                                                    >
                                                        <Table size={12} />
                                                        <span>Table</span>
                                                    </button>
                                                    <button
                                                        className={`${styles.toggleButton} ${viewMode === 'json' ? styles.toggleButtonActive : ''}`}
                                                        onClick={() => setViewMode('json')}
                                                        title="JSON View"
                                                    >
                                                        <FileJson size={12} />
                                                        <span>JSON</span>
                                                    </button>
                                                </div>
                                            )}
                                        </div>
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
                                        viewMode === 'table' ? (
                                            <DataGrid columns={result.schema} data={result.data} />
                                        ) : (
                                            <JsonView data={result.data} />
                                        )
                                    )}
                                </div>
                            </Panel>
                        </PanelGroup>
                    </Panel>

                    {isHistoryOpen && <PanelResizeHandle className={styles.resizeHandleHorizontal} />}

                    <Panel
                        ref={historyPanelRef}
                        defaultSize={0}
                        minSize={20}
                        maxSize={40}
                        collapsible={true}
                        onCollapse={() => setIsHistoryOpen(false)}
                        onExpand={() => setIsHistoryOpen(true)}
                    >
                        <QueryHistory
                            history={history}
                            onSelectQuery={(q) => setQuery(q)}
                            onClearHistory={clearHistory}
                            onClose={() => historyPanelRef.current?.collapse()}
                        />
                    </Panel>
                </PanelGroup>
            </div>
        </div>
    );
};
