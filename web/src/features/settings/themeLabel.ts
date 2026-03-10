import type { ThemePreference } from '../../types/models';

export function getThemeLabel(value: ThemePreference): string {
  switch (value) {
    case 'system':
      return 'System';
    case 'light':
      return 'Light';
    case 'dark':
      return 'Dark';
    default:
      return 'System';
  }
}
