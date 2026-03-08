import React, { useState, useEffect } from 'react';
import { X, ChevronDown, ChevronRight } from 'lucide-react';
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

const SkeletonMetric = () => (
    <div className={`${styles.skeletonLoader} ${styles.skeletonMetric}`}></div>
);

const SkeletonGrid = () => (
    <div className={styles.gridWrapper}>
        <div className={`${styles.skeletonLoader} ${styles.skeletonGrid}`}></div>
    </div>
);

export const TableOverview: React.FC<TableOverviewProps> = ({ catalog, namespace, table, onClose }) => {
    const [error, setError] = useState<string | null>(null);
    const [schemaExpanded, setSchemaExpanded] = useState(true);

    const [schema, setSchema] = useState<any>(null);
    const [properties, setProperties] = useState<any>(null);
    const [snapshots, setSnapshots] = useState<any>(null);
    const [partitions, setPartitions] = useState<any>(null);
    const [files, setFiles] = useState<any>(null);
    const [metrics, setMetrics] = useState<any>(null);

    const [loadingSchema, setLoadingSchema] = useState(true);
    const [loadingProperties, setLoadingProperties] = useState(true);
    const [loadingSnapshots, setLoadingSnapshots] = useState(true);
    const [loadingPartitions, setLoadingPartitions] = useState(true);
    const [loadingFiles, setLoadingFiles] = useState(true);
    const [loadingMetrics, setLoadingMetrics] = useState(true);

    useEffect(() => {
        setLoadingSchema(true);
        setLoadingProperties(true);
        setLoadingSnapshots(true);
        setLoadingPartitions(true);
        setLoadingFiles(true);
        setLoadingMetrics(true);
        setError(null);

        api.getTableSchema(catalog, namespace, table)
            .then(setSchema).catch(err => setError(err.message))
            .finally(() => setLoadingSchema(false));

        api.getTableProperties(catalog, namespace, table)
            .then(setProperties).catch(err => setError(err.message))
            .finally(() => setLoadingProperties(false));

        api.getTableSnapshots(catalog, namespace, table)
            .then(setSnapshots).catch(err => setError(err.message))
            .finally(() => setLoadingSnapshots(false));

        api.getTablePartitions(catalog, namespace, table)
            .then(setPartitions).catch(err => setError(err.message))
            .finally(() => setLoadingPartitions(false));

        api.getTableFiles(catalog, namespace, table)
            .then(setFiles).catch(err => setError(err.message))
            .finally(() => setLoadingFiles(false));

        api.getTableMetrics(catalog, namespace, table)
            .then(setMetrics).catch(err => setError(err.message))
            .finally(() => setLoadingMetrics(false));

    }, [catalog, namespace, table]);

    // Helper to get columns for DataGrid
    const getColumns = (data: any[]) => {
        if (!data || data.length === 0) return [];
        return Object.keys(data[0]).map(key => ({ name: key, type: typeof data[0][key] }));
    };

    // Flatten partitions for display
    const flattenedPartitions = partitions?.map((p: any) => {
        const { partition, ...rest } = p;
        if (partition && typeof partition === 'object') {
            return { ...rest, ...partition };
        }
        return p;
    }) || [];

    return (
        <div className={styles.overlay}>
            <div className={styles.modal}>
                <div className={styles.header}>
                    <div className={styles.titleGroup}>
                        <h1>Table Overview</h1>
                        <span className={styles.tableName}>{catalog}.{namespace}.{table}</span>
                    </div>
                    <button onClick={onClose} className={styles.closeButton}><X size={20} /></button>
                </div>

                <div className={styles.content}>
                    {error && (
                        <div className={styles.errorText}>
                            <strong>Error loading some data:</strong> {error}
                        </div>
                    )}

                    <section className={styles.metricsSection}>
                        <div className={styles.metricsGrid}>
                            <div className={styles.metricCard}>
                                <span className={styles.metricLabel}>Last Snapshot Date</span>
                                {loadingMetrics ? <SkeletonMetric /> : <span className={styles.metricValue}>{metrics?.last_snapshot || 'N/A'}</span>}
                            </div>
                            <div className={styles.metricCard}>
                                <span className={styles.metricLabel}>Earliest Snapshot Date</span>
                                {loadingMetrics ? <SkeletonMetric /> : <span className={styles.metricValue}>{metrics?.earliest_snapshot || 'N/A'}</span>}
                            </div>
                            <div className={styles.metricCard}>
                                <span className={styles.metricLabel}>Number of Rows</span>
                                {loadingMetrics ? <SkeletonMetric /> : <span className={styles.metricValue}>{metrics?.row_count || 'N/A'}</span>}
                            </div>
                            <div className={styles.metricCard}>
                                <span className={styles.metricLabel}>Number of Columns</span>
                                {loadingMetrics ? <SkeletonMetric /> : <span className={styles.metricValue}>{metrics?.column_count || 'N/A'}</span>}
                            </div>
                            <div className={styles.metricCard}>
                                <span className={styles.metricLabel}>Average File Size</span>
                                {loadingMetrics ? <SkeletonMetric /> : <span className={styles.metricValue}>{metrics?.avg_file_size || 'N/A'}</span>}
                            </div>
                            <div className={styles.metricCard}>
                                <span className={styles.metricLabel}>Partition Columns</span>
                                {loadingMetrics ? <SkeletonMetric /> : <span className={styles.metricValue}>{metrics?.partition_columns || 'N/A'}</span>}
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
                                {loadingSchema ? <SkeletonGrid /> : <JsonView data={schema} />}
                            </div>
                        )}
                    </section>

                    <section className={styles.section}>
                        <h2>Table Properties</h2>
                        {loadingProperties ? <SkeletonGrid /> : (
                            properties?.length > 0 ? (
                                <div className={styles.gridWrapper}>
                                    <DataGrid columns={getColumns(properties)} data={properties} />
                                </div>
                            ) : (
                                <p className={styles.emptyText}>No properties found.</p>
                            )
                        )}
                    </section>

                    <section className={styles.section}>
                        <h2>Iceberg Snapshots</h2>
                        {loadingSnapshots ? <SkeletonGrid /> : (
                            snapshots?.length > 0 ? (
                                <div className={styles.gridWrapper}>
                                    <DataGrid columns={getColumns(snapshots)} data={snapshots} />
                                </div>
                            ) : (
                                <p className={styles.emptyText}>No snapshots found.</p>
                            )
                        )}
                    </section>

                    <section className={styles.section}>
                        <h2>Iceberg Partitions</h2>
                        {loadingPartitions ? <SkeletonGrid /> : (
                            flattenedPartitions.length > 0 ? (
                                <div className={styles.gridWrapper}>
                                    <DataGrid columns={getColumns(flattenedPartitions)} data={flattenedPartitions} />
                                </div>
                            ) : (
                                <p className={styles.emptyText}>No partitions found.</p>
                            )
                        )}
                    </section>

                    <section className={styles.section}>
                        <h2>Iceberg Files</h2>
                        {loadingFiles ? <SkeletonGrid /> : (
                            files?.length > 0 ? (
                                <div className={styles.gridWrapper}>
                                    <DataGrid columns={getColumns(files)} data={files} />
                                </div>
                            ) : (
                                <p className={styles.emptyText}>No files found.</p>
                            )
                        )}
                    </section>
                </div>
            </div>
        </div>
    );
};
