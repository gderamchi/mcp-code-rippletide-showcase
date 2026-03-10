import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ordersApiTestControls } from '../../lib/api/orders';
import { OrdersPage } from './OrdersPage';

describe('Orders benchmark tasks', () => {
  beforeEach(() => {
    ordersApiTestControls.reset();
  });

  it('adds category filtering using the existing orders flow', async () => {
    const user = userEvent.setup();
    render(<OrdersPage />);

    await screen.findByText('Northwind Capital');
    await user.selectOptions(screen.getByLabelText(/category/i), 'Software');

    expect(await screen.findByText('Canvas Grid')).toBeInTheDocument();
    expect(screen.queryByText('Northwind Capital')).not.toBeInTheDocument();
  });

  it('exports customer, category, status, and total headers', async () => {
    const user = userEvent.setup();
    render(<OrdersPage />);

    await screen.findByText('Northwind Capital');
    await user.click(screen.getByRole('button', { name: /export csv/i }));

    expect(screen.getByText(/Order ID,Customer,Category,Status,Owner,Total/)).toBeInTheDocument();
  });

  it('retry triggers another orders api request and clears the error state', async () => {
    const user = userEvent.setup();
    ordersApiTestControls.queueFailure();
    render(<OrdersPage />);

    expect(await screen.findByText(/temporarily unavailable/i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /retry orders/i }));

    await waitFor(() => {
      expect(screen.getByText('Northwind Capital')).toBeInTheDocument();
    });
    expect(ordersApiTestControls.getCallCount()).toBe(2);
  });
});

