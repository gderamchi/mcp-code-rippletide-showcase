export function validateEmail(value: string): string | null {
  const trimmed = value.trim();

  if (!trimmed) {
    return 'Email is required.';
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
    return 'Enter a valid email address.';
  }

  return null;
}
