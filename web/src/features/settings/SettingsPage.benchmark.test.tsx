import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AppProviders } from '../../app/AppProviders';
import { resetSettingsApi } from '../../lib/api/settings';
import { SettingsPage } from './SettingsPage';

describe('Settings benchmark tasks', () => {
  beforeEach(() => {
    resetSettingsApi();
  });

  it('rejects blank invite emails and shows the validation error', async () => {
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

  it('shows the stable theme label for system mode', async () => {
    render(
      <AppProviders>
        <SettingsPage />
      </AppProviders>
    );

    expect(await screen.findByText(/theme preference: system/i)).toBeInTheDocument();
  });
});

