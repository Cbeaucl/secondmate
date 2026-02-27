export interface Column {
    name: string;
    type: string;
}

export interface QueryResult {
    schema?: Column[];
    data?: any[];
    error?: string;
}

export interface SystemInfo {
    app_name: string;
    spark_version: string;
    master: string;
    python_version: string;
}

declare global {
    interface Window {
        SECONDMATE_CONFIG?: {
            apiBaseUrl?: string;
        };
    }
}

const API_BASE_URL = window.SECONDMATE_CONFIG?.apiBaseUrl || '/api'; // Proxied by Vite or injected


export const api = {
    executeQuery: async (query: string): Promise<QueryResult> => {
        const response = await fetch(`${API_BASE_URL}/query/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        if (!response.ok) {
            return { error: `Error executing query: ${response.statusText}` };
        }
        return await response.json();
    },

    getCatalogs: async (): Promise<string[]> => {
        const response = await fetch(`${API_BASE_URL}/catalogs`);
        if (!response.ok) throw new Error('Failed to fetch catalogs');
        const data = await response.json();
        return data.catalogs;
    },

    getNamespaces: async (catalogName: string): Promise<string[]> => {
        const response = await fetch(`${API_BASE_URL}/catalogs/${catalogName}/namespaces`);
        if (!response.ok) throw new Error('Failed to fetch namespaces');
        const data = await response.json();
        return data.namespaces;
    },

    getTables: async (catalogName: string, namespace: string): Promise<string[]> => {
        const response = await fetch(`${API_BASE_URL}/catalogs/${catalogName}/namespaces/${namespace}/tables`);
        if (!response.ok) throw new Error('Failed to fetch tables');
        const data = await response.json();
        return data.tables;
    },

    searchCatalog: async (query: string): Promise<any[]> => {
        const response = await fetch(`${API_BASE_URL}/search?q=${encodeURIComponent(query)}`);
        if (!response.ok) throw new Error('Failed to search catalog');
        const data = await response.json();
        return data.results;
    },

    getSystemInfo: async (): Promise<SystemInfo> => {
        const response = await fetch(`${API_BASE_URL}/info`);
        if (!response.ok) throw new Error('Failed to fetch system info');
        return await response.json();
    },

    getTableOverview: async (catalogName: string, namespace: string, tableName: string): Promise<any> => {
        const response = await fetch(`${API_BASE_URL}/catalogs/${catalogName}/namespaces/${namespace}/tables/${tableName}/overview`);
        if (!response.ok) throw new Error('Failed to fetch table overview');
        return await response.json();
    }
};

// Backwards compatibility alias if needed, or just export it as part of api object above.
// But existing code uses `import { fetchQueryData } from ...`.
// So we should export `fetchQueryData` as standalone too, or refactor existing code.
// Let's keep `fetchQueryData` as a standalone export for now to avoid breaking DataViewer.


