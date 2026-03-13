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

export type DataType = 'string' | 'integer' | 'boolean';
export type UiInputType = 'text' | 'select' | 'radio' | 'toggle';

export interface ConfigOptionItem {
    label: string;
    value: any;
}

export interface ConfigOption {
    id: string;
    label: string;
    data_type: DataType;
    ui_input_type: UiInputType;
    current_value: any | null;
    default_value: any | null;
    options: ConfigOptionItem[] | null;
    is_required: boolean;
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

    getTables: async (catalogName: string, namespace: string): Promise<{name: string, type: 'table' | 'view'}[]> => {
        const response = await fetch(`${API_BASE_URL}/catalogs/${catalogName}/namespaces/${namespace}/tables`);
        if (!response.ok) throw new Error('Failed to fetch tables');
        const data = await response.json();
        return data.items;
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

    getTableSchema: async (catalogName: string, namespace: string, tableName: string): Promise<any> => {
        const response = await fetch(`${API_BASE_URL}/catalogs/${catalogName}/namespaces/${namespace}/tables/${tableName}/schema`);
        if (!response.ok) throw new Error('Failed to fetch table schema');
        return await response.json();
    },

    getTableProperties: async (catalogName: string, namespace: string, tableName: string): Promise<any> => {
        const response = await fetch(`${API_BASE_URL}/catalogs/${catalogName}/namespaces/${namespace}/tables/${tableName}/properties`);
        if (!response.ok) throw new Error('Failed to fetch table properties');
        return await response.json();
    },

    getTableSnapshots: async (catalogName: string, namespace: string, tableName: string): Promise<any> => {
        const response = await fetch(`${API_BASE_URL}/catalogs/${catalogName}/namespaces/${namespace}/tables/${tableName}/snapshots`);
        if (!response.ok) throw new Error('Failed to fetch table snapshots');
        return await response.json();
    },

    getTablePartitions: async (catalogName: string, namespace: string, tableName: string): Promise<any> => {
        const response = await fetch(`${API_BASE_URL}/catalogs/${catalogName}/namespaces/${namespace}/tables/${tableName}/partitions`);
        if (!response.ok) throw new Error('Failed to fetch table partitions');
        return await response.json();
    },

    getTableFiles: async (catalogName: string, namespace: string, tableName: string): Promise<any> => {
        const response = await fetch(`${API_BASE_URL}/catalogs/${catalogName}/namespaces/${namespace}/tables/${tableName}/files`);
        if (!response.ok) throw new Error('Failed to fetch table files');
        return await response.json();
    },

    getTableMetrics: async (catalogName: string, namespace: string, tableName: string): Promise<any> => {
        const response = await fetch(`${API_BASE_URL}/catalogs/${catalogName}/namespaces/${namespace}/tables/${tableName}/metrics`);
        if (!response.ok) throw new Error('Failed to fetch table metrics');
        return await response.json();
    },

    getTableDdl: async (catalogName: string, namespace: string, tableName: string): Promise<{ ddl: string }> => {
        const response = await fetch(`${API_BASE_URL}/catalogs/${catalogName}/namespaces/${namespace}/tables/${tableName}/ddl`);
        if (!response.ok) throw new Error('Failed to fetch table DDL');
        return await response.json();
    },

    getConfigs: async (): Promise<ConfigOption[]> => {
        const response = await fetch(`${API_BASE_URL}/configs`);
        if (!response.ok) throw new Error('Failed to fetch configs');
        return await response.json();
    },

    saveConfigs: async (configs: Record<string, any>): Promise<void> => {
        const response = await fetch(`${API_BASE_URL}/configs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(configs)
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Failed to save configs');
        }
    }
};

// Backwards compatibility alias if needed, or just export it as part of api object above.
// But existing code uses `import { fetchQueryData } from ...`.
// So we should export `fetchQueryData` as standalone too, or refactor existing code.
// Let's keep `fetchQueryData` as a standalone export for now to avoid breaking DataViewer.


