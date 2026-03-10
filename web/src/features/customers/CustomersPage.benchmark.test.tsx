import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CustomersPage } from './CustomersPage';

describe('Customers benchmark tasks', () => {
  it('uses the design system empty state when a segment has no accounts', async () => {
    const user = userEvent.setup();
    render(<CustomersPage />);

    await screen.findByText('Northwind Capital');
    await user.selectOptions(screen.getByLabelText(/segment/i), 'Dormant');

    expect(await screen.findByText(/no accounts in this segment/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /reset filter/i })).toBeInTheDocument();
  });
});

