import React, { useState, useEffect } from 'react';
import { X, ChevronDown, ChevronRight, Loader2 } from 'lucide-react';
import { JsonView } from '../Results/JsonView';
import { DataGrid } from '../Results/DataGrid';
import { api } from '../../services/api';
import styles from './TableOverview.module.css';

interface TableOverviewProps {
    catalog: string;
    namespace: string;
    table: string;
    onClose: () => void;
}

export const TableOverview: React.FC<TableOverviewProps> = ({ catalog, namespace, table, onClose }) => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [overviewData, setOverviewData] = useState<any>(null);
    const [schemaExpanded, setSchemaExpanded] = useState(true);

    useEffect(() => {
        const fetchOverview = async () => {
            setLoading(true);
            try {
                const data = await api.getTableOverview(catalog, namespace, table);
                setOverviewData(data);
            } catch (err: any) {
                setError(err.message || 'Failed to fetch table overview');
            } finally {
                setLoading(false);
            }
        };

        fetchOverview();
    }, [catalog, namespace, table]);

    if (loading) {
        return (
            <div className={styles.overlay}>
                <div className={styles.modal}>
                    <div className={styles.loadingContainer}>
                        <Loader2 className={styles.spinner} />
                        <span>Loading Table Overview...</span>
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className={styles.overlay}>
                <div className={styles.modal}>
                    <div className={styles.header}>
                        <h2>Error</h2>
                        <button onClick={onClose} className={styles.closeButton}><X size={20} /></button>
                    </div>
                    <div className={styles.content}>
                        <p className={styles.errorText}>{error}</p>
                    </div>
                </div>
            </div>
        );
    }

    const { tableName, schema, properties, snapshots, partitions, files } = overviewData;

    // Helper to get columns for DataGrid
    const getColumns = (data: any[]) => {
        if (!data || data.length === 0) return [];
        return Object.keys(data[0]).map(key => ({ name: key, type: typeof data[0][key] }));
    };

    // Flatten partitions for display
    const flattenedPartitions = partitions.map((p: any) => {
        const { partition, ...rest } = p;
        if (partition && typeof partition === 'object') {
            return { ...rest, ...partition };
        }
        return p;
    });

    // Calculate Metrics
    const lastSnapshot = snapshots.length > 0 ? new Date(snapshots[0].committed_at).toLocaleString() : 'N/A';
    const earliestSnapshot = snapshots.length > 0 ? new Date(snapshots[snapshots.length - 1].committed_at).toLocaleString() : 'N/A';

    let rowCount = 'N/A';
    if (snapshots.length > 0 && snapshots[0].summary && snapshots[0].summary['total-records']) {
        rowCount = parseInt(snapshots[0].summary['total-records']).toLocaleString();
    } else if (files.length > 0) {
        const total = files.reduce((acc: number, f: any) => acc + (f.record_count || 0), 0);
        rowCount = total.toLocaleString();
    }

    const columnCount = schema?.fields ? schema.fields.length.toString() : 'N/A';

    let avgFileSize = 'N/A';
    if (files.length > 0) {
        const totalSize = files.reduce((acc: number, f: any) => acc + (f.file_size_mb || 0), 0);
        avgFileSize = (totalSize / files.length).toFixed(2) + ' MB';
    }

    let partitionColumns = 'N/A';
    if (partitions.length > 0 && partitions[0].partition && typeof partitions[0].partition === 'object') {
        const keys = Object.keys(partitions[0].partition);
        if (keys.length > 0) {
            partitionColumns = keys.join(', ');
        }
    }

    return (
        <div className={styles.overlay}>
            <div className={styles.modal}>
                <div className={styles.header}>
                    <div className={styles.titleGroup}>
                        <h1>Table Overview</h1>
                        <span className={styles.tableName}>{tableName}</span>
                    </div>
                    <button onClick={onClose} className={styles.closeButton}><X size={20} /></button>
                </div>

                <div className={styles.content}>
                    <section className={styles.metricsSection}>
                        <div className={styles.metricsGrid}>
                            <div className={styles.metricCard}>
                                <span className={styles.metricLabel}>Last Snapshot Date</span>
                                <span className={styles.metricValue}>{lastSnapshot}</span>
                            </div>
                            <div className={styles.metricCard}>
                                <span className={styles.metricLabel}>Earliest Snapshot Date</span>
                                <span className={styles.metricValue}>{earliestSnapshot}</span>
                            </div>
                            <div className={styles.metricCard}>
                                <span className={styles.metricLabel}>Number of Rows</span>
                                <span className={styles.metricValue}>{rowCount}</span>
                            </div>
                            <div className={styles.metricCard}>
                                <span className={styles.metricLabel}>Number of Columns</span>
                                <span className={styles.metricValue}>{columnCount}</span>
                            </div>
                            <div className={styles.metricCard}>
                                <span className={styles.metricLabel}>Average File Size</span>
                                <span className={styles.metricValue}>{avgFileSize}</span>
                            </div>
                            <div className={styles.metricCard}>
                                <span className={styles.metricLabel}>Partition Columns</span>
                                <span className={styles.metricValue}>{partitionColumns}</span>
                            </div>
                        </div>
                    </section>

                    <section className={styles.section}>
                        <div className={styles.sectionHeader} onClick={() => setSchemaExpanded(!schemaExpanded)}>
                            {schemaExpanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                            <h2>Schema</h2>
                        </div>
                        {schemaExpanded && (
                            <div className={styles.jsonWrapper}>
                                <JsonView data={schema} />
                            </div>
                        )}
                    </section>

                    <section className={styles.section}>
                        <h2>Table Properties</h2>
                        {properties.length > 0 ? (
                            <div className={styles.gridWrapper}>
                                <DataGrid columns={getColumns(properties)} data={properties} />
                            </div>
                        ) : (
                            <p className={styles.emptyText}>No properties found.</p>
                        )}
                    </section>

                    <section className={styles.section}>
                        <h2>Iceberg Snapshots</h2>
                        {snapshots.length > 0 ? (
                            <div className={styles.gridWrapper}>
                                <DataGrid columns={getColumns(snapshots)} data={snapshots} />
                            </div>
                        ) : (
                            <p className={styles.emptyText}>No snapshots found.</p>
                        )}
                    </section>

                    <section className={styles.section}>
                        <h2>Iceberg Partitions</h2>
                        {flattenedPartitions.length > 0 ? (
                            <div className={styles.gridWrapper}>
                                <DataGrid columns={getColumns(flattenedPartitions)} data={flattenedPartitions} />
                            </div>
                        ) : (
                            <p className={styles.emptyText}>No partitions found.</p>
                        )}
                    </section>

                    <section className={styles.section}>
                        <h2>Iceberg Files</h2>
                        {files.length > 0 ? (
                            <div className={styles.gridWrapper}>
                                <DataGrid columns={getColumns(files)} data={files} />
                            </div>
                        ) : (
                            <p className={styles.emptyText}>No files found.</p>
                        )}
                    </section>
                </div>
            </div>
        </div>
    );
};
