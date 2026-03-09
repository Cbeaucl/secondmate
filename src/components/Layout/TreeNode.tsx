import React, { useState } from 'react';
import { Database, Table, Folder, ChevronRight, ChevronDown, Loader2, Check } from 'lucide-react';
import styles from './Sidebar.module.css';
import { TableMenu } from './TableMenu';

export interface TreeNodeProps {
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
    onShowDdl?: (catalog: string, namespace: string, table: string) => void;
}

export const TreeNode: React.FC<TreeNodeProps> = ({
    label,
    type,
    catalog,
    namespace,
    children,
    isExpanded,
    onToggle,
    isLoading,
    forceExpand,
    onTableOverview,
    onShowDdl
}) => {
    const [copied, setCopied] = useState(false);

    const handleCopy = (e: React.MouseEvent) => {
        if (type === 'table' && catalog && namespace) {
            e.stopPropagation();
            const fullName = `${catalog}.${namespace}.${label}`;
            navigator.clipboard.writeText(fullName);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } else if (onToggle) {
            onToggle();
        }
    };

    const Icon = type === 'catalog' ? Database : type === 'namespace' ? Folder : (copied ? Check : Table);
    const color = type === 'catalog' ? '#38bdf8' : type === 'namespace' ? '#fbbf24' : (copied ? '#10b981' : '#a78bfa');
    const showChildren = forceExpand || isExpanded;

    return (
        <div className={styles.treeItem}>
            <div
                className={styles.treeRow}
                onClick={type === 'table' ? handleCopy : onToggle}
                style={{ cursor: 'pointer' }}
                title={type === 'table' ? "Click to copy table name" : undefined}
            >
                {type !== 'table' && (
                    <div style={{ width: 16, display: 'flex', alignItems: 'center' }}>
                        {isLoading ? <Loader2 size={12} className={styles.spinner} /> :
                            showChildren ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    </div>
                )}
                {type === 'table' && <div style={{ width: 16 }} />}
                <Icon size={14} className={styles.icon} color={color} />
                <span className="truncate">{label}</span>
                {type === 'table' && onTableOverview && onShowDdl && catalog && namespace && (
                    <TableMenu
                        catalog={catalog}
                        namespace={namespace}
                        table={label}
                        onTableOverview={onTableOverview}
                        onShowDdl={onShowDdl}
                    />
                )}
            </div>
            {showChildren && children && <div className={styles.treeChildren}>{children}</div>}
        </div>
    );
};
