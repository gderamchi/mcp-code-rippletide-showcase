import { useEffect, useState } from 'react';
import { Card } from '../../components/ui/Card';
import { InlineNotice } from '../../components/ui/InlineNotice';
import { PageEmptyState } from '../../components/ui/PageEmptyState';
import { SelectField } from '../../components/ui/SelectField';
import type { Customer, CustomerSegment } from '../../types/models';
import { listCustomers } from '../../lib/api/customers';
import { CustomerNotesPanel } from './CustomerNotesPanel';
import styles from './CustomersPage.module.css';

const segmentOptions = [
  { label: 'All segments', value: 'All' },
  { label: 'Strategic', value: 'Strategic' },
  { label: 'Growth', value: 'Growth' },
  { label: 'Pilot', value: 'Pilot' },
  { label: 'Dormant', value: 'Dormant' },
];

export function CustomersPage(): JSX.Element {
  const [segment, setSegment] = useState<CustomerSegment | 'All'>('All');
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    setLoading(true);
    void listCustomers(segment).then((value) => {
      if (active) {
        setCustomers(value);
        setLoading(false);
      }
    });

    return () => {
      active = false;
    };
  }, [segment]);

  return (
    <section className={styles.page}>
      <div className={styles.header}>
        <div className={styles.titleBlock}>
          <span className={styles.eyebrow}>Relationship watchlist</span>
          <h2 className={styles.title}>Customers</h2>
          <p className={styles.copy}>View accounts by segment and keep handoff notes in the shared rhythm.</p>
        </div>
        <SelectField
          id="customer-segment"
          label="Segment"
          onChange={(event) => setSegment(event.currentTarget.value as CustomerSegment | 'All')}
          options={segmentOptions}
          value={segment}
        />
      </div>

      {loading ? <InlineNotice>Loading customers…</InlineNotice> : null}

      {!loading && customers.length === 0 ? (
        <PageEmptyState
          actionLabel="Reset filter"
          body="No customers match the selected segment right now."
          eyebrow="Customer view"
          onAction={() => setSegment('All')}
          title="No accounts in this segment"
        />
      ) : null}

      {!loading && customers.length > 0 ? (
        <div className={styles.list}>
          {customers.map((customer) => (
            <Card key={customer.id}>
              <h3 className={styles.itemTitle}>{customer.name}</h3>
              <p className={styles.itemCopy}>
                {customer.segment} cohort · {customer.owner} · Last order {customer.lastOrderDate}
              </p>
            </Card>
          ))}
        </div>
      ) : null}

      <Card>
        <CustomerNotesPanel />
      </Card>
    </section>
  );
}
