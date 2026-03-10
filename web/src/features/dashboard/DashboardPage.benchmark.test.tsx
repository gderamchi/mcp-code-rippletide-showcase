import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AppProviders } from '../../app/AppProviders';
import { resetSettingsApi } from '../../lib/api/settings';
import { DashboardPage } from './DashboardPage';
import { SettingsPage } from '../settings/SettingsPage';

describe('Dashboard benchmark tasks', () => {
  beforeEach(() => {
    resetSettingsApi();
  });

  it('keeps low-stock alerts in sync with settings', async () => {
    const user = userEvent.setup();
    render(
      <AppProviders>
        <DashboardPage />
        <SettingsPage />
      </AppProviders>
    );

    expect(await screen.findByText(/low-stock alert rail is active/i)).toBeInTheDocument();
    await user.click(screen.getByLabelText(/low-stock alerts/i));
    await waitFor(() => {
      expect(screen.queryByText(/low-stock alert rail is active/i)).not.toBeInTheDocument();
    });
  });
});
