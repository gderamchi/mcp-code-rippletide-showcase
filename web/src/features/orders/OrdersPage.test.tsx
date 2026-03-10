import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ordersApiTestControls } from '../../lib/api/orders';
import { OrdersPage } from './OrdersPage';

describe('OrdersPage', () => {
  beforeEach(() => {
    ordersApiTestControls.reset();
  });

  it('filters orders by category with the existing controller pattern', async () => {
    const user = userEvent.setup();
    render(<OrdersPage />);

    expect(await screen.findByText('Northwind Capital')).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText(/category/i), 'Software');

    expect(await screen.findByText('Canvas Grid')).toBeInTheDocument();
    expect(screen.queryByText('Northwind Capital')).not.toBeInTheDocument();
  });

  it('exports the current orders slice with the expected CSV headers', async () => {
    const user = userEvent.setup();
    render(<OrdersPage />);

    await screen.findByText('Northwind Capital');
    await user.click(screen.getByRole('button', { name: /export csv/i }));

    expect(screen.getByText(/Order ID,Customer,Category,Status,Owner,Total/)).toBeInTheDocument();
  });

  it('retries through the existing orders API client after an initial failure', async () => {
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
