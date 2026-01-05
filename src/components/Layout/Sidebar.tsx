import React, { useEffect, useState } from 'react';
import { Database, Table, Folder, ChevronRight, ChevronDown, Search, Loader2 } from 'lucide-react';
import styles from './Sidebar.module.css';
import { api } from '../../services/api';

interface TreeNodeProps {
    label: string;
    type: 'catalog' | 'namespace' | 'table';
    children?: React.ReactNode;
    isExpanded?: boolean;
    onToggle?: () => void;
    isLoading?: boolean;
}

const TreeNode: React.FC<TreeNodeProps> = ({ label, type, children, isExpanded, onToggle, isLoading }) => {
    const Icon = type === 'catalog' ? Database : type === 'namespace' ? Folder : Table;
    const color = type === 'catalog' ? '#38bdf8' : type === 'namespace' ? '#fbbf24' : '#a78bfa';

    return (
        <div className={styles.treeItem}>
            <div className={styles.treeRow} onClick={onToggle} style={{ cursor: 'pointer' }}>
                {type !== 'table' && (
                    <div style={{ width: 16, display: 'flex', alignItems: 'center' }}>
                        {isLoading ? <Loader2 size={12} className={styles.spinner} /> :
                            isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    </div>
                )}
                {type === 'table' && <div style={{ width: 16 }} />}
                <Icon size={14} className={styles.icon} color={color} />
                <span className="truncate">{label}</span>
            </div>
            {isExpanded && children && <div className={styles.treeChildren}>{children}</div>}
        </div>
    );
};

export const Sidebar: React.FC = () => {
    const [catalogs, setCatalogs] = useState<string[]>([]);
    const [expandedCatalogs, setExpandedCatalogs] = useState<Record<string, boolean>>({});
    const [namespaces, setNamespaces] = useState<Record<string, string[]>>({});
    const [expandedNamespaces, setExpandedNamespaces] = useState<Record<string, boolean>>({}); // key: catalog.namespace
    const [tables, setTables] = useState<Record<string, string[]>>({}); // key: catalog.namespace
    const [loading, setLoading] = useState<Record<string, boolean>>({}); // key: node id

    useEffect(() => {
        loadCatalogs();
    }, []);

    const loadCatalogs = async () => {
        try {
            const data = await api.getCatalogs();
            setCatalogs(data);
        } catch (err) {
            console.error(err);
        }
    };

    const toggleCatalog = async (catalog: string) => {
        const isExpanded = !expandedCatalogs[catalog];
        setExpandedCatalogs(prev => ({ ...prev, [catalog]: isExpanded }));

        if (isExpanded && !namespaces[catalog]) {
            setLoading(prev => ({ ...prev, [catalog]: true }));
            try {
                const data = await api.getNamespaces(catalog);
                setNamespaces(prev => ({ ...prev, [catalog]: data }));
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(prev => ({ ...prev, [catalog]: false }));
            }
        }
    };

    const toggleNamespace = async (catalog: string, namespace: string) => {
        const key = `${catalog}.${namespace}`;
        const isExpanded = !expandedNamespaces[key];
        setExpandedNamespaces(prev => ({ ...prev, [key]: isExpanded }));

        if (isExpanded && !tables[key]) {
            setLoading(prev => ({ ...prev, [key]: true }));
            try {
                const data = await api.getTables(catalog, namespace);
                setTables(prev => ({ ...prev, [key]: data }));
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(prev => ({ ...prev, [key]: false }));
            }
        }
    };

    return (
        <div className={styles.sidebar}>
            <div className={styles.header}>
                <div className={styles.title}>Connections</div>
                <div className={styles.actions}>
                    <button className={styles.iconButton} title="New Connection">+</button>
                </div>
            </div>

            <div className={styles.searchBox}>
                <Search size={14} className={styles.searchIcon} />
                <input type="text" placeholder="Search objects..." className={styles.searchInput} />
            </div>

            <div className={styles.tree}>
                {catalogs.map(catalog => (
                    <TreeNode
                        key={catalog}
                        label={catalog}
                        type="catalog"
                        isExpanded={expandedCatalogs[catalog]}
                        isLoading={loading[catalog]}
                        onToggle={() => toggleCatalog(catalog)}
                    >
                        {namespaces[catalog]?.map(ns => (
                            <TreeNode
                                key={ns}
                                label={ns}
                                type="namespace"
                                isExpanded={expandedNamespaces[`${catalog}.${ns}`]}
                                isLoading={loading[`${catalog}.${ns}`]}
                                onToggle={() => toggleNamespace(catalog, ns)}
                            >
                                {tables[`${catalog}.${ns}`]?.map(table => (
                                    <TreeNode
                                        key={table}
                                        label={table}
                                        type="table"
                                    />
                                ))}
                            </TreeNode>
                        ))}
                    </TreeNode>
                ))}
            </div>
        </div>
    );
};
