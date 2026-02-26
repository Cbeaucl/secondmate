import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Workspace } from './Workspace';
import React from 'react';

// Mock the dependencies that might cause issues in a unit test environment
vi.mock('@monaco-editor/react', () => ({
    Editor: ({ defaultValue, onChange }: any) => (
        <textarea
            data-testid="mock-monaco-editor"
            defaultValue={defaultValue}
            onChange={(e) => onChange(e.target.value)}
        />
    ),
    default: ({ defaultValue, onChange }: any) => (
        <textarea
            data-testid="mock-monaco-editor"
            defaultValue={defaultValue}
            onChange={(e) => onChange(e.target.value)}
        />
    ),
}));

vi.mock('react-resizable-panels', () => ({
    PanelGroup: ({ children }: any) => <div data-testid="panel-group">{children}</div>,
    Panel: ({ children }: any) => <div data-testid="panel">{children}</div>,
    PanelResizeHandle: () => <div data-testid="resize-handle" />,
}));

vi.mock('../../services/api', () => ({
    api: {
        executeQuery: vi.fn(),
    },
}));

// Mock Lucide icons
vi.mock('lucide-react', () => ({
    Play: () => <span data-testid="play-icon" />,
}));

describe('Workspace Component Initial State', () => {
    it('renders the initial state correctly', () => {
        render(<Workspace />);

        // Check for the "Run" button
        const runButton = screen.getByRole('button', { name: /run/i });
        expect(runButton).toBeInTheDocument();
        expect(runButton).not.toBeDisabled();

        // Check for the welcome message
        expect(screen.getByText(/Welcome Aboard Matey!/i)).toBeInTheDocument();
        expect(screen.getByText(/Welcome To Secondmate! Get started by entering your query above./i)).toBeInTheDocument();

        // Check for the "Query Results" header
        expect(screen.getByText(/Query Results/i)).toBeInTheDocument();

        // Check if the editor has the initial query
        // Note: In our mock, the SqlEditor passes initialValue to Editor's defaultValue
        const editor = screen.getByTestId('mock-monaco-editor');
        expect(editor).toHaveValue('-- Write your SparkSQL here\nSELECT * FROM user.sales.transactions LIMIT 100;');
    });
});
