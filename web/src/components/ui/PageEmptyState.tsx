import { Button } from './Button';
import styles from './PageEmptyState.module.css';

interface PageEmptyStateProps {
  eyebrow: string;
  title: string;
  body: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function PageEmptyState({
  eyebrow,
  title,
  body,
  actionLabel,
  onAction,
}: PageEmptyStateProps): JSX.Element {
  return (
    <div className={styles.wrap}>
      <span className={styles.eyebrow}>{eyebrow}</span>
      <h3 className={styles.title}>{title}</h3>
      <p className={styles.body}>{body}</p>
      {actionLabel && onAction ? <Button variant="secondary" onClick={onAction}>{actionLabel}</Button> : null}
    </div>
  );
}
