import { createContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import type { AppSettings } from '../types/models';
import { getSettings, subscribeSettings, updateSettings } from '../lib/api/settings';

interface SettingsContextValue {
  settings: AppSettings | null;
  loading: boolean;
  saveSettings: (partial: Partial<AppSettings>) => Promise<void>;
}

const SettingsContext = createContext<SettingsContextValue | null>(null);

export function AppProviders({ children }: { children: ReactNode }): JSX.Element {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;

    void getSettings().then((value) => {
      if (mountedRef.current) {
        setSettings(value);
        setLoading(false);
      }
    });

    const unsubscribe = subscribeSettings((value) => {
      setSettings(value);
      setLoading(false);
    });

    return () => {
      mountedRef.current = false;
      unsubscribe();
    };
  }, []);

  const value = useMemo<SettingsContextValue>(
    () => ({
      settings,
      loading,
      async saveSettings(partial) {
        setLoading(true);
        const next = await updateSettings(partial);
        if (!mountedRef.current) {
          return;
        }
        setSettings(next);
        setLoading(false);
      },
    }),
    [loading, settings]
  );

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
}

export { SettingsContext };
