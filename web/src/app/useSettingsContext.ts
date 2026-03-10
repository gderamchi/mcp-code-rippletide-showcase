import { useContext } from 'react';
import { SettingsContext } from './AppProviders';

export function useSettingsContext() {
  const value = useContext(SettingsContext);

  if (!value) {
    throw new Error('useSettingsContext must be used within AppProviders.');
  }

  return value;
}
