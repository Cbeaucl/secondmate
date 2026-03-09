import React, { useEffect, useState } from 'react';
import { MoreVertical, FileText, Code } from 'lucide-react';
import styles from './Sidebar.module.css';

export interface TableMenuProps {
    catalog: string;
    namespace: string;
    table: string;
    onTableOverview: (catalog: string, namespace: string, table: string) => void;
    onShowDdl: (catalog: string, namespace: string, table: string) => void;
}

export const TableMenu: React.FC<TableMenuProps> = ({ catalog, namespace, table, onTableOverview, onShowDdl }) => {
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
                    <div
                        className={styles.menuItem}
                        onClick={() => {
                            onShowDdl(catalog, namespace, table);
                            setMenuOpen(null);
                        }}
                    >
                        <Code size={14} />
                        <span>Show DDL</span>
                    </div>
                </div>
            )}
        </>
    );
};
