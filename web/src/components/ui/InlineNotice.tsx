import type { ReactNode } from 'react';
import styles from './InlineNotice.module.css';

interface InlineNoticeProps {
  tone?: 'info' | 'error' | 'success';
  children: ReactNode;
}

export function InlineNotice({
  tone = 'info',
  children,
}: InlineNoticeProps): JSX.Element {
  return <div className={[styles.notice, styles[tone]].join(' ')}>{children}</div>;
}
