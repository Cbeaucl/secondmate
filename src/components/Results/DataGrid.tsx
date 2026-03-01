import React from 'react';
import styles from './DataGrid.module.css';

interface Column {
    name: string;
    type: string;
}

interface DataGridProps {
    columns: Column[];
    data: Record<string, unknown>[];
}

export const DataGrid: React.FC<DataGridProps> = React.memo(({ columns, data }) => {
    return (
        <div className={styles.gridContainer}>
            <table className={styles.table}>
                <thead>
                    <tr>
                        {columns.map((col) => (
                            <th key={col.name}>
                                <div className={styles.headerCell}>
                                    <span>{col.name}</span>
                                    <span className={styles.typeLabel}>{col.type}</span>
                                </div>
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {data.map((row, i) => (
                        <tr key={i}>
                            {columns.map((col) => (
                                <td key={`${i}-${col.name}`}>
                                    {typeof row[col.name] === 'object' && row[col.name] !== null
                                        ? JSON.stringify(row[col.name])
                                        : String(row[col.name] ?? '')}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
});
