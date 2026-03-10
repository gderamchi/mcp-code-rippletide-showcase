import { Card } from './Card';
import styles from './StatCard.module.css';

interface StatCardProps {
  label: string;
  value: string;
  footnote: string;
}

export function StatCard({ label, value, footnote }: StatCardProps): JSX.Element {
  return (
    <Card>
      <p className={styles.label}>{label}</p>
      <p className={styles.value}>{value}</p>
      <p className={styles.footnote}>{footnote}</p>
    </Card>
  );
}
