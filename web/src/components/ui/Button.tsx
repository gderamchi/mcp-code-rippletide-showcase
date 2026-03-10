import type { ButtonHTMLAttributes } from 'react';
import styles from './Button.module.css';

type ButtonVariant = 'primary' | 'secondary' | 'ghost';

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
};

export const Button = ({
  className,
  type = 'button',
  variant = 'primary',
  ...props
}: ButtonProps) => {
  const classes = [styles.button, styles[variant], className].filter(Boolean).join(' ');

  return <button {...props} className={classes} type={type} />;
};
