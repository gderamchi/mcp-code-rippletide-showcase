import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { InlineNotice } from '../../components/ui/InlineNotice';
import { SelectField } from '../../components/ui/SelectField';
import { useOrdersController } from './useOrdersController';
import styles from './OrdersPage.module.css';

const categoryOptions = [
  { label: 'All categories', value: 'All' },
  { label: 'Hardware', value: 'Hardware' },
  { label: 'Software', value: 'Software' },
  { label: 'Services', value: 'Services' },
];

export function OrdersPage(): JSX.Element {
  const { state, setSelectedCategory, retry, exportCurrent } = useOrdersController();

  return (
    <section className={styles.page}>
      <div className={styles.header}>
        <div className={styles.titleBlock}>
          <span className={styles.eyebrow}>Live demand map</span>
          <h2 className={styles.title}>Orders</h2>
          <p className={styles.copy}>Filter the queue, recover from transient failures, and export the current slice.</p>
        </div>
        <div className={styles.controls}>
          <SelectField
            id="orders-category"
            label="Category"
            onChange={(event) => setSelectedCategory(event.currentTarget.value as 'All' | 'Hardware' | 'Software' | 'Services')}
            options={categoryOptions}
            value={state.selectedCategory}
          />
          <Button onClick={exportCurrent} variant="secondary">Export CSV</Button>
        </div>
      </div>

      {state.status === 'loading' ? <InlineNotice>Loading orders…</InlineNotice> : null}
      {state.status === 'error' ? (
        <Card>
          <InlineNotice tone="error">{state.errorMessage}</InlineNotice>
          <Button onClick={() => void retry()} variant="secondary">Retry orders</Button>
        </Card>
      ) : null}
      {state.status === 'ready' ? (
        <Card className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Customer</th>
                <th>Category</th>
                <th>Status</th>
                <th>Owner</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {state.orders.map((order) => (
                <tr key={order.id}>
                  <td>{order.id}</td>
                  <td>{order.customerName}</td>
                  <td>{order.category}</td>
                  <td>{order.status}</td>
                  <td>{order.owner}</td>
                  <td>${order.total.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      ) : null}

      {state.exportedCsv ? <pre className={styles.exportPreview}>{state.exportedCsv}</pre> : null}
    </section>
  );
}
