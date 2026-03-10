import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { AppShell } from './AppShell';

describe('AppShell benchmark tasks', () => {
  it('closes the mobile drawer after nav selection', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<div>Dashboard benchmark view</div>} />
            <Route path="/orders" element={<div>Orders benchmark view</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    );

    await user.click(screen.getByRole('button', { name: /open navigation menu/i }));
    const dialog = screen.getByRole('dialog');
    await user.click(within(dialog).getByRole('link', { name: 'Orders' }));

    expect(await screen.findByText('Orders benchmark view')).toBeInTheDocument();
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});

