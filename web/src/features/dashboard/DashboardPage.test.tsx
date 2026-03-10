import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AppProviders } from '../../app/AppProviders';
import { DashboardPage } from './DashboardPage';
import { SettingsPage } from '../settings/SettingsPage';
import { resetSettingsApi } from '../../lib/api/settings';

function renderDashboardWithSettings(): void {
  render(
    <AppProviders>
      <DashboardPage />
      <SettingsPage />
    </AppProviders>
  );
}

describe('DashboardPage', () => {
  beforeEach(() => {
    resetSettingsApi();
  });

  it('shows the low-stock alert rail by default and hides it when disabled from settings', async () => {
    const user = userEvent.setup();
    renderDashboardWithSettings();

    expect(await screen.findByText(/low-stock alert rail is active/i)).toBeInTheDocument();

    await user.click(screen.getByLabelText(/low-stock alerts/i));

    await waitFor(() => {
      expect(screen.queryByText(/low-stock alert rail is active/i)).not.toBeInTheDocument();
    });
  });
});
