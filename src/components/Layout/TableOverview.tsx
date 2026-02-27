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
                            <DataGrid columns={getColumns(properties)} data={properties} />
                        ) : (
                            <p className={styles.emptyText}>No properties found.</p>
                        )}
                    </section>

                    <section className={styles.section}>
                        <h2>Iceberg Snapshots</h2>
                        {snapshots.length > 0 ? (
                            <DataGrid columns={getColumns(snapshots)} data={snapshots} />
                        ) : (
                            <p className={styles.emptyText}>No snapshots found.</p>
                        )}
                    </section>

                    <section className={styles.section}>
                        <h2>Iceberg Partitions</h2>
                        {flattenedPartitions.length > 0 ? (
                            <DataGrid columns={getColumns(flattenedPartitions)} data={flattenedPartitions} />
                        ) : (
                            <p className={styles.emptyText}>No partitions found.</p>
                        )}
                    </section>

                    <section className={styles.section}>
                        <h2>Iceberg Files</h2>
                        {files.length > 0 ? (
                            <DataGrid columns={getColumns(files)} data={files} />
                        ) : (
                            <p className={styles.emptyText}>No files found.</p>
                        )}
                    </section>
                </div>
            </div>
        </div>
    );
};
