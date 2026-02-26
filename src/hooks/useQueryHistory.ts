import { useState } from 'react';

export interface HistoryEntry {
    id: string;
    query: string;
    timestamp: number;
}

const STORAGE_KEY = 'sql_query_history';
const MAX_HISTORY = 50;

export const useQueryHistory = () => {
    const [history, setHistory] = useState<HistoryEntry[]>(() => {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) {
            try {
                return JSON.parse(saved);
            } catch (e) {
                console.error('Failed to parse history', e);
            }
        }
        return [];
    });

    const addEntry = (query: string) => {
        if (!query.trim()) return;

        setHistory(prev => {
            // Remove the same query if it exists to move it to the top
            const filtered = prev.filter(h => h.query.trim() !== query.trim());

            const newEntry: HistoryEntry = {
                id: Math.random().toString(36).substring(2, 11),
                query,
                timestamp: Date.now(),
            };

            const newHistory = [newEntry, ...filtered].slice(0, MAX_HISTORY);
            localStorage.setItem(STORAGE_KEY, JSON.stringify(newHistory));
            return newHistory;
        });
    };

    const clearHistory = () => {
        setHistory([]);
        localStorage.removeItem(STORAGE_KEY);
    };

    return { history, addEntry, clearHistory };
};
