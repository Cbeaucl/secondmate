// Workspace.tsx
import React, { useState, useRef, useEffect } from 'react';
import { Panel, PanelGroup, PanelResizeHandle, type ImperativePanelHandle } from 'react-resizable-panels';
import { SqlEditor } from '../Editor/SqlEditor';
import { DataGrid } from '../Results/DataGrid';
import { JsonView } from '../Results/JsonView';
import { SteamboatLoader } from '../SteamboatLoader';
import { Play, Table, FileJson, History, Settings, AlertTriangle } from 'lucide-react';
import styles from './Workspace.module.css';
import { api, type QueryResult, type ConfigOption } from '../../services/api';
import { useJobQueue } from '../../hooks/useJobQueue';
import { QueryHistory } from '../History/QueryHistory';
import { ConfigModal } from '../Editor/ConfigModal';
import logoUrl from '../../assets/logo.png';

export const Workspace: React.FC = () => {
    const [query, setQuery] = useState('-- Write your SparkSQL here\nSELECT * FROM user.sales.transactions LIMIT 100;');
    const [viewMode, setViewMode] = useState<'table' | 'json'>('table');
    const [isHistoryOpen, setIsHistoryOpen] = useState(false);

    const [configs, setConfigs] = useState<ConfigOption[]>([]);
    const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);

    const historyPanelRef = useRef<ImperativePanelHandle>(null);
    const { jobs, selectedJob, selectedJobResult, isLoadingResult, submitJob, selectJob } = useJobQueue();

    const fetchConfigs = async () => {
        try {
            const data = await api.getConfigs();
            setConfigs(data);
        } catch (err) {
            console.error('Failed to fetch configs', err);
        }
    };

    useEffect(() => {
        fetchConfigs();
    }, []);

    const missingRequiredConfigs = configs.filter(c =>
        c.is_required && (c.current_value === null || c.current_value === '')
    );

    const handleRunQuery = async () => {
        if (!query.trim()) return;
        await submitJob(query);

        // Open the history panel if closed
        const panel = historyPanelRef.current;
        if (panel && panel.isCollapsed()) {
            panel.expand();
        }
    };

    const handleSelectJob = (job: typeof selectedJob extends infer T ? NonNullable<T> : never) => {
        // Populate editor with the job's query
        setQuery(job.query_text);
        selectJob(job);
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

    // Determine what to show in the result area
    const isJobActive = selectedJob && (selectedJob.status === 'queued' || selectedJob.status === 'running');
    const isJobFailed = selectedJob && selectedJob.status === 'failed';
    const isJobSucceeded = selectedJob && selectedJob.status === 'succeeded';
    const hasResults = isJobSucceeded && selectedJobResult?.data && selectedJobResult?.schema;

    return (
        <div className={styles.workspace}>
            <div className={styles.toolbar}>
                <button
                    className={`${styles.runButton} ${missingRequiredConfigs.length > 0 ? styles.runButtonWarning : ''}`}
                    onClick={handleRunQuery}
                    disabled={missingRequiredConfigs.length > 0}
                    title={missingRequiredConfigs.length > 0 ? "Missing required configurations. Please update settings before running." : ""}
                >
                    {missingRequiredConfigs.length > 0 ? (
                        <AlertTriangle size={14} className="text-yellow-500" />
                    ) : (
                        <Play size={14} fill="currentColor" />
                    )}
                    <span>Run</span>
                </button>

                {configs.length > 0 && (
                    <button
                        className={styles.configButton}
                        onClick={() => setIsConfigModalOpen(true)}
                        title="Configure Spark Settings"
                    >
                        <Settings size={14} />
                    </button>
                )}

                <button
                    className={`${styles.historyToggleButton} ${isHistoryOpen ? styles.historyToggleButtonActive : ''}`}
                    onClick={toggleHistory}
                    title="Toggle Query Queue"
                >
                    <History size={14} />
                    <span>Queue</span>
                </button>
            </div>

            <ConfigModal
                isOpen={isConfigModalOpen}
                onClose={() => setIsConfigModalOpen(false)}
                configs={configs}
                onSaved={fetchConfigs}
            />

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
                                            {hasResults && (
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
                                        {hasResults && selectedJobResult?.data && (
                                            <span className={styles.meta}>
                                                {selectedJobResult.data.length} rows retrieved
                                            </span>
                                        )}
                                    </div>

                                    {/* No job selected — welcome state */}
                                    {!selectedJob && (
                                        <div className={styles.emptyState}>
                                            <img src={logoUrl} alt="SecondMate Logo" style={{ maxWidth: '400px', width: '100%', marginBottom: '1rem', objectFit: 'contain' }} />
                                            <div className={styles.emptyStateMain}>
                                                Welcome To Secondmate! Get started by entering your query above.
                                            </div>
                                        </div>
                                    )}

                                    {/* Queued or Running state */}
                                    {(isJobActive || isLoadingResult) && (
                                        <SteamboatLoader />
                                    )}

                                    {/* Failed state */}
                                    {isJobFailed && selectedJobResult?.error && (
                                        <div className={styles.errorContainer}>
                                            <h3 className={styles.errorHeading}>Error</h3>
                                            <pre className={styles.errorText}>{selectedJobResult.error}</pre>
                                        </div>
                                    )}

                                    {/* Succeeded state */}
                                    {hasResults && !isLoadingResult && (
                                        viewMode === 'table' ? (
                                            <DataGrid columns={selectedJobResult!.schema!} data={selectedJobResult!.data!} />
                                        ) : (
                                            <JsonView data={selectedJobResult!.data!} />
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
                            jobs={jobs}
                            selectedJobId={selectedJob?.job_id ?? null}
                            onSelectJob={handleSelectJob}
                            onClose={() => historyPanelRef.current?.collapse()}
                        />
                    </Panel>
                </PanelGroup>
            </div>
        </div>
    );
};
