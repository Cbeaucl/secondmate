import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { TableOverview } from './TableOverview';
import { api } from '../../services/api';
import React from 'react';

vi.mock('../../services/api');
vi.mock('../Results/JsonView', () => ({
    JsonView: () => <div data-testid="json-view" />
}));
vi.mock('../Results/DataGrid', () => ({
    DataGrid: ({ columns, data }: any) => (
        <div data-testid="data-grid">
            <div data-testid="columns">{JSON.stringify(columns)}</div>
            <div data-testid="data-rows">{JSON.stringify(data)}</div>
        </div>
    )
}));

describe('TableOverview', () => {
    it('correctly flattens files with empty partitions for unpartitioned tables', async () => {
        const mockOverviewData = {
            tableName: 'catalog.ns.table',
            schema: { fields: [] },
            properties: [],
            snapshots: [],
            partitions: [],
            files: [
                {
                    content: 0,
                    file_format: 'PARQUET',
                    partition: {}, // Empty partition for unpartitioned table
                    record_count: 100,
                    file_size_mb: 1.5
                }
            ]
        };

        (api.getTableOverview as any).mockResolvedValue(mockOverviewData);

        render(
            <TableOverview
                catalog="catalog"
                namespace="ns"
                table="table"
                onClose={() => {}}
            />
        );

        // Wait for loading to finish
        await waitFor(() => expect(screen.queryByText(/Loading Table Overview/i)).not.toBeInTheDocument());

        // Find the Files section DataGrid
        // We can find the <h2> with text "Iceberg Files" and then find the sibling grid
        const filesHeader = screen.getByText('Iceberg Files');
        const filesGrid = filesHeader.parentElement?.querySelector('[data-testid="data-grid"]');

        const columns = JSON.parse(filesGrid?.querySelector('[data-testid="columns"]')?.textContent || '[]');
        const dataRows = JSON.parse(filesGrid?.querySelector('[data-testid="data-rows"]')?.textContent || '[]');

        // Verify that 'partition' column is not present in columns since it was flattened away (it was empty)
        expect(columns.map((c: any) => c.name)).not.toContain('partition');

        // Verify other columns are present
        expect(columns.map((c: any) => c.name)).toContain('content');
        expect(columns.map((c: any) => c.name)).toContain('file_format');
        expect(columns.map((c: any) => c.name)).toContain('record_count');
        expect(columns.map((c: any) => c.name)).toContain('file_size_mb');

        // Verify data record doesn't have the partition key but has others
        expect(dataRows[0]).not.toHaveProperty('partition');
        expect(dataRows[0].content).toBe(0);
        expect(dataRows[0].record_count).toBe(100);
    });
});
