import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AppProviders } from '../../app/AppProviders';
import { resetSettingsApi } from '../../lib/api/settings';
import { SettingsPage } from './SettingsPage';

describe('SettingsPage', () => {
  beforeEach(() => {
    resetSettingsApi();
  });

  it('rejects blank invite emails with the shared validation helper', async () => {
    const user = userEvent.setup();
    render(
      <AppProviders>
        <SettingsPage />
      </AppProviders>
    );

    await user.type(screen.getByLabelText(/invite admin email/i), '   ');
    await user.click(screen.getByRole('button', { name: /send invite/i }));

    expect(await screen.findByText(/email is required/i)).toBeInTheDocument();
  });

  it('shows the correct theme label copy', async () => {
    render(
      <AppProviders>
        <SettingsPage />
      </AppProviders>
    );

    expect(await screen.findByText(/theme preference: system/i)).toBeInTheDocument();
  });
});
