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

export type JobStatus = 'queued' | 'running' | 'succeeded' | 'failed';

export interface Job {
    job_id: string;
    query_text: string;
    status: JobStatus;
    error_message: string | null;
    created_at: number;
    started_at: number | null;
    completed_at: number | null;
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
    // --- Job Queue Endpoints ---

    submitJob: async (query: string): Promise<{ job_id: string; status: string }> => {
        const response = await fetch(`${API_BASE_URL}/jobs/submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Failed to submit job');
        }
        return await response.json();
    },

    listJobs: async (): Promise<{ jobs: Job[] }> => {
        const response = await fetch(`${API_BASE_URL}/jobs`);
        if (!response.ok) throw new Error('Failed to fetch jobs');
        return await response.json();
    },

    getJob: async (jobId: string): Promise<Job> => {
        const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`);
        if (!response.ok) throw new Error('Failed to fetch job');
        return await response.json();
    },

    getJobResults: async (jobId: string): Promise<QueryResult> => {
        const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/results`);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            return { error: errorData.detail || 'Failed to fetch results' };
        }
        return await response.json();
    },

    // --- Catalog Endpoints ---

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
