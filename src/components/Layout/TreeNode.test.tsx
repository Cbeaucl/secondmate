import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { TreeNode } from './TreeNode';

describe('TreeNode Component', () => {
    it('renders label correctly', () => {
        render(<TreeNode label="test-label" type="catalog" />);
        expect(screen.getByText('test-label')).toBeInTheDocument();
    });

    it('triggers onToggle when clicked', () => {
        const handleToggle = vi.fn();
        render(<TreeNode label="test-label" type="catalog" onToggle={handleToggle} />);

        fireEvent.click(screen.getByText('test-label'));
        expect(handleToggle).toHaveBeenCalledTimes(1);
    });

    it('renders children when isExpanded is true', () => {
        render(
            <TreeNode label="parent" type="catalog" isExpanded={true}>
                <div data-testid="child-node">child content</div>
            </TreeNode>
        );
        expect(screen.getByTestId('child-node')).toBeInTheDocument();
        expect(screen.getByText('child content')).toBeInTheDocument();
    });

    it('hides children when isExpanded is false', () => {
        render(
            <TreeNode label="parent" type="catalog" isExpanded={false}>
                <div data-testid="child-node">child content</div>
            </TreeNode>
        );
        expect(screen.queryByTestId('child-node')).not.toBeInTheDocument();
    });

    it('shows TableMenu for table types when onTableOverview is provided', () => {
        const handleTableOverview = vi.fn();
        render(
            <TreeNode
                label="test-table"
                type="table"
                catalog="test-catalog"
                namespace="test-namespace"
                onTableOverview={handleTableOverview}
            />
        );

        // TableMenu should render a button with title "Table Menu"
        const moreButton = screen.getByTitle('Table Menu');
        expect(moreButton).toBeInTheDocument();
    });

    it('does not show TableMenu for non-table types', () => {
        const handleTableOverview = vi.fn();
        render(
            <TreeNode
                label="test-catalog"
                type="catalog"
                catalog="test-catalog"
                namespace="test-namespace"
                onTableOverview={handleTableOverview}
            />
        );

        const moreButton = screen.queryByTitle('Table Menu');
        expect(moreButton).not.toBeInTheDocument();
    });
});
