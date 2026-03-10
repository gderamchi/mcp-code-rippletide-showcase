import { Card } from '../../components/ui/Card';
import { InlineNotice } from '../../components/ui/InlineNotice';
import { StatCard } from '../../components/ui/StatCard';
import { baseCustomers, baseOrders } from '../../lib/api/seed';
import { useSettingsContext } from '../../app/useSettingsContext';
import styles from './DashboardPage.module.css';

export function DashboardPage(): JSX.Element {
  const { loading, settings } = useSettingsContext();
  const delayedOrders = baseOrders.filter((order) => order.status !== 'Ready').length;

  return (
    <section className={styles.hero}>
      <div className={styles.headline}>
        <span className={styles.eyebrow}>Merchandise command center</span>
        <h2 className={styles.title}>Steer the queue before stock tension becomes churn.</h2>
        <p className={styles.copy}>
          Northstar Ops gives the team a shared view of order pressure, customer mix, and
          the supply signals that need attention before the next planning cut.
        </p>
      </div>

      <div className={styles.grid}>
        <StatCard label="Orders in flight" value={String(baseOrders.length)} footnote="Across hardware, software, and services." />
        <StatCard label="Accounts watched" value={String(baseCustomers.length)} footnote="Strategic, growth, and pilot cohorts." />
        <StatCard label="Needs attention" value={String(delayedOrders)} footnote="Delayed and at-risk orders on the floor today." />
      </div>

      {loading ? <InlineNotice>Loading operating preferences…</InlineNotice> : null}

      {settings?.lowStockAlerts ? (
        <Card>
          <h3 className={styles.alertTitle}>Low-stock alert rail is active</h3>
          <p className={styles.alertCopy}>
            Buyers will see a highlighted alert when demand-heavy items need a replenishment check.
          </p>
        </Card>
      ) : null}
    </section>
  );
}
