import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from '../components/shell/AppShell';
import { CustomersPage } from '../features/customers/CustomersPage';
import { DashboardPage } from '../features/dashboard/DashboardPage';
import { OrdersPage } from '../features/orders/OrdersPage';
import { SettingsPage } from '../features/settings/SettingsPage';
import { BenchmarkStudioPage } from '../features/studio/BenchmarkStudioPage';
import { AppProviders } from './AppProviders';

export function AppRouter(): JSX.Element {
  return (
    <BrowserRouter>
      <AppProviders>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<DashboardPage />} />
            <Route path="/orders" element={<OrdersPage />} />
            <Route path="/customers" element={<CustomersPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/studio" element={<BenchmarkStudioPage />} />
            <Route path="*" element={<Navigate replace to="/" />} />
          </Route>
        </Routes>
      </AppProviders>
    </BrowserRouter>
  );
}
