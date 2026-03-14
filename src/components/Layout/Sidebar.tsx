import React, { useEffect, useState } from 'react';
import { Database, Table, Folder, Search, Loader2, X, Check, Eye } from 'lucide-react';
import styles from './Sidebar.module.css';
import { api } from '../../services/api';
import { TreeNode } from './TreeNode';
import { TableMenu } from './TableMenu';

interface SidebarProps {
    onTableOverview?: (catalog: string, namespace: string, table: string) => void;
    onShowDdl?: (catalog: string, namespace: string, table: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onTableOverview, onShowDdl }) => {
    const [catalogs, setCatalogs] = useState<string[]>([]);
    const [expandedCatalogs, setExpandedCatalogs] = useState<Record<string, boolean>>({});
    const [namespaces, setNamespaces] = useState<Record<string, string[]>>({});
    const [expandedNamespaces, setExpandedNamespaces] = useState<Record<string, boolean>>({}); // key: catalog.namespace
    const [tables, setTables] = useState<Record<string, {name: string, type: 'table' | 'view'}[]>>({}); // key: catalog.namespace
    const [loading, setLoading] = useState<Record<string, boolean>>({}); // key: node id

    // Tab State
    const [activeTab, setActiveTab] = useState<'browse' | 'search'>('browse');

    // Search State
    const [searchQuery, setSearchQuery] = useState('');
    const [isSearching, setIsSearching] = useState(false);
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [copiedNodeInfo, setCopiedNodeInfo] = useState<string | null>(null);

    const handleCopySearchNode = (item: any) => {
        if (item.type === 'table' || item.type === 'view') {
            const fullName = `${item.catalog}.${item.namespace}.${item.table}`;
            navigator.clipboard.writeText(fullName);
            setCopiedNodeInfo(fullName);
            setTimeout(() => setCopiedNodeInfo(null), 2000);
        }
    };

    useEffect(() => {
        loadCatalogs();
    }, []);

    useEffect(() => {
        if (!searchQuery.trim()) {
            setSearchResults([]);
            return;
        }

        const timer = setTimeout(async () => {
            setIsSearching(true);
            try {
                const results = await api.searchCatalog(searchQuery);
                setSearchResults(results);
            } catch (err) {
                console.error("Search failed", err);
            } finally {
                setIsSearching(false);
            }
        }, 300); // Debounce

        return () => clearTimeout(timer);
    }, [searchQuery]);

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
                <div className={styles.title}>Data Catalog</div>
            </div>

            <div className={styles.tabs}>
                <div
                    className={`${styles.tab} ${activeTab === 'browse' ? styles.activeTab : ''}`}
                    onClick={() => setActiveTab('browse')}
                >
                    Browse
                </div>
                <div
                    className={`${styles.tab} ${activeTab === 'search' ? styles.activeTab : ''}`}
                    onClick={() => setActiveTab('search')}
                >
                    Search
                </div>
            </div>

            {activeTab === 'search' && (
                <div className={styles.searchBox}>
                    <Search size={14} className={styles.searchIcon} />
                    <input
                        type="text"
                        placeholder="Search tables..."
                        className={styles.searchInput}
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        autoFocus
                    />
                    {searchQuery && (
                        <X
                            size={14}
                            className={styles.clearIcon}
                            onClick={() => setSearchQuery('')}
                        />
                    )}
                </div>
            )}

            <div className={styles.tree}>
                {activeTab === 'browse' ? (
                    catalogs.map(catalog => (
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
                                    {tables[`${catalog}.${ns}`]?.map(tableObj => (
                                        <TreeNode
                                            key={tableObj.name}
                                            label={tableObj.name}
                                            type={tableObj.type as 'table' | 'view'}
                                            catalog={catalog}
                                            namespace={ns}
                                            onTableOverview={onTableOverview}
                                            onShowDdl={onShowDdl}
                                        />
                                    ))}
                                </TreeNode>
                            ))}
                        </TreeNode>
                    ))
                ) : (
                    <>
                        {isSearching && (
                            <div style={{ padding: '12px', display: 'flex', justifyContent: 'center' }}>
                                <Loader2 size={16} className={styles.spinner} />
                            </div>
                        )}
                        {!isSearching && searchResults.length === 0 && searchQuery && (
                            <div style={{ padding: '0 12px', color: '#666', fontSize: '13px', fontStyle: 'italic' }}>
                                No results found
                            </div>
                        )}
                        {!isSearching && searchResults.map((item, idx) => {
                            const isTableOrView = item.type === 'table' || item.type === 'view';
                            const fullName = isTableOrView ? `${item.catalog}.${item.namespace}.${item.table}` : '';
                            const isCopied = copiedNodeInfo === fullName && isTableOrView;

                            return (
                                <div
                                    key={idx}
                                    className={styles.treeRow}
                                    style={{ paddingLeft: '12px', cursor: isTableOrView ? 'pointer' : 'default' }}
                                    onClick={isTableOrView ? () => handleCopySearchNode(item) : undefined}
                                    title={isTableOrView ? "Click to copy name" : undefined}
                                >
                                    {item.type === 'catalog' && <Database size={14} className={styles.icon} color="#38bdf8" />}
                                    {item.type === 'namespace' && <Folder size={14} className={styles.icon} color="#fbbf24" />}
                                    {item.type === 'table' && (
                                        isCopied ? <Check size={14} className={styles.icon} color="#10b981" /> : <Table size={14} className={styles.icon} color="#a78bfa" />
                                    )}
                                    {item.type === 'view' && (
                                        isCopied ? <Check size={14} className={styles.icon} color="#10b981" /> : <Eye size={14} className={styles.icon} color="#a78bfa" />
                                    )}

                                    <span className="truncate" style={{ marginLeft: '6px' }}>
                                        {item.type === 'catalog' && item.catalog}
                                        {item.type === 'namespace' && `${item.catalog}.${item.namespace}`}
                                        {isTableOrView && fullName}
                                    </span>

                                    {isTableOrView && onTableOverview && onShowDdl && (
                                        <TableMenu
                                            catalog={item.catalog}
                                            namespace={item.namespace}
                                            table={item.table}
                                            isView={item.type === 'view'}
                                            onTableOverview={onTableOverview}
                                            onShowDdl={onShowDdl}
                                        />
                                    )}
                                </div>
                            );
                        })}
                    </>
                )}
            </div>
        </div>
    );
};
