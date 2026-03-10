import type { HTMLAttributes } from 'react';
import styles from './Card.module.css';

type CardProps = HTMLAttributes<HTMLDivElement> & {
  tone?: 'default' | 'muted';
};

export const Card = ({ className, tone = 'default', ...props }: CardProps) => {
  const classes = [
    styles.card,
    tone === 'muted' ? styles.muted : null,
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return <div {...props} className={classes} />;
};
