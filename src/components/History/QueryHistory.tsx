import React from 'react';
import type { HistoryEntry } from '../../hooks/useQueryHistory';
import { Clock, Trash2, History as HistoryIcon, X } from 'lucide-react';
import styles from './QueryHistory.module.css';

interface QueryHistoryProps {
    history: HistoryEntry[];
    onSelectQuery: (query: string) => void;
    onClearHistory: () => void;
    onClose: () => void;
}

export const QueryHistory: React.FC<QueryHistoryProps> = ({ history, onSelectQuery, onClearHistory, onClose }) => {
    const formatDate = (timestamp: number) => {
        const date = new Date(timestamp);
        const today = new Date();
        const yesterday = new Date();
        yesterday.setDate(today.getDate() - 1);

        if (date.toDateString() === today.toDateString()) {
            return 'Today';
        } else if (date.toDateString() === yesterday.toDateString()) {
            return 'Yesterday';
        } else {
            return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
        }
    };

    // Grouping history by date while maintaining order
    const groups: { label: string; entries: HistoryEntry[] }[] = [];
    history.forEach(entry => {
        const label = formatDate(entry.timestamp);
        let group = groups.find(g => g.label === label);
        if (!group) {
            group = { label, entries: [] };
            groups.push(group);
        }
        group.entries.push(entry);
    });

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <div className={styles.title}>
                    <HistoryIcon size={16} />
                    <span>Query History</span>
                </div>
                <div className={styles.actions}>
                    {history.length > 0 && (
                        <button
                            className={styles.clearButton}
                            onClick={(e) => {
                                e.stopPropagation();
                                if (confirm('Are you sure you want to clear your query history?')) {
                                    onClearHistory();
                                }
                            }}
                            title="Clear History"
                        >
                            <Trash2 size={14} />
                        </button>
                    )}
                    <button className={styles.closeButton} onClick={onClose} title="Close">
                        <X size={16} />
                    </button>
                </div>
            </div>

            <div className={styles.content}>
                {history.length === 0 ? (
                    <div className={styles.emptyState}>
                        <Clock size={32} />
                        <p>No query history yet</p>
                    </div>
                ) : (
                    groups.map((group) => (
                        <div key={group.label} className={styles.group}>
                            <div className={styles.groupLabel}>{group.label}</div>
                            {group.entries.map((entry) => (
                                <div
                                    key={entry.id}
                                    className={styles.card}
                                    onClick={() => onSelectQuery(entry.query)}
                                >
                                    <pre className={styles.queryPreview}>
                                        {entry.query}
                                    </pre>
                                    <div className={styles.timestamp}>
                                        {new Date(entry.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};
