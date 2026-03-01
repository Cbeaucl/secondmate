import React, { useEffect, useState } from 'react';
import { Database, Table, Folder, ChevronRight, ChevronDown, Search, Loader2, X, MoreVertical, FileText } from 'lucide-react';
import styles from './Sidebar.module.css';
import { api } from '../../services/api';

interface TableMenuProps {
    catalog: string;
    namespace: string;
    table: string;
    onTableOverview: (catalog: string, namespace: string, table: string) => void;
}

const TableMenu: React.FC<TableMenuProps> = ({ catalog, namespace, table, onTableOverview }) => {
    const [menuOpen, setMenuOpen] = useState<{ x: number, y: number } | null>(null);

    const handleMoreClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        setMenuOpen({ x: e.clientX, y: e.clientY });
    };

    useEffect(() => {
        if (!menuOpen) return;
        const closeMenu = () => setMenuOpen(null);
        window.addEventListener('click', closeMenu);
        return () => window.removeEventListener('click', closeMenu);
    }, [menuOpen]);

    return (
        <>
            <button className={styles.moreButton} onClick={handleMoreClick} title="Table Menu">
                <MoreVertical size={14} />
            </button>
            {menuOpen && (
                <div
                    className={styles.menu}
                    style={{ top: menuOpen.y, left: menuOpen.x }}
                    onClick={(e) => e.stopPropagation()}
                >
                    <div
                        className={styles.menuItem}
                        onClick={() => {
                            onTableOverview(catalog, namespace, table);
                            setMenuOpen(null);
                        }}
                    >
                        <FileText size={14} />
                        <span>Table Overview</span>
                    </div>
                </div>
            )}
        </>
    );
};

interface TreeNodeProps {
    label: string;
    type: 'catalog' | 'namespace' | 'table';
    catalog?: string;
    namespace?: string;
    children?: React.ReactNode;
    isExpanded?: boolean;
    onToggle?: () => void;
    isLoading?: boolean;
    forceExpand?: boolean;
    onTableOverview?: (catalog: string, namespace: string, table: string) => void;
}

const TreeNode: React.FC<TreeNodeProps> = ({
    label,
    type,
    catalog,
    namespace,
    children,
    isExpanded,
    onToggle,
    isLoading,
    forceExpand,
    onTableOverview
}) => {
    const Icon = type === 'catalog' ? Database : type === 'namespace' ? Folder : Table;
    const color = type === 'catalog' ? '#38bdf8' : type === 'namespace' ? '#fbbf24' : '#a78bfa';
    const showChildren = forceExpand || isExpanded;

    return (
        <div className={styles.treeItem}>
            <div className={styles.treeRow} onClick={onToggle} style={{ cursor: 'pointer' }}>
                {type !== 'table' && (
                    <div style={{ width: 16, display: 'flex', alignItems: 'center' }}>
                        {isLoading ? <Loader2 size={12} className={styles.spinner} /> :
                            showChildren ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    </div>
                )}
                {type === 'table' && <div style={{ width: 16 }} />}
                <Icon size={14} className={styles.icon} color={color} />
                <span className="truncate">{label}</span>
                {type === 'table' && onTableOverview && catalog && namespace && (
                    <TableMenu
                        catalog={catalog}
                        namespace={namespace}
                        table={label}
                        onTableOverview={onTableOverview}
                    />
                )}
            </div>
            {showChildren && children && <div className={styles.treeChildren}>{children}</div>}
        </div>
    );
};

interface SidebarProps {
    onTableOverview?: (catalog: string, namespace: string, table: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onTableOverview }) => {
    const [catalogs, setCatalogs] = useState<string[]>([]);
    const [expandedCatalogs, setExpandedCatalogs] = useState<Record<string, boolean>>({});
    const [namespaces, setNamespaces] = useState<Record<string, string[]>>({});
    const [expandedNamespaces, setExpandedNamespaces] = useState<Record<string, boolean>>({}); // key: catalog.namespace
    const [tables, setTables] = useState<Record<string, string[]>>({}); // key: catalog.namespace
    const [loading, setLoading] = useState<Record<string, boolean>>({}); // key: node id

    // Tab State
    const [activeTab, setActiveTab] = useState<'browse' | 'search'>('browse');

    // Search State
    const [searchQuery, setSearchQuery] = useState('');
    const [isSearching, setIsSearching] = useState(false);
    const [searchResults, setSearchResults] = useState<any[]>([]);

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
                                    {tables[`${catalog}.${ns}`]?.map(table => (
                                        <TreeNode
                                            key={table}
                                            label={table}
                                            type="table"
                                            catalog={catalog}
                                            namespace={ns}
                                            onTableOverview={onTableOverview}
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
                        {!isSearching && searchResults.map((item, idx) => (
                            <div key={idx} className={styles.treeRow} style={{ paddingLeft: '12px' }}>
                                {item.type === 'catalog' && <Database size={14} className={styles.icon} color="#38bdf8" />}
                                {item.type === 'namespace' && <Folder size={14} className={styles.icon} color="#fbbf24" />}
                                {item.type === 'table' && <Table size={14} className={styles.icon} color="#a78bfa" />}

                                <span className="truncate" style={{ marginLeft: '6px' }}>
                                    {item.type === 'catalog' && item.catalog}
                                    {item.type === 'namespace' && `${item.catalog}.${item.namespace}`}
                                    {item.type === 'table' && `${item.catalog}.${item.namespace}.${item.table}`}
                                </span>

                                {item.type === 'table' && onTableOverview && (
                                    <TableMenu
                                        catalog={item.catalog}
                                        namespace={item.namespace}
                                        table={item.table}
                                        onTableOverview={onTableOverview}
                                    />
                                )}
                            </div>
                        ))}
                    </>
                )}
            </div>
        </div>
    );
};
