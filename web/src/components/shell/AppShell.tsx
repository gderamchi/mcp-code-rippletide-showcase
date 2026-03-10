import { useEffect, useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { Button } from '../ui/Button';
import styles from './AppShell.module.css';

const navItems = [
  { label: 'Dashboard', to: '/' },
  { label: 'Orders', to: '/orders' },
  { label: 'Customers', to: '/customers' },
  { label: 'Settings', to: '/settings' },
];

function navLinkClass({ isActive }: { isActive: boolean }): string {
  return [styles.navLink, isActive ? styles.navLinkActive : ''].filter(Boolean).join(' ');
}

interface NavListProps {
  onNavigate?: () => void;
}

function NavList({ onNavigate }: NavListProps): JSX.Element {
  return (
    <nav className={styles.nav} aria-label="Primary">
      {navItems.map((item) => (
        <NavLink key={item.to} className={navLinkClass} onClick={onNavigate} to={item.to}>
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}

export function AppShell(): JSX.Element {
  const location = useLocation();
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    setDrawerOpen(false);
  }, [location.pathname]);

  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <div className={styles.brand}>
          <span className={styles.brandMark}>Editorial Ops</span>
          <h1 className={styles.brandTitle}>Northstar Ops</h1>
          <p className={styles.brandCopy}>Monitor demand, inventory, and the team’s next move.</p>
        </div>
        <NavList />
      </aside>

      {drawerOpen ? (
        <div className={[styles.drawer, styles.drawerOpen].join(' ')} role="dialog">
          <div className={styles.drawerPanel}>
            <Button onClick={() => setDrawerOpen(false)} variant="ghost">Close</Button>
            <NavList onNavigate={() => setDrawerOpen(false)} />
          </div>
        </div>
      ) : null}

      <main className={styles.main}>
        <div className={styles.topbar}>
          <span className={styles.topbarTitle}>Northstar Ops</span>
          <Button aria-label="Open navigation menu" onClick={() => setDrawerOpen(true)} variant="secondary">
            Menu
          </Button>
        </div>
        <div className={styles.content}>
          <Outlet />
        </div>
      </main>
    </div>
  );
}
