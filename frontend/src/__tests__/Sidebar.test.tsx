import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Sidebar } from '../components/layout/Sidebar';

describe('Sidebar', () => {
  const onPageChange = vi.fn();

  beforeEach(() => {
    onPageChange.mockClear();
  });

  it('renders brand and navigation', () => {
    render(
      <Sidebar currentPage="dashboard" onPageChange={onPageChange} semesterName="1st Sem 2025" />
    );

    expect(screen.getByText('AcadSort')).toBeInTheDocument();
    expect(screen.getByText('1st Sem 2025')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Dashboard/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Review Queue/i })).toBeInTheDocument();
  });

  it('highlights active page', () => {
    render(<Sidebar currentPage="review" onPageChange={onPageChange} />);

    const reviewBtn = screen.getByRole('button', { name: /Review Queue/i });
    expect(reviewBtn).toHaveAttribute('data-active', 'true');
  });

  it('calls onPageChange when nav clicked', () => {
    render(<Sidebar currentPage="dashboard" onPageChange={onPageChange} />);

    fireEvent.click(screen.getByRole('button', { name: /Settings/i }));
    expect(onPageChange).toHaveBeenCalledWith('settings');
  });

  it('shows pending badge on review queue', () => {
    render(
      <Sidebar currentPage="dashboard" onPageChange={onPageChange} pendingCount={5} />
    );

    expect(screen.getByText('5')).toBeInTheDocument();
  });
});
