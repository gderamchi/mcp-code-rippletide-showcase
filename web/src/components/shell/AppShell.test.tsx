import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { AppShell } from './AppShell';

describe('AppShell', () => {
  it('closes the mobile drawer after a route selection', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<div>Dashboard view</div>} />
            <Route path="/orders" element={<div>Orders view</div>} />
            <Route path="/customers" element={<div>Customers view</div>} />
            <Route path="/settings" element={<div>Settings view</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    );

    await user.click(screen.getByRole('button', { name: /open navigation menu/i }));
    const dialog = screen.getByRole('dialog');

    await user.click(within(dialog).getByRole('link', { name: 'Orders' }));

    expect(await screen.findByText('Orders view')).toBeInTheDocument();
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});
